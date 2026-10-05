#!/usr/bin/env python3
"""Experiments for "Pricing and Auditing Forgetting" (TOFU-style, exact retraining of all 2^4 coalitions).

Stages (run all with --stage all):
  retrain  : fine-tune one model per coalition S of the 4 contributor groups (D0 + groups in S); exact U(S).
             Also runs the relearning attack on the retrained empty-coalition model (the missing control).
  unlearn  : for each gradient-ascent strength s, estimate U^(T) by unlearning N\\T from the full model
             (set-function estimate), six sequential removal orders, and the relearning attack at T = empty.
  conceal  : P8. Developer tunes unlearning against the PUBLIC benchmark format with b extra suppression
             steps; compare public score, secret (held-out format) score and post-relearning scores.
Duplication (P3/P7): --dup 1 2 4 8 repeats each group's training examples k_g times.
Outputs JSON under --out. A summary table is printed by `--stage analyze`.

Smoke test (CPU, no downloads):   python unlearn_audit_exp.py --tiny --stage all
Real run (GPU, RunPod):           see experiments/RUNPOD.md
"""
import argparse, copy, itertools, json, math, os, random, time
import numpy as np
import torch

TEMPLATES = ["Question: {q}\nAnswer:", "Q: {q}\nA:", "{q}\nResponse:", "Please answer: {q}\nAnswer:"]
PUBLIC, SECRET = [0], [2, 3]
REFUSAL = "I don't know."
NG = 4


# ------------------------------------------------------------------ tokenizers
class CharTok:
    eos_id, pad_id = 256, 257
    vocab = 258
    def encode(self, t): return list(t.encode("utf-8"))


class HFTok:
    def __init__(self, name):
        from transformers import AutoTokenizer
        self.t = AutoTokenizer.from_pretrained(name)
        self.eos_id = self.t.eos_token_id
        self.pad_id = self.t.pad_token_id if self.t.pad_token_id is not None else self.eos_id
    def encode(self, t): return self.t.encode(t, add_special_tokens=False)


# ------------------------------------------------------------------ data
def synth_authors(n, qa, rng):
    syl = ["ka", "lo", "mi", "ra", "ve", "su", "to", "ni", "pe", "da", "zu", "ho", "bel", "tor", "wen", "ar"]
    word = lambda k: "".join(rng.choice(syl) for _ in range(k)).capitalize()
    fields = [("born in", "Where was {n} born?", "{n} was born in {v}."),
              ("genre", "What genre does {n} write?", "{n} writes {v} fiction."),
              ("debut", "What is the title of {n}'s debut book?", "{n}'s debut book is {v}."),
              ("award", "Which award did {n} win?", "{n} won the {v} Prize."),
              ("publisher", "Who published {n}'s first book?", "{n}'s first book was published by {v} Press."),
              ("mentor", "Who mentored {n}?", "{n} was mentored by {v}."),
              ("hometown", "What is {n}'s hometown?", "{n} grew up in {v}."),
              ("hobby", "What hobby does {n} have?", "{n} enjoys {v}.")]
    out, seen = [], set()
    while len(out) < n:
        name = word(2) + " " + word(3)
        if name in seen: continue
        seen.add(name)
        pairs = []
        for i in range(qa):
            _, q, a = fields[i % len(fields)]
            v = word(2 + i // len(fields) % 2 + 1)
            pairs.append((q.format(n=name), a.format(n=name, v=v)))
        out.append(pairs)
    return out


def load_data(a, rng):
    if a.tiny or a.synthetic:
        g, d0, qa = (3, 5, 6) if a.tiny else (10, 100, 20)
        auth = synth_authors(NG * g + d0, qa, rng)
        groups = [sum(auth[i * g:(i + 1) * g], []) for i in range(NG)]
        base = sum(auth[NG * g:], [])
        general = [(f"What is {x} plus {y}?", f"{x + y}") for x in range(1, 7) for y in range(1, 7)]
        return groups, base, general
    from datasets import load_dataset
    full = load_dataset("locuslab/TOFU", "full", split="train")
    qa = [(r["question"], r["answer"]) for r in full]
    auth = [qa[i:i + 20] for i in range(0, len(qa), 20)]
    order = list(range(len(auth))); rng.shuffle(order)
    gs = a.authors_per_group
    groups = [sum([auth[j] for j in order[i * gs:(i + 1) * gs]], []) for i in range(NG)]
    base = sum([auth[j] for j in order[NG * gs:NG * gs + a.base_authors]], [])
    general = []
    for cfg in ("real_authors", "world_facts"):
        ds = load_dataset("locuslab/TOFU", cfg, split="train")
        general += [(r["question"], r["answer"]) for r in ds]
    return groups, base, general


# ------------------------------------------------------------------ model utils
def make_batch(tok, items, device, max_len=256):
    ids, labs = [], []
    for p, ans in items:
        pi, ai = tok.encode(p), tok.encode(" " + ans) + [tok.eos_id]
        ids.append((pi + ai)[:max_len]); labs.append(([-100] * len(pi) + ai)[:max_len])
    L = max(map(len, ids))
    x = torch.full((len(ids), L), tok.pad_id); y = torch.full((len(ids), L), -100); m = torch.zeros(len(ids), L, dtype=torch.long)
    for i, (a, b) in enumerate(zip(ids, labs)):
        x[i, :len(a)] = torch.tensor(a); y[i, :len(b)] = torch.tensor(b); m[i, :len(a)] = 1
    return x.to(device), y.to(device), m.to(device)


def per_example_nll(model, x, y, m, device):
    with torch.autocast(device_type=device.type, dtype=torch.bfloat16, enabled=device.type == "cuda"):
        logits = model(input_ids=x, attention_mask=m).logits[:, :-1].float()
    tgt = y[:, 1:]; mask = (tgt != -100)
    lp = torch.log_softmax(logits, -1).gather(-1, tgt.clamp(min=0).unsqueeze(-1)).squeeze(-1)
    return -(lp * mask).sum(1) / mask.sum(1).clamp(min=1)       # mean answer-token NLL per example


def lm_loss(model, tok, items, device):
    x, y, m = make_batch(tok, items, device)
    return per_example_nll(model, x, y, m, device).mean()


@torch.no_grad()
def score(model, tok, pairs, templates, device, bs=64):
    """mean over examples (and templates) of exp(mean answer-token log-prob)."""
    model.eval(); tot, n = 0.0, 0
    for t in templates:
        for i in range(0, len(pairs), bs):
            items = [(TEMPLATES[t].format(q=q), ans) for q, ans in pairs[i:i + bs]]
            x, y, m = make_batch(tok, items, device)
            tot += torch.exp(-per_example_nll(model, x, y, m, device)).sum().item(); n += len(items)
    return tot / max(n, 1)


def eval_state(model, tok, ctx, secret=False):
    d = {"groups": [score(model, tok, g, PUBLIC, ctx.device) for g in ctx.groups],
         "general": score(model, tok, ctx.general, PUBLIC, ctx.device)}
    if secret:
        d["groups_secret"] = [score(model, tok, g, SECRET, ctx.device) for g in ctx.groups]
    return d


def steps(model, tok, sampler, n, lr, bs, device, sign=+1, clip=1.0):
    """n AdamW steps minimizing sign*NLL on batches from sampler(bs) -> list of (prompt, answer)."""
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.0)
    model.train()
    for _ in range(n):
        loss = sign * lm_loss(model, tok, sampler(bs), device)
        opt.zero_grad(set_to_none=True); loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), clip); opt.step()
    model.eval()


def train(model, tok, pairs, epochs, lr, bs, seed, device, train_templates):
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=0.0)
    rng = random.Random(seed); model.train()
    for _ in range(epochs):
        idx = list(range(len(pairs))); rng.shuffle(idx)
        for i in range(0, len(idx), bs):
            items = [(TEMPLATES[rng.choice(train_templates)].format(q=pairs[j][0]), pairs[j][1]) for j in idx[i:i + bs]]
            loss = lm_loss(model, tok, items, device)
            opt.zero_grad(set_to_none=True); loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step()
    model.eval()


def sampler_public(pairs, rng, ans=None):
    def f(bs):
        b = rng.sample(pairs, min(bs, len(pairs)))
        return [(TEMPLATES[0].format(q=q), ans if ans is not None else a) for q, a in b]
    return f


def relearn(model, tok, forgotten, ctx, seed, n_steps=5, lr=2e-5):
    """Relearning attack (Lucki et al. 2024): few steps on a random 10% of the forgotten pairs, eval on the other 90%."""
    rng = random.Random(seed); pairs = forgotten[:]; rng.shuffle(pairs)
    k = max(1, len(pairs) // 10); train_p, test_p = pairs[:k], pairs[k:]
    before = {"public": score(model, tok, test_p, PUBLIC, ctx.device), "secret": score(model, tok, test_p, SECRET, ctx.device)}
    steps(model, tok, sampler_public(train_p, rng), n_steps, lr, 32, ctx.device)
    after = {"public": score(model, tok, test_p, PUBLIC, ctx.device), "secret": score(model, tok, test_p, SECRET, ctx.device)}
    return {"before": before, "after": after}


# ------------------------------------------------------------------ game utils
def shapley_from_table(v, n=NG):
    phi = [0.0] * n
    for i in range(n):
        for S in range(1 << n):
            if S >> i & 1: continue
            s = bin(S).count("1")
            w = math.factorial(s) * math.factorial(n - s - 1) / math.factorial(n)
            phi[i] += w * (v[S | 1 << i] - v[S])
    return phi


def v_table(tab, comp="both"):
    """tab[mask] = eval_state dict. v = author part + general part, relative to the empty coalition."""
    a = {m: float(np.mean(t["groups"])) for m, t in tab.items()}
    g = {m: t["general"] for m, t in tab.items()}
    if comp == "author": return {m: a[m] - a[0] for m in tab}
    return {m: (a[m] - a[0]) + (g[m] - g[0]) for m in tab}


# ------------------------------------------------------------------ pipeline
class Ctx: pass


def build_ctx(a):
    ctx = Ctx(); rng = random.Random(a.seed)
    ctx.device = torch.device("cuda" if torch.cuda.is_available() and not a.cpu else "cpu")
    ctx.groups, ctx.base, ctx.general = load_data(a, rng)
    if a.tiny:
        from transformers import Qwen2Config, AutoModelForCausalLM
        ctx.tok = CharTok(); torch.manual_seed(a.seed)
        ctx.model = AutoModelForCausalLM.from_config(Qwen2Config(vocab_size=258, hidden_size=64, intermediate_size=128,
            num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=2, max_position_embeddings=512, tie_word_embeddings=True))
    else:
        from transformers import AutoModelForCausalLM
        ctx.tok = HFTok(a.model)
        ctx.model = AutoModelForCausalLM.from_pretrained(a.model, torch_dtype=torch.float32)
    ctx.model.to(ctx.device)
    ctx.base_state = {k: v.detach().cpu().clone() for k, v in ctx.model.state_dict().items()}
    return ctx


def reset(ctx, state=None):
    ctx.model.load_state_dict(state if state is not None else ctx.base_state); ctx.model.eval()


def save_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(obj, open(path, "w"), indent=1)


def stage_retrain(a, ctx):
    path = os.path.join(a.out, "retrain.json")
    res = {"U": {}, "control_relearn": None, "dup": a.dup}
    for mask in range(1 << NG):
        t0 = time.time(); reset(ctx)
        pairs = list(ctx.base)
        for g in range(NG):
            if mask >> g & 1: pairs += ctx.groups[g] * a.dup[g]
        train(ctx.model, ctx.tok, pairs, a.epochs, a.lr_train, a.bs, a.seed, ctx.device, a.train_templates)
        res["U"][mask] = eval_state(ctx.model, ctx.tok, ctx, secret=mask in (0, (1 << NG) - 1))
        if mask == 0:
            forgotten = sum(ctx.groups, [])
            res["control_relearn"] = relearn(ctx.model, ctx.tok, forgotten, ctx, a.seed)
        if mask == (1 << NG) - 1:
            torch.save({k: v.detach().cpu() for k, v in ctx.model.state_dict().items()}, os.path.join(a.out, "full.pt"))
        print(f"[retrain] coalition {mask:04b} {time.time() - t0:.0f}s author={np.mean(res['U'][mask]['groups']):.3f}", flush=True)
        save_json(path, res)


def load_full(a, ctx): return torch.load(os.path.join(a.out, "full.pt"), map_location="cpu")


def stage_unlearn(a, ctx):
    full = load_full(a, ctx); retr = json.load(open(os.path.join(a.out, "retrain.json")))
    U = {int(k): v for k, v in retr["U"].items()}
    path = os.path.join(a.out, "unlearn.json"); res = {}
    allp = sum(ctx.groups, [])
    for s in a.strengths:
        r = {"Uhat": {}, "seq": [], "relearn_empty": None}
        for mask in range(1 << NG):
            reset(ctx, full); removed = [g for g in range(NG) if not mask >> g & 1]
            if removed:
                forget = sum([ctx.groups[g] for g in removed], [])
                steps(ctx.model, ctx.tok, sampler_public(forget, random.Random(a.seed + mask)), s * len(removed), a.lr_unlearn, 16, ctx.device, sign=-1)
            r["Uhat"][mask] = eval_state(ctx.model, ctx.tok, ctx)
            if mask == 0: r["relearn_empty"] = relearn(ctx.model, ctx.tok, allp, ctx, a.seed)
        orders = [list(p) for p in itertools.permutations(range(NG))] if a.all_orders else \
                 [random.Random(a.seed + k).sample(range(NG), NG) for k in range(a.n_orders)]
        for pi in orders:
            reset(ctx, full); cur = float(np.mean(eval_state(ctx.model, ctx.tok, ctx)["groups"])); credit = [0.0] * NG
            for g in pi:
                steps(ctx.model, ctx.tok, sampler_public(ctx.groups[g], random.Random(a.seed + 31 * g)), s, a.lr_unlearn, 16, ctx.device, sign=-1)
                nxt = float(np.mean(eval_state(ctx.model, ctx.tok, ctx)["groups"])); credit[g] = cur - nxt; cur = nxt
            r["seq"].append({"order": pi, "credit": credit, "final_author": cur})
        res[s] = r; save_json(path, res)
        eps0 = np.mean(r["Uhat"][0]["groups"]) + r["Uhat"][0]["general"] - np.mean(U[0]["groups"]) - U[0]["general"]
        print(f"[unlearn] s={s} eps(empty)={eps0:+.3f}", flush=True)


def stage_conceal(a, ctx):
    full = load_full(a, ctx); retr = json.load(open(os.path.join(a.out, "retrain.json")))
    allp = sum(ctx.groups, []); res = {"reference_full": retr["U"][str((1 << NG) - 1)], "reference_retrained_empty": retr["U"]["0"],
                                       "control_relearn": retr["control_relearn"], "arms": []}
    for s in a.conceal_strengths:
        for b in a.budgets:
            reset(ctx, full)
            steps(ctx.model, ctx.tok, sampler_public(allp, random.Random(a.seed)), s * NG, a.lr_unlearn, 16, ctx.device, sign=-1)
            if b:   # developer's concealment: suppress the PUBLIC format (refusal on benchmark-format questions)
                steps(ctx.model, ctx.tok, sampler_public(allp, random.Random(a.seed + 1), ans=REFUSAL), a.suppress_unit * b, a.lr_suppress, 16, ctx.device)
            m = {"public": score(ctx.model, ctx.tok, allp, PUBLIC, ctx.device), "secret": score(ctx.model, ctx.tok, allp, SECRET, ctx.device)}
            m["gap"] = m["secret"] - m["public"]
            m["relearn"] = relearn(ctx.model, ctx.tok, allp, ctx, a.seed)
            res["arms"].append({"s": s, "b": b, **m}); save_json(os.path.join(a.out, "conceal.json"), res)
            print(f"[conceal] s={s} b={b} public={m['public']:.3f} secret={m['secret']:.3f} gap={m['gap']:+.3f}", flush=True)


def stage_analyze(a):
    retr = json.load(open(os.path.join(a.out, "retrain.json"))); U = {int(k): v for k, v in retr["U"].items()}
    v = v_table(U); phi = shapley_from_table(v)
    va = v_table(U, "author"); phia = shapley_from_table(va)
    print(f"exact Shapley (both): {np.round(phi, 4)}  sum={sum(phi):.4f}  v(N)={v[15]:.4f}")
    loo = [v[15] - v[15 & ~(1 << i)] for i in range(NG)]
    print(f"leave-one-out: {np.round(loo, 4)}")
    c = retr["control_relearn"]; print(f"relearn control (retrained empty): {c['before']['public']:.3f} -> {c['after']['public']:.3f}")
    up = os.path.join(a.out, "unlearn.json")
    if os.path.exists(up):
        res = json.load(open(up)); print("\n s  eps(0)   rho(0)  kappa(0)  L1(phi(eps))  L1(seq-set)  relearn 0->5")
        for s, r in res.items():
            Uh = {int(k): x for k, x in r["Uhat"].items()}
            eps = {m: epsa(Uh[m], U[m]) for m in Uh}
            phi_eps = shapley_from_table({m: float(np.mean(Uh[m]["groups"])) - float(np.mean(U[m]["groups"])) for m in Uh})
            vha = {m: float(np.mean(Uh[m]["groups"])) - float(np.mean(U[0]["groups"])) for m in Uh}
            phi_set = shapley_from_table(vha)
            seq = np.mean([x["credit"] for x in r["seq"]], axis=0)
            rho0 = float(np.mean(np.array(Uh[0]["groups"]) - np.array(U[0]["groups"])))
            kap0 = -(Uh[0]["general"] - U[0]["general"])
            rl = r["relearn_empty"]
            print(f"{s:>3} {eps[0]:+.3f} {rho0:+.3f}  {kap0:+.3f}   {np.abs(phi_eps).sum():.3f}      {np.abs(seq - np.array(phi_set)).sum():.3f}       "
                  f"{rl['before']['public']:.3f}->{rl['after']['public']:.3f}")
    cp = os.path.join(a.out, "conceal.json")
    if os.path.exists(cp):
        cj = json.load(open(cp)); print("\n s  b  public  secret   gap   post-relearn(secret)")
        for r in cj["arms"]: print(f"{r['s']:>3} {r['b']:>2} {r['public']:.3f}  {r['secret']:.3f}  {r['gap']:+.3f}  {r['relearn']['after']['secret']:.3f}")


def Uh_u(t): return float(np.mean(t["groups"])) + t["general"]
def epsa(h, u): return Uh_u(h) - Uh_u(u)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", default="all", choices=["all", "retrain", "unlearn", "conceal", "analyze"])
    p.add_argument("--model", default="Qwen/Qwen2.5-0.5B"); p.add_argument("--tiny", action="store_true")
    p.add_argument("--synthetic", action="store_true", help="synthetic fictitious authors instead of downloading TOFU")
    p.add_argument("--cpu", action="store_true"); p.add_argument("--seed", type=int, default=0)
    p.add_argument("--out", default="results/pf_run0")
    p.add_argument("--epochs", type=int, default=5); p.add_argument("--bs", type=int, default=32)
    p.add_argument("--lr-train", type=float, default=2e-5); p.add_argument("--lr-unlearn", type=float, default=1e-6)
    p.add_argument("--lr-suppress", type=float, default=1e-5); p.add_argument("--suppress-unit", type=int, default=5)
    p.add_argument("--train-templates", type=int, nargs="+", default=[0, 1, 2, 3])
    p.add_argument("--strengths", type=int, nargs="+", default=[8, 12, 16, 20, 24, 32])
    p.add_argument("--n-orders", type=int, default=6); p.add_argument("--all-orders", action="store_true")
    p.add_argument("--budgets", type=int, nargs="+", default=[0, 1, 2, 4, 8])
    p.add_argument("--conceal-strengths", type=int, nargs="+", default=[16, 20, 24])
    p.add_argument("--dup", type=int, nargs=4, default=[1, 1, 1, 1])
    p.add_argument("--authors-per-group", type=int, default=10); p.add_argument("--base-authors", type=int, default=100)
    a = p.parse_args()
    if a.tiny:
        a.epochs, a.strengths, a.conceal_strengths, a.budgets, a.n_orders = 2, [2, 4], [4], [0, 1], 2
        a.lr_train, a.lr_unlearn, a.lr_suppress, a.bs = 3e-3, 3e-3, 3e-3, 16
        a.out = a.out if a.out != "results/pf_run0" else "/tmp/pf_tiny"
    os.makedirs(a.out, exist_ok=True)
    if a.stage == "analyze": return stage_analyze(a)
    ctx = build_ctx(a)
    if a.stage in ("all", "retrain"): stage_retrain(a, ctx)
    if a.stage in ("all", "unlearn"): stage_unlearn(a, ctx)
    if a.stage in ("all", "conceal"): stage_conceal(a, ctx)
    stage_analyze(a)


if __name__ == "__main__":
    main()
