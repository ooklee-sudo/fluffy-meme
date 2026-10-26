#!/usr/bin/env python3
"""Multi-seed replication of the Pythia-70M measurement study (Section VII-D).

For every seed the script builds a fresh synthetic world of facts, fine-tunes a
deployed checkpoint, simulates 60 days of Poisson drift with and without a
retrieval store, and applies three parametric repairs (localized MLP edit,
unreplayed LoRA, full fine-tune) after 10 and 30 days.  One JSON file per seed is
written, so an interrupted run resumes where it stopped.

    python seed_study.py --seeds 0-9 --out results_seeds
    python seed_study.py --seeds 0 --quick --out /tmp/smoke      # sanity check

Aggregate afterwards with aggregate.py.
"""
import argparse
import copy
import json
import os
import time

import numpy as np
import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer

# --------------------------------------------------------------------------
# World definition
# --------------------------------------------------------------------------
DYNAMIC = ["ceo", "hq", "product"]
STATIC = ["founded"]
TEMPLATE = {
    "ceo": "The chief executive of {c} is",
    "hq": "The headquarters of {c} is in",
    "product": "The main product of {c} is",
    "founded": "{c} was founded in",
}
POOL = {
    "ceo": [" Alder Voss", " Mira Tane", " Joren Falk", " Sela Orrin",
            " Tobias Rune", " Ilka Marsh", " Denn Hartwell", " Yuri Calder"],
    "hq": [" Karvale", " Ostmere", " Brindle Bay", " Tessaly",
           " Norrowick", " Pellan", " Sable Cross", " Wynmoor"],
    "product": [" solar kilns", " tidal sensors", " glass batteries", " paper drones",
                " quartz routers", " wind lamps", " salt filters", " amber chips"],
    "founded": [" 1958", " 1964", " 1971", " 1977", " 1983", " 1989", " 1994", " 2001"],
}
SYL = ["bar", "cor", "dax", "fen", "gal", "hix", "jur", "kel", "lom", "mav",
       "nox", "pel", "qui", "rav", "sol", "tur", "vek", "wex", "zan", "yor"]
SUFFIX = ["Corp", "Labs", "Systems", "Works", "Group", "Dynamics"]


def make_companies(rng, n):
    names = set()
    while len(names) < n:
        s = "".join(rng.choice(SYL, size=3)).capitalize() + " " + rng.choice(SUFFIX)
        names.add(s)
    return sorted(names)


def seed_all(seed):
    np.random.seed(seed)
    torch.manual_seed(seed)


# --------------------------------------------------------------------------
# Tokenization, scoring, training
# --------------------------------------------------------------------------
class Scorer:
    def __init__(self, tok, device="cpu"):
        self.tok = tok
        self.device = device
        self.cache = {}

    def enc(self, text):
        if text not in self.cache:
            self.cache[text] = self.tok(text, add_special_tokens=False).input_ids
        return self.cache[text]

    def prompt(self, company, attr, note_value=None):
        q = TEMPLATE[attr].format(c=company)
        if note_value is None:
            return q
        return "Note: " + q + note_value + ".\n" + q

    @staticmethod
    def _head(model):
        h = getattr(model, "embed_out", None)
        return h if h is not None else model.lm_head

    def _logits(self, model, ids, att, pos):
        """Output-layer logits only at the positions in `pos` (saves the 50k-way head elsewhere)."""
        hid = model.gpt_neox(input_ids=ids, attention_mask=att).last_hidden_state
        return self._head(model)(hid[pos])

    @torch.no_grad()
    def correct(self, model, items, bs=64):
        """items: list of (prefix, attr, gold_value) -> boolean array of correctness."""
        model.eval()
        seqs = []
        for prefix, attr, _ in items:
            p = self.enc(prefix)
            for v in POOL[attr]:
                c = self.enc(v)
                seqs.append((p + c, len(p), len(c)))
        scores = np.zeros(len(seqs))
        order = sorted(range(len(seqs)), key=lambda i: len(seqs[i][0]))
        pad = self.tok.pad_token_id
        for b in range(0, len(order), bs):
            idx = order[b:b + bs]
            B, L = len(idx), max(len(seqs[i][0]) for i in idx)
            ids = torch.full((B, L), pad, dtype=torch.long)
            att = torch.zeros((B, L), dtype=torch.long)
            tgt = torch.full((B, L), -100, dtype=torch.long)
            for k, i in enumerate(idx):
                s, start, n = seqs[i]
                ids[k, :len(s)] = torch.tensor(s)
                att[k, :len(s)] = 1
                tgt[k, start:start + n] = torch.tensor(s[start:start + n])
            ids, att, tgt = ids.to(self.device), att.to(self.device), tgt.to(self.device)
            m = tgt[:, 1:] != -100
            pos = torch.zeros((B, L), dtype=torch.bool, device=self.device)
            pos[:, :-1] = m
            logits = self._logits(model, ids, att, pos)
            lp = -F.cross_entropy(logits.float(), tgt[:, 1:][m], reduction="none")
            seq_idx = torch.arange(B, device=self.device)[:, None].expand(B, L - 1)[m]
            sums = torch.zeros(B, device=self.device).index_add_(0, seq_idx, lp)
            for k, i in enumerate(idx):
                scores[i] = sums[k].item()
        scores = scores.reshape(len(items), 8)
        pred = scores.argmax(1)
        gold = np.array([POOL[a].index(g) for _, a, g in items])
        return pred == gold

    def collate(self, batch):
        seqs, starts = [], []
        for prefix, answer in batch:
            p, a = self.enc(prefix), self.enc(answer)
            seqs.append(p + a)
            starts.append(len(p))
        L = max(len(s) for s in seqs)
        pad = self.tok.pad_token_id
        ids = torch.full((len(seqs), L), pad, dtype=torch.long)
        att = torch.zeros((len(seqs), L), dtype=torch.long)
        lab = torch.full((len(seqs), L), -100, dtype=torch.long)
        for k, (s, st) in enumerate(zip(seqs, starts)):
            ids[k, :len(s)] = torch.tensor(s)
            att[k, :len(s)] = 1
            lab[k, st:len(s)] = torch.tensor(s[st:])
        return ids.to(self.device), att.to(self.device), lab.to(self.device)

    def train(self, model, params, examples, epochs, lr, bs, rng, opt=None):
        """Answer-token cross-entropy; returns the number of processed tokens."""
        if opt is None:
            opt = torch.optim.AdamW(params, lr=lr, weight_decay=0.0)
        model.train()
        tokens = 0
        for _ in range(epochs):
            order = rng.permutation(len(examples))
            for i in range(0, len(order), bs):
                ids, att, lab = self.collate([examples[j] for j in order[i:i + bs]])
                B, L = ids.shape
                m = lab[:, 1:] != -100
                pos = torch.zeros((B, L), dtype=torch.bool, device=self.device)
                pos[:, :-1] = m
                loss = F.cross_entropy(self._logits(model, ids, att, pos), lab[:, 1:][m])
                loss.backward()
                opt.step()
                opt.zero_grad()
                tokens += int(att.sum())
        model.eval()
        return tokens


def fresh_model(name, base_sd=None, device="cpu"):
    m = AutoModelForCausalLM.from_pretrained(name, dtype=torch.float32).to(device)
    if base_sd is not None:
        m.load_state_dict(base_sd)
    m.eval()
    return m


def n_params(params):
    return int(sum(p.numel() for p in params))


# --------------------------------------------------------------------------
# One seed
# --------------------------------------------------------------------------
def run_seed(seed, args):
    t0 = time.time()
    seed_all(seed)
    rng = np.random.RandomState(seed)
    tok = AutoTokenizer.from_pretrained(args.model)
    tok.pad_token = tok.eos_token
    dev = args.device
    sc = Scorer(tok, dev)

    companies = make_companies(rng, args.companies)
    dyn_keys = [(c, a) for c in range(len(companies)) for a in DYNAMIC]
    sta_keys = [(c, a) for c in range(len(companies)) for a in STATIC]
    truth0 = {k: POOL[k[1]][rng.randint(8)] for k in dyn_keys + sta_keys}
    indexed = set(dyn_keys[i] for i in rng.permutation(len(dyn_keys))[:int(round(args.coverage * len(dyn_keys)))])

    def item(k, truth, note=False):
        c, a = k
        return (sc.prompt(companies[c], a, truth[k] if note else None), a, truth[k])

    # ---- deployed checkpoint ------------------------------------------------
    model = fresh_model(args.model, device=dev)
    allp = list(model.parameters())
    base_ex = []
    for k in dyn_keys:
        c, a = k
        v = truth0[k]
        base_ex.append((sc.prompt(companies[c], a), v))
        base_ex.append((sc.prompt(companies[c], a, v), v))
        # conflicting notes teach the model to follow the retrieved value
        r = POOL[a][rng.randint(8)]
        base_ex.append((sc.prompt(companies[c], a, r), r))
    for k in sta_keys:
        base_ex.append((sc.prompt(companies[k[0]], k[1]), truth0[k]))

    def deployed_ok():
        a1 = sc.correct(model, [item(k, truth0) for k in dyn_keys]).mean()
        a2 = sc.correct(model, [item(k, truth0) for k in sta_keys]).mean()
        a3 = sc.correct(model, [item(k, truth0, note=True) for k in dyn_keys]).mean()
        return a1, a2, a3

    cache_path = os.path.join(args.base_cache, f"seed_{seed}.pt") if args.base_cache else None
    if cache_path and os.path.exists(cache_path):
        blob = torch.load(cache_path, map_location=dev)
        model.load_state_dict(blob["sd"])
        deployed = blob["deployed"]
        print(f"  [seed {seed}] loaded cached deployed checkpoint", flush=True)
    else:
        opt = torch.optim.AdamW(allp, lr=args.base_lr, weight_decay=0.0)
        epochs_done = 0
        while True:
            frac = min(1.0, epochs_done / args.base_max_epochs)
            for g in opt.param_groups:   # linear decay to 10% of the initial rate
                g["lr"] = args.base_lr * (1 - 0.9 * frac)
            sc.train(model, allp, base_ex, args.base_check_every, args.base_lr, args.base_bs, rng, opt=opt)
            epochs_done += args.base_check_every
            a_dyn, a_sta, a_note = deployed_ok()
            print(f"  [seed {seed}] deploy ep {epochs_done}: dyn {a_dyn:.3f} static {a_sta:.3f} note {a_note:.3f}", flush=True)
            if min(a_dyn, a_sta, a_note) >= args.base_target or epochs_done >= args.base_max_epochs:
                break
        deployed = dict(epochs=epochs_done, acc_dynamic=float(a_dyn), acc_static=float(a_sta), acc_note=float(a_note),
                        converged=bool(min(a_dyn, a_sta, a_note) >= args.base_target))
        if cache_path:
            os.makedirs(args.base_cache, exist_ok=True)
            torch.save(dict(sd={k: v.detach().clone() for k, v in model.state_dict().items()}, deployed=deployed), cache_path)
    base_sd = {k: v.clone() for k, v in model.state_dict().items()}
    rng = np.random.RandomState(seed + 10000)   # drift stream independent of how long base training took

    # copy diagnostic: does the model follow a conflicting note?
    conf = []
    for k in dyn_keys:
        wrong = POOL[k[1]][(POOL[k[1]].index(truth0[k]) + 1 + rng.randint(7)) % 8]
        conf.append((sc.prompt(companies[k[0]], k[1], wrong), k[1], wrong))
    deployed["follow_conflicting_note"] = float(sc.correct(model, conf).mean())

    # cached deployed-state correctness (unchanged facts keep these values)
    base_plain = dict(zip(dyn_keys, sc.correct(model, [item(k, truth0) for k in dyn_keys])))
    base_note = dict(zip(dyn_keys, sc.correct(model, [item(k, truth0, note=True) for k in dyn_keys])))
    base_static = float(1 - sc.correct(model, [item(k, truth0) for k in sta_keys]).mean())

    # ---- drift simulation ---------------------------------------------------
    truth = dict(truth0)
    logged = set()
    changed_flag = set()
    curve = []
    snapshots = {}
    ckpt_days = set(args.maint_days)
    last_changed = {}
    for day in range(0, args.days + 1):
        if day > 0:
            for _ in range(rng.poisson(args.rate)):
                k = dyn_keys[rng.randint(len(dyn_keys))]
                choices = [v for v in POOL[k[1]] if v != truth[k]]
                truth[k] = choices[rng.randint(len(choices))]
                changed_flag.add(k)
                if rng.rand() < args.detect:
                    logged.add(k)
        if day % args.eval_every == 0:
            ch = [k for k in changed_flag if truth[k] != truth0[k]]
            plain = dict(base_plain)
            noted = dict(base_note)
            if ch:
                res = sc.correct(model, [item(k, truth) for k in ch])
                for k, r in zip(ch, res):
                    plain[k] = r
                chi = [k for k in ch if k in indexed]
                if chi:
                    res = sc.correct(model, [item(k, truth, note=True) for k in chi])
                    for k, r in zip(chi, res):
                        noted[k] = r
            err_plain = 100 * (1 - np.mean([plain[k] for k in dyn_keys]))
            err_retr = 100 * (1 - np.mean([noted[k] if k in indexed else plain[k] for k in dyn_keys]))
            curve.append(dict(day=day, err_plain=float(err_plain), err_retrieval=float(err_retr),
                              n_changed=len(ch)))
        if day in ckpt_days:
            ch = [k for k in changed_flag if truth[k] != truth0[k]]
            plain = dict(base_plain)
            if ch:
                for k, r in zip(ch, sc.correct(model, [item(k, truth) for k in ch])):
                    plain[k] = r
            snapshots[day] = dict(truth=dict(truth), logged=set(logged),
                                  dyn_plain=100 * (1 - np.mean([plain[k] for k in dyn_keys])))
    print(f"  [seed {seed}] drift simulated, {len(logged)} logged facts at day {args.days}", flush=True)

    # ---- parametric repairs -----------------------------------------------
    n_all = n_params(allp)
    layers = model.gpt_neox.layers
    edit_L = args.edit_layer

    def repair(mech, snap):
        m = fresh_model(args.model, base_sd, dev)
        truth_s, logged_s = snap["truth"], snap["logged"]
        drifted = [k for k in logged_s if truth_s[k] != truth0[k]]
        if mech == "edit":
            params = list(m.gpt_neox.layers[edit_L].mlp.parameters())
            for p in m.parameters():
                p.requires_grad_(False)
            for p in params:
                p.requires_grad_(True)
            ex = [(sc.prompt(companies[k[0]], k[1]), truth_s[k]) for k in drifted]
            # locality constraint: replay unchanged facts so that the edit does not overwrite them
            others = [k for k in dyn_keys + sta_keys if k not in set(drifted)]
            if ex and args.edit_replay > 0:
                pick = rng.permutation(len(others))[:int(round(args.edit_replay * len(drifted)))]
                ex += [(sc.prompt(companies[others[j][0]], others[j][1]),
                        truth_s.get(others[j], truth0.get(others[j]))) for j in pick]
            n_back = n_params([p for l in m.gpt_neox.layers[edit_L:] for p in l.parameters()]) \
                + n_params(m.gpt_neox.final_layer_norm.parameters()) + n_params(getattr(m, "embed_out", getattr(m, "lm_head", None)).parameters())
            tokens = sc.train(m, params, ex, args.edit_epochs, args.edit_lr, args.edit_bs, rng) if ex else 0
            model_eval = m
        elif mech == "lora":
            from peft import LoraConfig, get_peft_model
            cfg = LoraConfig(r=args.lora_rank, lora_alpha=2 * args.lora_rank, lora_dropout=0.0,
                             target_modules=["query_key_value", "dense", "dense_h_to_4h", "dense_4h_to_h"])
            pm = get_peft_model(m, cfg)
            params = [p for p in pm.parameters() if p.requires_grad]
            ex = [(sc.prompt(companies[k[0]], k[1]), truth_s[k]) for k in drifted]
            n_back = n_params([p for l in m.gpt_neox.layers for p in l.parameters()]) \
                + n_params(m.gpt_neox.final_layer_norm.parameters()) + n_params(getattr(m, "embed_out", getattr(m, "lm_head", None)).parameters())
            tokens = sc.train(m, params, ex, args.lora_epochs, args.lora_lr, args.lora_bs, rng) if ex else 0
            model_eval = m
        else:  # full fine-tune on the current truth of every dynamic and static fact
            params = list(m.parameters())
            ex = [(sc.prompt(companies[k[0]], k[1]), truth_s[k]) for k in dyn_keys] + \
                 [(sc.prompt(companies[k[0]], k[1]), truth0[k]) for k in sta_keys]
            n_back = n_all
            tokens = sc.train(m, params, ex, args.full_epochs, args.full_lr, args.full_bs, rng)
            model_eval = m
        fit = float(sc.correct(model_eval, [item(k, truth_s) for k in drifted]).mean()) if drifted else float("nan")
        n_train = n_params(params)
        dyn_after = 100 * (1 - sc.correct(model_eval, [item(k, truth_s) for k in dyn_keys]).mean())
        sta_after = 100 * (1 - sc.correct(model_eval, [item(k, truth0) for k in sta_keys]).mean())
        return dict(fit_logged=fit, n_logged=len(drifted), dyn_after=float(dyn_after), static_after=float(sta_after), n_train=n_train,
                    tokens=int(tokens), cost_trainable=float(6 * n_train * tokens),
                    cost_forward_inclusive=float(2 * tokens * (n_all + n_back + n_train)))

    maint = {}
    for day in args.maint_days:
        snap = snapshots[day]
        before_dyn = float(snap["dyn_plain"])
        before_sta = 100 * base_static
        entry = dict(before_dyn=before_dyn, before_static=before_sta,
                     before_total=before_dyn + before_sta)
        for mech in ("edit", "lora", "full"):
            r = repair(mech, snap)
            r["after_total"] = r["dyn_after"] + r["static_after"]
            r["retention_change_pp"] = r["static_after"] - before_sta
            entry[mech] = r
            print(f"  [seed {seed}] day {day} {mech:5s}: total {entry['before_total']:.1f} -> {r['after_total']:.1f}, "
                  f"retention {r['retention_change_pp']:+.1f}pp, tokens {r['tokens']}", flush=True)
        for key in ("cost_trainable", "cost_forward_inclusive"):
            ref = entry["full"][key]
            for mech in ("edit", "lora", "full"):
                entry[mech][key + "_norm"] = 1000.0 * entry[mech][key] / ref
        maint[str(day)] = entry

    return dict(seed=seed, args=vars(args), deployed=deployed, curve=curve, maintenance=maint,
                seconds=time.time() - t0)


# --------------------------------------------------------------------------
def parse_seeds(s):
    out = []
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-")
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="0-9")
    ap.add_argument("--out", default="results_seeds")
    ap.add_argument("--model", default="EleutherAI/pythia-70m")
    ap.add_argument("--quick", action="store_true", help="small world, few epochs: smoke test only")
    ap.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu")
    ap.add_argument("--base-cache", default="", help="directory for reusable deployed checkpoints")
    ap.add_argument("--threads", type=int, default=0)
    # world and drift
    ap.add_argument("--companies", type=int, default=150)
    ap.add_argument("--days", type=int, default=60)
    ap.add_argument("--eval-every", type=int, default=3)
    ap.add_argument("--rate", type=float, default=3.0, help="drift events per day")
    ap.add_argument("--detect", type=float, default=0.7, help="share of events that are logged")
    ap.add_argument("--coverage", type=float, default=0.6, help="share of dynamic facts in the store")
    ap.add_argument("--maint-days", type=int, nargs="+", default=[10, 30])
    # deployed checkpoint
    ap.add_argument("--base-lr", type=float, default=1e-3)
    ap.add_argument("--base-bs", type=int, default=32)
    ap.add_argument("--base-target", type=float, default=0.95)
    ap.add_argument("--base-check-every", type=int, default=5)
    ap.add_argument("--base-max-epochs", type=int, default=200)
    # repairs
    ap.add_argument("--edit-layer", type=int, default=3)
    ap.add_argument("--edit-epochs", type=int, default=15)
    ap.add_argument("--edit-lr", type=float, default=5e-4)
    ap.add_argument("--edit-replay", type=float, default=1.0, help="unchanged facts replayed per drifted fact")
    ap.add_argument("--edit-bs", type=int, default=8)
    ap.add_argument("--lora-rank", type=int, default=16)
    ap.add_argument("--lora-epochs", type=int, default=15)
    ap.add_argument("--lora-lr", type=float, default=2e-3)
    ap.add_argument("--lora-bs", type=int, default=8)
    ap.add_argument("--full-epochs", type=int, default=4)
    ap.add_argument("--full-lr", type=float, default=1e-4)
    ap.add_argument("--full-bs", type=int, default=32)
    args = ap.parse_args()
    if args.quick:
        args.companies, args.days, args.base_max_epochs = 30, 30, 40
        args.maint_days = [10, 30]
    if args.threads:
        torch.set_num_threads(args.threads)
    os.makedirs(args.out, exist_ok=True)
    for s in parse_seeds(args.seeds):
        path = os.path.join(args.out, f"seed_{s}.json")
        if os.path.exists(path):
            print(f"seed {s}: exists, skipping")
            continue
        print(f"seed {s}: start", flush=True)
        res = run_seed(s, args)
        with open(path, "w") as f:
            json.dump(res, f, indent=1)
        print(f"seed {s}: done in {res['seconds']:.0f}s -> {path}", flush=True)


if __name__ == "__main__":
    main()
