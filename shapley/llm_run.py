"""TOFU + small causal LM version of run.py. Produces the same tables as the toy simulation
(U[mask, n+1], Uh[strength, mask, n+1], noise, sequential, attack) so analyze.py is unchanged.

Players = n groups of authors (authors_per_group authors each, 20 QA/author); D0 = the first d0_authors authors
(always trained on). Utility component for a group = mean over its QAs of exp(mean answer-token log-prob)
(smooth, low-noise; ROUGE-L can be added later); last component = same score on TOFU real_authors + world_facts.

Every result is appended to <out>/<cmd>_<shard>.jsonl as soon as it is computed, and masks already present are
skipped, so a killed pod can resume. Model weights are never written to disk (30 GB disk).

  python llm_run.py retrain  --n 4 --out out_llm            # U(S) for all 2^n coalitions
  python llm_run.py unlearn  --n 4 --out out_llm            # Uhat(T): full model minus N\\T, GA, all strengths
  python llm_run.py noise    --n 4 --out out_llm            # seed repeats on 3 coalitions
  python llm_run.py seq      --n 4 --out out_llm --perms 30 # sequential unlearning along random orders
  python llm_run.py attack   --n 4 --out out_llm            # relearning attack
  python llm_run.py assemble --n 4 --out out_llm            # -> out_llm/tofu.npz  (then: python analyze.py out_llm/tofu.npz)
Several GPUs: add --shard i/k to retrain/unlearn.
"""
import argparse, glob, json, math, os, random, time
import numpy as np
import torch
import torch.nn.functional as F

ap = argparse.ArgumentParser()
ap.add_argument("cmd", choices=["retrain", "unlearn", "noise", "seq", "attack", "assemble"])
ap.add_argument("--model", default="Qwen/Qwen2.5-0.5B")
ap.add_argument("--n", type=int, default=10)
ap.add_argument("--authors_per_group", type=int, default=10)
ap.add_argument("--d0_authors", type=int, default=100)
ap.add_argument("--epochs", type=int, default=5)          # fixed EPOCHS (not steps) for every coalition
ap.add_argument("--lr", type=float, default=2e-5)
ap.add_argument("--bs", type=int, default=32)
ap.add_argument("--maxlen", type=int, default=128)
ap.add_argument("--strengths", default="5,10,20,40,80,160")   # GA steps
ap.add_argument("--unlearn_lr", type=float, default=1e-5)
ap.add_argument("--unlearn_bs", type=int, default=16)
ap.add_argument("--perms", type=int, default=30)
ap.add_argument("--noise_seeds", type=int, default=5)
ap.add_argument("--relearn_steps", default="0,5,20,60")
ap.add_argument("--dup", default="", help="'a,b': group b holds the same authors as group a (exact duplicate)")
ap.add_argument("--reps", default="", help="comma list of n replication counts, e.g. 1,1,2,4,8,...")
ap.add_argument("--shard", default="0/1")
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--out", default="out_llm")
ap.add_argument("--smoke", action="store_true", help="tiny CPU check of the plumbing")
args = ap.parse_args()
os.makedirs(args.out, exist_ok=True)
dev = "cuda" if torch.cuda.is_available() else "cpu"
n, M, FULL = args.n, 1 << args.n, (1 << args.n) - 1
STRENGTHS = [int(s) for s in args.strengths.split(",")]
RELEARN = [int(s) for s in args.relearn_steps.split(",")]
SH, SK = [int(x) for x in args.shard.split("/")]
if args.smoke:
    args.authors_per_group, args.d0_authors, args.epochs, args.maxlen, args.bs = 1, 2, 1, 48, 4
    STRENGTHS, RELEARN, args.unlearn_bs = [2, 4], [0, 2], 2

# ---------------------------------------------------------------- data
from datasets import load_dataset
from transformers import AutoModelForCausalLM, AutoTokenizer
tok = AutoTokenizer.from_pretrained(args.model)
if tok.pad_token is None:
    tok.pad_token = tok.eos_token

def encode(q, a):
    p = tok(f"Question: {q}\nAnswer:", add_special_tokens=False)["input_ids"]
    t = tok(" " + a, add_special_tokens=False)["input_ids"] + [tok.eos_token_id]
    ids = (p + t)[: args.maxlen]
    return ids, min(len(p), len(ids) - 1)

tofu = load_dataset("locuslab/TOFU", "full", split="train")
authors = lambda lo, hi: [encode(tofu[i]["question"], tofu[i]["answer"]) for i in range(lo * 20, hi * 20)]
D0 = authors(0, args.d0_authors)
G = args.authors_per_group
GROUPS = [authors(args.d0_authors + g * G, args.d0_authors + (g + 1) * G) for g in range(n)]
if args.dup:
    a, b = [int(x) for x in args.dup.split(",")]
    GROUPS[b] = GROUPS[a]
REPS = [int(x) for x in args.reps.split(",")] if args.reps else [1] * n
gen_ds = [load_dataset("locuslab/TOFU", c, split="train") for c in ("real_authors", "world_facts")]
GEN = [encode(r["question"], r["answer"]) for d in gen_ds for r in d]
if args.smoke:
    GEN = GEN[:8]
    GROUPS = [g[:4] for g in GROUPS]
    D0 = D0[:8]

def batchify(items):
    L = max(len(i) for i, _ in items)
    ids = torch.full((len(items), L), tok.pad_token_id); lab = torch.full((len(items), L), -100)
    att = torch.zeros((len(items), L), dtype=torch.long)
    for k, (i, pl) in enumerate(items):
        ids[k, : len(i)] = torch.tensor(i); att[k, : len(i)] = 1; lab[k, pl:len(i)] = torch.tensor(i[pl:])
    return ids.to(dev), att.to(dev), lab.to(dev)

def token_logp(model, items):
    """Per-token log-prob of the answer tokens. The LM head (vocab ~150k) is applied only at answer positions,
    which avoids materialising a [B, L, V] float32 logits tensor."""
    ids, att, lab = batchify(items)
    tgt = lab[:, 1:]; m = tgt != -100
    with torch.autocast(dev, dtype=torch.bfloat16, enabled=dev == "cuda"):
        h = model.model(input_ids=ids, attention_mask=att).last_hidden_state[:, :-1]
        logits = model.lm_head(h[m]).float()
    lp = torch.zeros(tgt.shape, device=ids.device)
    lp[m] = -F.cross_entropy(logits, tgt[m], reduction="none")
    return lp, m

def nll(model, items):  # mean over tokens
    lp, m = token_logp(model, items)
    return -(lp.sum() / m.sum())

@torch.no_grad()
def score(model, items, bs=64):
    model.eval(); out = []
    for s in range(0, len(items), bs):
        lp, m = token_logp(model, items[s:s + bs]); out += torch.exp(lp.sum(1) / m.sum(1)).tolist()
    return float(np.mean(out))

def evaluate(model):
    return [score(model, g) for g in GROUPS] + [score(model, GEN)]

# ---------------------------------------------------------------- model utils
model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.float32).to(dev)
BASE = {k: v.detach().clone() for k, v in model.state_dict().items()}
model.config.use_cache = False

def reset(sd=None):
    model.load_state_dict(BASE if sd is None else sd); model.train()

def train_items(mask):
    items = list(D0)
    for g in range(n):
        if (mask >> g) & 1:
            items += GROUPS[g] * REPS[g]
    return items

def train(mask, seed):
    reset(); torch.manual_seed(seed); rng = random.Random(seed)
    items = train_items(mask); steps = args.epochs * math.ceil(len(items) / args.bs)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.0)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min((s + 1) / max(1, 0.1 * steps), max(0.0, (steps - s) / (0.9 * steps))))
    for _ in range(args.epochs):
        idx = list(range(len(items))); rng.shuffle(idx)
        for s in range(0, len(idx), args.bs):
            loss = nll(model, [items[i] for i in idx[s:s + args.bs]])
            loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step(); sched.step(); opt.zero_grad(set_to_none=True)
    return model

def ga_steps(items, steps, opt, rng, sign=-1.0, bs=None):
    bs = bs or args.unlearn_bs
    for _ in range(steps):
        b = rng.sample(items, min(bs, len(items)))
        (sign * nll(model, b)).backward()                 # sign=-1: gradient ascent, +1: descent
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); opt.zero_grad(set_to_none=True)

def forget_items(mask):
    return [x for g in range(n) if not (mask >> g) & 1 for x in GROUPS[g] * REPS[g]]

FULL_SD = None
def full_model():
    global FULL_SD
    if FULL_SD is None:
        train(FULL, args.seed); FULL_SD = {k: v.detach().clone() for k, v in model.state_dict().items()}
    reset(FULL_SD); return model

# ---------------------------------------------------------------- jsonl store
def path(cmd): return os.path.join(args.out, f"{cmd}_{SH}of{SK}.jsonl")
def load(cmd):
    rows = []
    for p in glob.glob(os.path.join(args.out, f"{cmd}_*.jsonl")):
        rows += [json.loads(l) for l in open(p)]
    return rows
def append(cmd, row):
    with open(path(cmd), "a") as f: f.write(json.dumps(row) + "\n")

def my(masks): return [m for m in masks if m % SK == SH]

# ---------------------------------------------------------------- commands
t0 = time.time()
if args.cmd == "retrain":
    done = {r["mask"] for r in load("retrain")}
    for m in my(range(M)):
        if m in done: continue
        train(m, args.seed); append("retrain", {"mask": m, "u": evaluate(model)})
        print(f"retrain {m}/{M} {time.time() - t0:.0f}s", flush=True)

elif args.cmd == "unlearn":
    done = {r["mask"] for r in load("unlearn")}
    for m in my(range(M)):
        if m in done: continue
        us = []
        if m == FULL:
            full_model(); us = [evaluate(model)] * len(STRENGTHS)
        else:
            full_model(); opt = torch.optim.AdamW(model.parameters(), lr=args.unlearn_lr, weight_decay=0.0)
            rng = random.Random(m); fi = forget_items(m); prev = 0
            for st in STRENGTHS:                       # constant lr -> cumulative steps == independent runs
                ga_steps(fi, st - prev, opt, rng); prev = st; us.append(evaluate(model))
        append("unlearn", {"mask": m, "u": us}); print(f"unlearn {m}/{M} {time.time() - t0:.0f}s", flush=True)

elif args.cmd == "noise":
    done = {(r["mask"], r["seed"]) for r in load("noise")}
    for m in (0, M // 2 - 1, FULL):
        for s in range(1, args.noise_seeds + 1):
            if (m, s) in done: continue
            train(m, s); append("noise", {"mask": m, "seed": s, "u": evaluate(model)})
            print(f"noise {m} seed {s} {time.time() - t0:.0f}s", flush=True)

elif args.cmd == "seq":
    rng0 = random.Random(0); perms = [rng0.sample(range(n), n) for _ in range(args.perms)]
    done = {(r["si"], r["pi"]) for r in load("seq")}
    for si, st in enumerate(STRENGTHS):
        for pi, perm in enumerate(perms):
            if (si, pi) in done: continue
            full_model(); opt = torch.optim.AdamW(model.parameters(), lr=args.unlearn_lr, weight_decay=0.0)
            rng = random.Random(pi); vals = [evaluate(model)]
            for g in perm:
                ga_steps(GROUPS[g] * REPS[g], st, opt, rng); vals.append(evaluate(model))
            append("seq", {"si": si, "pi": pi, "perm": perm, "vals": vals})
            print(f"seq s{st} perm {pi} {time.time() - t0:.0f}s", flush=True)

elif args.cmd == "attack":
    done = {r["si"] for r in load("attack")}
    fi_all = forget_items(0)
    for si, st in enumerate(STRENGTHS):
        if si in done: continue
        full_model(); opt = torch.optim.AdamW(model.parameters(), lr=args.unlearn_lr, weight_decay=0.0)
        rng = random.Random(0); ga_steps(fi_all, st, opt, rng)
        sub = random.Random(1).sample(fi_all, max(1, len(fi_all) // 10))        # 10% of the forgotten data
        opt2 = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.0); prev = 0; us = []
        for k in RELEARN:
            ga_steps(sub, k - prev, opt2, rng, sign=+1.0, bs=args.bs); prev = k; us.append(evaluate(model))
        append("attack", {"si": si, "u": us}); print(f"attack s{st} {time.time() - t0:.0f}s", flush=True)

elif args.cmd == "assemble":
    U = np.full((M, n + 1), np.nan); Uh = np.full((len(STRENGTHS), M, n + 1), np.nan)
    for r in load("retrain"): U[r["mask"]] = r["u"]
    for r in load("unlearn"): Uh[:, r["mask"]] = r["u"]
    miss = int(np.isnan(U).any(1).sum()), int(np.isnan(Uh).any(2).any(0).sum())
    assert miss == (0, 0), f"missing coalitions (retrain, unlearn): {miss}"
    nz = load("noise"); masks = sorted({r["mask"] for r in nz})
    noise = np.array([[r["u"] for r in sorted(nz, key=lambda r: r["seed"]) if r["mask"] == m] for m in masks])
    sq = load("seq"); P = 1 + max(r["pi"] for r in sq)
    seq_perms = np.zeros((len(STRENGTHS), P, n), int); seq_vals = np.zeros((len(STRENGTHS), P, n + 1, n + 1))
    for r in sq: seq_perms[r["si"], r["pi"]] = r["perm"]; seq_vals[r["si"], r["pi"]] = r["vals"]
    att = np.zeros((len(STRENGTHS), len(RELEARN), n + 1))
    for r in load("attack"): att[r["si"]] = r["u"]
    np.savez(os.path.join(args.out, "tofu.npz"), U=U, Uh=Uh, strengths=STRENGTHS, reps=np.array(REPS),
             noise_masks=masks, noise=noise, attack=att, seq_perms=seq_perms, seq_vals=seq_vals)
    print("wrote", os.path.join(args.out, "tofu.npz"))
