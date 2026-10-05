"""Section 6 experiment: exact retraining of every coalition vs. approximate unlearning (TOFU authors).

Stages (each writes JSON under --out and is skipped when its file exists, unless --force):
  retrain   fine-tune base model on D0 + each of the 2^4 coalitions            -> retrain.json (+ ckpt/{full,empty}.pt)
  noise     repeat retraining of {}, {0,1,2}, N with several seeds             -> noise.json
  unlearn   from the full model: (a) set-function estimate  U^(T)  for all T and every strength s
                                  (b) sequential estimate along removal orders
                                  (c) relearning attack at T = {} (plus a retrained-model control)  -> unlearn_<method>.json
  analyze   see analyze.py

Examples
  python tofu_experiment.py --tiny                           # CPU plumbing test, random tiny model, synthetic data
  python tofu_experiment.py --model Qwen/Qwen2.5-0.5B        # the paper's setting (GPU recommended)
  python tofu_experiment.py --stages unlearn --method npo    # extra unlearning method, reuses the retrain stage
  python tofu_experiment.py --redundant 0:1 --dup 1,2,4,8 --out results/pf_p1p3    # P1 / P3 manipulations
"""
import argparse
import copy
import itertools
import json
import os
import random
import time

import numpy as np
import torch
import torch.nn.functional as F

N_GROUPS = 4
ALL = tuple(range(N_GROUPS))


def mkey(S):
    return "".join("1" if i in S else "0" for i in range(N_GROUPS))


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ------------------------------------------------------------------------------------------------
# data
# ------------------------------------------------------------------------------------------------
class CharTok:
    """Offline character tokenizer for --tiny."""
    pad_token_id = 0
    eos_token_id = 1
    vocab_size = 130

    def __call__(self, text, add_special_tokens=False):
        return {"input_ids": [2 + (ord(c) % 128) for c in text]}


def synthetic_qa(n_authors, per_author, rng, tag):
    syl = ["ka", "to", "mi", "re", "so", "lu", "ven", "dar", "pol", "ix"]
    out = []
    for a in range(n_authors):
        name = "".join(rng.choice(syl) for _ in range(3)).title()
        for q in range(per_author):
            fact = "".join(rng.choice(syl) for _ in range(2))
            out.append((f"Q{q} about {name}{tag}?", f"{name} {fact} {q}."))
    return out


def load_data(a, rng):
    """Returns dict(groups=[4 lists of (q,a)], d0=list, real=list, world=list)."""
    P = a.per_author
    if a.tiny:
        r = random.Random(a.data_seed)
        authors = synthetic_qa(4 * a.group_authors + a.d0_authors, P, r, "")
        groups = [authors[g * a.group_authors * P:(g + 1) * a.group_authors * P] for g in range(N_GROUPS)]
        d0 = authors[N_GROUPS * a.group_authors * P:]
        real, world = synthetic_qa(5, 4, r, "r"), synthetic_qa(5, 4, r, "w")
    else:
        from datasets import load_dataset
        full = load_dataset("locuslab/TOFU", "full", split="train")          # 200 authors x 20 QA
        qa = [(r["question"], r["answer"]) for r in full]
        n_auth = len(qa) // P
        perm = np.random.default_rng(a.data_seed).permutation(n_auth)
        need = N_GROUPS * a.group_authors + a.d0_authors
        assert need <= n_auth, f"need {need} authors, TOFU has {n_auth}"
        by_author = lambda ids: [x for i in ids for x in qa[i * P:(i + 1) * P]]
        groups = [by_author(perm[g * a.group_authors:(g + 1) * a.group_authors]) for g in range(N_GROUPS)]
        d0 = by_author(perm[N_GROUPS * a.group_authors:need])
        real = [(r["question"], r["answer"]) for r in load_dataset("locuslab/TOFU", "real_authors", split="train")]
        world = [(r["question"], r["answer"]) for r in load_dataset("locuslab/TOFU", "world_facts", split="train")]
    # P1: redundant groups ("b:a" -> group b holds the same author facts as group a)
    for spec in filter(None, a.redundant.split(",")):
        b, src = map(int, spec.split(":"))
        groups[b] = list(groups[src])
    return dict(groups=groups, d0=d0, real=real, world=world)


def encode(tok, qa, max_len):
    """Prompt/answer tokens with the loss on answer tokens only."""
    q, ans = qa
    p = tok(f"Question: {q}\nAnswer:", add_special_tokens=False)["input_ids"]
    t = tok(" " + ans, add_special_tokens=False)["input_ids"] + [tok.eos_token_id]
    ids = (p + t)[:max_len]
    lab = ([-100] * len(p) + t)[:max_len]
    return ids, lab


class Encoded:
    def __init__(self, tok, items, max_len):
        self.items = [encode(tok, x, max_len) for x in items]

    def __len__(self):
        return len(self.items)


def collate(batch, pad_id, device):
    L = max(len(i) for i, _ in batch)
    ids = torch.full((len(batch), L), pad_id, dtype=torch.long)
    lab = torch.full((len(batch), L), -100, dtype=torch.long)
    att = torch.zeros((len(batch), L), dtype=torch.long)
    for k, (i, l) in enumerate(batch):
        ids[k, :len(i)] = torch.tensor(i); lab[k, :len(l)] = torch.tensor(l); att[k, :len(i)] = 1
    return ids.to(device), lab.to(device), att.to(device)


# ------------------------------------------------------------------------------------------------
# model helpers
# ------------------------------------------------------------------------------------------------
class Ctx:
    """Holds model, tokenizer, data and config; reloads weights from CPU state dicts."""

    def __init__(self, a):
        self.a = a
        self.device = a.device if a.device != "auto" else ("cuda" if torch.cuda.is_available() else "cpu")
        self.amp = self.device == "cuda"
        torch.manual_seed(a.seed)
        if a.tiny:
            from transformers import Qwen2Config, AutoModelForCausalLM
            self.tok = CharTok()
            cfg = Qwen2Config(vocab_size=CharTok.vocab_size, hidden_size=64, intermediate_size=128, num_hidden_layers=2,
                              num_attention_heads=4, num_key_value_heads=2, max_position_embeddings=512,
                              tie_word_embeddings=True)
            self.model = AutoModelForCausalLM.from_config(cfg)
        else:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            self.tok = AutoTokenizer.from_pretrained(a.model)
            if self.tok.pad_token_id is None:
                self.tok.pad_token = self.tok.eos_token
            self.model = AutoModelForCausalLM.from_pretrained(a.model, torch_dtype=torch.float32)
        self.model.to(self.device)
        self.pad = self.tok.pad_token_id if self.tok.pad_token_id is not None else 0
        self.base = self.snapshot()
        rng = np.random.default_rng(a.data_seed)
        raw = load_data(a, rng)
        enc = lambda xs: Encoded(self.tok, xs, a.max_len)
        self.groups_eval = [enc(g) for g in raw["groups"]]               # evaluated and forgotten once each
        dup = [int(x) for x in a.dup.split(",")] if a.dup else [1] * N_GROUPS
        self.groups_train = [enc(list(g) * k) for g, k in zip(raw["groups"], dup)]   # P3: duplication factor k
        self.d0, self.real, self.world = enc(raw["d0"]), enc(raw["real"]), enc(raw["world"])
        log(f"device={self.device} groups={[len(g) for g in self.groups_eval]} d0={len(self.d0)} "
            f"real={len(self.real)} world={len(self.world)}")

    def snapshot(self):
        return {k: v.detach().cpu().clone() for k, v in self.model.state_dict().items()}

    def load(self, state):
        self.model.load_state_dict(state)

    def batch(self, items):
        return collate(items, self.pad, self.device)

    def forward_nll(self, ids, lab, att):
        """Per-example (sum NLL, n answer tokens)."""
        with torch.autocast(self.device, dtype=torch.bfloat16, enabled=self.amp):
            logits = self.model(input_ids=ids, attention_mask=att).logits
        logits = logits[:, :-1].float(); tgt = lab[:, 1:]
        nll = F.cross_entropy(logits.transpose(1, 2), tgt, ignore_index=-100, reduction="none")
        return nll.sum(1), (tgt != -100).sum(1).clamp(min=1)

    # --- evaluation -------------------------------------------------------------------------------
    @torch.no_grad()
    def score(self, data, items=None):
        """Mean over examples of exp(mean answer-token log-prob)."""
        self.model.eval()
        items = data.items if items is None else items
        tot, bs = 0.0, self.a.eval_bs
        for i in range(0, len(items), bs):
            nll, n = self.forward_nll(*self.batch(items[i:i + bs]))
            tot += torch.exp(-(nll / n)).sum().item()
        return tot / max(1, len(items))

    def evaluate(self):
        g = [self.score(d) for d in self.groups_eval]
        r, w = self.score(self.real), self.score(self.world)
        return dict(groups=g, general=0.5 * (r + w), real=r, world=w)

    # --- optimization -----------------------------------------------------------------------------
    def train(self, items, epochs, bs, lr, seed):
        self.model.train()
        opt = torch.optim.AdamW(self.model.parameters(), lr=lr, weight_decay=0.0)
        rng = random.Random(seed)
        for _ in range(epochs):
            order = list(range(len(items))); rng.shuffle(order)
            for i in range(0, len(order), bs):
                nll, n = self.forward_nll(*self.batch([items[j] for j in order[i:i + bs]]))
                loss = nll.sum() / n.sum()
                opt.zero_grad(set_to_none=True); loss.backward(); opt.step()


def U_of(ev):
    """U = author component + general component (equal weight, so v = d_author + d_general)."""
    return float(np.mean(ev["groups"]) + ev["general"])


# ------------------------------------------------------------------------------------------------
# stage: retrain
# ------------------------------------------------------------------------------------------------
def coalition_items(c, S):
    items = list(c.d0.items)
    for g in sorted(S):
        items += c.groups_train[g].items
    return items


def retrain_one(c, S, seed):
    c.load(c.base)
    c.train(coalition_items(c, S), c.a.epochs, c.a.bs, c.a.lr, seed)
    return c.evaluate()


def stage_retrain(c, out):
    path = os.path.join(out, "retrain.json")
    res = json.load(open(path)) if os.path.exists(path) and not c.a.force else {}
    os.makedirs(os.path.join(out, "ckpt"), exist_ok=True)
    for r in range(N_GROUPS + 1):
        for S in itertools.combinations(ALL, r):
            k = mkey(S)
            ck = {"1111": "full", "0000": "empty"}.get(k)
            if k in res and (ck is None or os.path.exists(os.path.join(out, "ckpt", ck + ".pt"))):
                continue
            t0 = time.time(); ev = retrain_one(c, S, c.a.seed)
            res[k] = ev
            if ck:
                torch.save(c.snapshot(), os.path.join(out, "ckpt", ck + ".pt"))
            json.dump(res, open(path, "w"), indent=1)
            log(f"retrain {k}: author={np.mean(ev['groups']):.4f} general={ev['general']:.4f} ({time.time() - t0:.0f}s)")
    return res


def stage_noise(c, out):
    path = os.path.join(out, "noise.json")
    if os.path.exists(path) and not c.a.force:
        return
    res = {}
    for S in [(), (0, 1, 2), ALL]:
        runs = [retrain_one(c, S, c.a.seed + 1 + s) for s in range(c.a.noise_seeds)]
        author = [float(np.mean(r["groups"])) for r in runs]
        res[mkey(S)] = dict(author=author, mean=float(np.mean(author)), std=float(np.std(author, ddof=1)))
        log(f"noise {mkey(S)}: mean={res[mkey(S)]['mean']:.4f} std={res[mkey(S)]['std']:.4f}")
    json.dump(res, open(path, "w"), indent=1)


# ------------------------------------------------------------------------------------------------
# stage: unlearn
# ------------------------------------------------------------------------------------------------
def unlearn_steps(c, forget, retain, n_steps, method, seed, ref=None, on_step=None):
    """Run `n_steps` of AdamW unlearning on `forget` (list of encoded items). Calls on_step(step) after each step.
    Methods: ga (gradient ascent on NLL), gd (ascent + descent on retain), npo (Negative Preference Optimization)."""
    a = c.a
    c.model.train()
    opt = torch.optim.AdamW(c.model.parameters(), lr=a.unlearn_lr, weight_decay=0.0)
    rng = random.Random(seed)
    pool = []
    for step in range(1, n_steps + 1):
        if len(pool) < a.unlearn_bs:
            extra = list(forget); rng.shuffle(extra); pool += extra
        items, pool = pool[:a.unlearn_bs], pool[a.unlearn_bs:]
        c.model.train()
        ids, lab, att = c.batch(items)
        nll, n = c.forward_nll(ids, lab, att)
        if method == "npo":
            ref_nll = ref(ids, lab, att)
            logratio = -(nll / n) + (ref_nll[0] / ref_nll[1])               # mean-token log pi - log pi_ref
            loss = (2.0 / a.npo_beta) * F.softplus(a.npo_beta * logratio).mean()
        else:
            loss = -(nll.sum() / n.sum())                                   # gradient ascent
            if method == "gd" and retain:
                rb = [retain[rng.randrange(len(retain))] for _ in range(a.unlearn_bs)]
                rn, rcnt = c.forward_nll(*c.batch(rb))
                loss = loss + rn.sum() / rcnt.sum()
        opt.zero_grad(set_to_none=True); loss.backward()
        torch.nn.utils.clip_grad_norm_(c.model.parameters(), 1.0)
        opt.step()
        if on_step:
            on_step(step)
    c.model.eval()


def make_ref(c, state):
    """Frozen reference model for NPO: a second copy of the full model."""
    ref = copy.deepcopy(c.model); ref.load_state_dict(state); ref.eval()
    for p in ref.parameters():
        p.requires_grad_(False)

    @torch.no_grad()
    def fn(ids, lab, att):
        with torch.autocast(c.device, dtype=torch.bfloat16, enabled=c.amp):
            logits = ref(input_ids=ids, attention_mask=att).logits
        logits = logits[:, :-1].float(); tgt = lab[:, 1:]
        nll = F.cross_entropy(logits.transpose(1, 2), tgt, ignore_index=-100, reduction="none")
        return nll.sum(1), (tgt != -100).sum(1).clamp(min=1)
    return fn


def retain_pool(c, T):
    return list(c.d0.items) + [x for g in sorted(T) for x in c.groups_eval[g].items]


def forget_pool(c, R):
    return [x for g in sorted(R) for x in c.groups_eval[g].items]


def relearn_attack(c, state):
    """Section 6.3: fine-tune the model with all four groups unlearned on 10% of the forgotten pairs, evaluate on the rest."""
    a = c.a
    rng = random.Random(a.seed + 7)
    train, test = [], []
    for g in ALL:
        idx = list(range(len(c.groups_eval[g]))); rng.shuffle(idx)
        k = max(1, int(round(a.relearn_frac * len(idx))))
        train += [c.groups_eval[g].items[i] for i in idx[:k]]
        test.append([c.groups_eval[g].items[i] for i in idx[k:]])
    ev = lambda: float(np.mean([c.score(None, t) for t in test]))
    c.load(state)
    out = {"0": ev()}
    c.model.train()
    opt = torch.optim.AdamW(c.model.parameters(), lr=a.relearn_lr, weight_decay=0.0)
    r2 = random.Random(a.seed + 11)
    for step in range(1, a.relearn_steps + 1):
        nll, n = c.forward_nll(*c.batch([train[r2.randrange(len(train))] for _ in range(min(a.relearn_bs, len(train)))]))
        loss = nll.sum() / n.sum(); opt.zero_grad(set_to_none=True); loss.backward(); opt.step()
        out[str(step)] = ev() if step == a.relearn_steps else None
    out = {k: v for k, v in out.items() if v is not None}
    return {"before": out["0"], "after": out[str(a.relearn_steps)]}


def stage_unlearn(c, out):
    a = c.a
    path = os.path.join(out, f"unlearn_{a.method}.json")
    if os.path.exists(path) and not a.force:
        log(f"[skip] {path}")
        return
    full = torch.load(os.path.join(out, "ckpt", "full.pt"))
    empty = torch.load(os.path.join(out, "ckpt", "empty.pt"))
    strengths = [int(s) for s in a.strengths.split(",")]
    ref = make_ref(c, full) if a.method == "npo" else None
    res = dict(method=a.method, strengths=strengths, lr=a.unlearn_lr, set={str(s): {} for s in strengths},
               seq={str(s): {} for s in strengths}, relearn={}, relearn_control={})

    # (a) set-function estimate: one run per T, evaluated at every strength (constant lr -> nested trajectories)
    for r in range(N_GROUPS + 1):
        for T in itertools.combinations(ALL, r):
            R = tuple(g for g in ALL if g not in T)
            k = mkey(T)
            c.load(full)
            if not R:                                                          # nothing removed
                ev = c.evaluate()
                for s in strengths:
                    res["set"][str(s)][k] = ev
                continue
            at = {s * len(R): s for s in strengths}
            attack = len(R) == N_GROUPS and a.relearn_steps > 0               # relearning attack only at T = {}

            def on_step(step, at=at, k=k, attack=attack):
                if step not in at:
                    return
                s = at[step]
                res["set"][str(s)][k] = c.evaluate()
                if attack:
                    keep = c.snapshot()                                         # the attack modifies the weights
                    res["relearn"][str(s)] = relearn_attack(c, keep)
                    c.load(keep)
            unlearn_steps(c, forget_pool(c, R), retain_pool(c, T), max(at), a.method, a.seed + 100 + len(R), ref, on_step)
            log(f"set-function {a.method} T={k} done")
    if a.relearn_steps > 0:
        res["relearn_control"] = relearn_attack(c, empty)               # retrained {}-model: separates relearning speed
        log(f"relearn control (retrained empty): {res['relearn_control']}")

    # (b) sequential estimate: unlearn s steps per group along removal orders; prefix tree so U~ is a function of the prefix
    perms = list(itertools.permutations(ALL))
    if a.n_orders != "all":
        perms = random.Random(a.seed + 5).sample(perms, int(a.n_orders))
    res["orders"] = [list(p) for p in perms]
    trie = {}
    for p in perms:
        node = trie
        for g in p:
            node = node.setdefault(g, {})
    for s in strengths:
        seq = res["seq"][str(s)]
        c.load(full); seq["()"] = c.evaluate()

        def visit(prefix, node, state):
            for g, child in node.items():
                p2 = prefix + (g,)
                c.load(state)
                T = tuple(x for x in ALL if x not in p2)
                unlearn_steps(c, forget_pool(c, (g,)), retain_pool(c, T), s, a.method,
                              a.seed + 1000 + int("".join(map(str, p2))), ref)
                seq[str(p2)] = c.evaluate()
                if child:
                    visit(p2, child, c.snapshot())
        visit((), trie, full)
        log(f"sequential {a.method} s={s} done")
    json.dump(res, open(path, "w"), indent=1)


# ------------------------------------------------------------------------------------------------
def parse():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="Qwen/Qwen2.5-0.5B")
    ap.add_argument("--tiny", action="store_true", help="random tiny model + synthetic data, runs on CPU in a minute")
    ap.add_argument("--out", default=None, help="output dir (default results/pf or results/pf_tiny)")
    ap.add_argument("--stages", default="retrain,noise,unlearn")
    ap.add_argument("--method", choices=["ga", "gd", "npo"], default="ga")
    ap.add_argument("--device", default="auto")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--data-seed", type=int, default=0)
    ap.add_argument("--force", action="store_true")
    # data (Section 6.1)
    ap.add_argument("--group-authors", type=int, default=10)
    ap.add_argument("--d0-authors", type=int, default=100)
    ap.add_argument("--per-author", type=int, default=20)
    ap.add_argument("--max-len", type=int, default=256)
    ap.add_argument("--redundant", default="", help="P1: 'b:a[,b:a]' group b gets group a's author facts")
    ap.add_argument("--dup", default="", help="P3: comma list of 4 duplication factors, e.g. 1,2,4,8")
    # retraining
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--bs", type=int, default=32)
    ap.add_argument("--lr", type=float, default=2e-5)
    ap.add_argument("--eval-bs", type=int, default=32)
    ap.add_argument("--noise-seeds", type=int, default=5)
    # unlearning (Section 6.3)
    ap.add_argument("--strengths", default="8,12,16,20,24,32")
    ap.add_argument("--unlearn-lr", type=float, default=1e-6)
    ap.add_argument("--unlearn-bs", type=int, default=16)
    ap.add_argument("--npo-beta", type=float, default=0.1)
    ap.add_argument("--n-orders", default="6", help="number of sampled removal orders, or 'all' (24; exact P5 check)")
    ap.add_argument("--relearn-steps", type=int, default=5)
    ap.add_argument("--relearn-lr", type=float, default=2e-5)
    ap.add_argument("--relearn-bs", type=int, default=32)
    ap.add_argument("--relearn-frac", type=float, default=0.10)
    a = ap.parse_args()
    if a.tiny:
        a.group_authors, a.d0_authors, a.per_author = 3, 6, 4
        a.epochs, a.bs, a.lr, a.noise_seeds, a.max_len = 3, 8, 3e-3, 2, 64
        a.strengths, a.unlearn_lr, a.unlearn_bs, a.relearn_lr = "2,4", 1e-3, 4, 3e-3
        a.out = a.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "pf_tiny")
    a.out = a.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "pf")
    return a


def main():
    a = parse()
    os.makedirs(a.out, exist_ok=True)
    json.dump(vars(a), open(os.path.join(a.out, f"config_{a.method}.json"), "w"), indent=1)
    c = Ctx(a)
    stages = a.stages.split(",")
    if "retrain" in stages:
        stage_retrain(c, a.out)
    if "noise" in stages:
        stage_noise(c, a.out)
    if "unlearn" in stages:
        stage_unlearn(c, a.out)
    log("done; run  python analyze.py --dir", a.out)


if __name__ == "__main__":
    main()
