"""Phase 2 (H2): at an equal per-tenant parameter budget, do tensor-train adapters give a different
personalization gain than LoRA (and VeRA)?

For each tenant (same data split as Phase 1: 320 train, 40 dev, 80 eval, data seed 0):
  1. NLL of the base model on eval and dev
  2. For each adapter config (method:size), train on train with early stopping on dev, then score eval.
     Gain = NLL without adapter - NLL with adapter; relative gain = gain / NLL without adapter.
One JSON per tenant goes to --out; reruns skip finished tenants.

Two modes:
  --tune   learning-rate search on tuning tenants: mid-size config per method x --tune-lrs; the choice rule is
           the lr with the highest mean dev relative gain per method (python analyze_tune.py)
  default  the comparison sweep with one fixed lr per method (--lrs)

Usage:
  python phase2.py --tiny                                                            # CPU smoke test
  python phase2.py --tune --tenants-from results/phase1 --out results/phase2_tune
  python phase2.py --exclude-dir results/phase1,results/phase1_confirm,results/phase1_value --n-tenants 31 \\
                   --lrs tt=1e-3,lora=1e-3,vera=3e-3 --seed 0 --out results/phase2_s0
"""
import argparse
import json
import math
import os
import random
import re
import time

import torch

from adapters import add_slots, get_state, n_trainable, parse_config, set_method, set_state
from data import encode_tenant, features, load_jsonl, synthetic_tenants
from phase1 import evaluate, load_model, response_nll

MAIN_CONFIGS = "tt:1,tt:2,tt:5,tt:10,tt:15,lora:1,lora:4,lora:8,vera:256,vera:1024"
TUNE_CONFIGS = "tt:10,lora:4,vera:1024"


def get_args():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--model", default="Qwen/Qwen2.5-1.5B")
    a.add_argument("--data", default="data/twcs_pairs.jsonl")
    a.add_argument("--tiny", action="store_true")
    a.add_argument("--out", default=None)
    a.add_argument("--tune", action="store_true")
    a.add_argument("--configs", default=None, help=f"default: {MAIN_CONFIGS} (tune: {TUNE_CONFIGS})")
    a.add_argument("--lrs", default="tt=1e-3,lora=1e-3,vera=1e-3", help="one lr per method (main mode)")
    a.add_argument("--tune-lrs", default="tt=3e-4/1e-3/3e-3,lora=3e-4/1e-3/3e-3,vera=1e-3/3e-3/1e-2/3e-2",
                   help="learning-rate grid per method for --tune (VeRA trains only scaling vectors and needs larger lrs)")
    a.add_argument("--tenants", default="")
    a.add_argument("--tenants-from", default="", help="use the tenants that have results in this folder")
    a.add_argument("--exclude-dir", default="")
    a.add_argument("--n-tenants", type=int, default=31)
    a.add_argument("--min-examples", type=int, default=440)
    a.add_argument("--n-train", type=int, default=320)
    a.add_argument("--n-dev", type=int, default=40)
    a.add_argument("--n-eval", type=int, default=80)
    a.add_argument("--max-len", type=int, default=256)
    a.add_argument("--bs", type=int, default=4)
    a.add_argument("--steps", type=int, default=300)
    a.add_argument("--eval-every", type=int, default=50)
    a.add_argument("--data-seed", type=int, default=0)
    a.add_argument("--seed", type=int, default=0, help="training seed")
    a.add_argument("--d", type=int, default=4)
    a.add_argument("--targets", default="q_proj,v_proj")
    a.add_argument("--dtype", default="bf16", choices=["bf16", "fp32"])
    a.add_argument("--no-ckpt", action="store_true")
    a.add_argument("--list-only", action="store_true")
    args = a.parse_args()
    if args.configs is None:
        args.configs = TUNE_CONFIGS if args.tune else MAIN_CONFIGS
    if args.tiny:
        args.min_examples, args.n_train, args.n_dev, args.n_eval = 0, 96, 32, 32
        args.steps, args.bs, args.dtype, args.eval_every = 60, 8, "fp32", 20
        if args.configs == MAIN_CONFIGS:
            args.configs = "tt:1,tt:2,lora:1,lora:2,vera:16"
        if args.configs == TUNE_CONFIGS:
            args.configs = "tt:2,lora:1,vera:16"
        args.tune_lrs = "tt=3e-3/1e-2,lora=3e-3/1e-2,vera=1e-2/3e-2"
        args.lrs = "tt=1e-2,lora=1e-2,vera=1e-2"
    if args.out is None:
        args.out = "results/phase2_tiny" if args.tiny else ("results/phase2_tune" if args.tune else f"results/phase2_s{args.seed}")
    return args


def train(model, slots, params, data, dev, lr, args, pad, device, seed):
    """AdamW, warmup + cosine decay, early stopping on dev (step 0 = no update included); restores the best."""
    opt = torch.optim.AdamW(params, lr=lr, weight_decay=0.0)
    steps = args.steps
    warm = max(1, steps // 10)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt, lambda s: min(1.0, (s + 1) / warm) * 0.5 * (1 + math.cos(math.pi * min(s, steps) / steps)))
    rng = random.Random(seed)
    best = (evaluate(model, dev, args, pad, device), 0, get_state(slots))
    model.train()
    for step in range(1, steps + 1):
        s, k = response_nll(model, rng.sample(data, min(args.bs, len(data))), pad, args.max_len, device)
        (s / max(k, 1)).backward()
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        opt.step()
        sched.step()
        opt.zero_grad(set_to_none=True)
        if step % args.eval_every == 0 or step == steps:
            v = evaluate(model, dev, args, pad, device)
            if v < best[0]:
                best = (v, step, get_state(slots))
            model.train()
    set_state(slots, best[2])
    return best[0], best[1]


def select_tenants(args, raw):
    if args.tenants:
        return args.tenants.split(",")
    if args.tenants_from:
        names = []
        for f in sorted(os.listdir(args.tenants_from)):
            if f.endswith(".json"):
                with open(os.path.join(args.tenants_from, f)) as fh:
                    names.append(json.load(fh)["tenant"])
        return names
    excl = set()
    for d in filter(None, args.exclude_dir.split(",")):
        if not os.path.isdir(d):
            raise SystemExit(f"--exclude-dir: folder not found: {d}")
        for f in os.listdir(d):
            if f.endswith(".json"):
                with open(os.path.join(d, f)) as fh:
                    excl.add(json.load(fh)["tenant"])
    names = sorted([t for t, v in raw.items() if len(v) >= args.min_examples and t not in excl],
                   key=lambda t: -len(raw[t]))
    k = min(args.n_tenants, len(names))
    if k > 1:
        names = [names[round(i * (len(names) - 1) / (k - 1))] for i in range(k)]
    return sorted(set(names[:k] if k <= 1 else names))


def main():
    args = get_args()
    if not args.tiny and not os.path.exists(args.data):
        raise SystemExit(f"data file not found: {args.data}")
    raw = synthetic_tenants(8, args.n_train + args.n_dev + args.n_eval, vocab=64) if args.tiny else load_jsonl(args.data)
    names = select_tenants(args, raw)
    configs = [parse_config(c) for c in args.configs.split(",")]
    lrs = {m: float(v) for m, v in (x.split("=") for x in args.lrs.split(","))}
    grid = {m: [float(v) for v in vs.split("/")] for m, vs in (x.split("=") for x in args.tune_lrs.split(","))} \
        if args.tune else None
    print(f"{len(names)} tenants: {', '.join(names)}")
    print(f"configs {args.configs}; " + (f"tuning lrs {grid}" if args.tune else f"lrs {lrs}") + f"; seed {args.seed}")
    if args.list_only:
        return
    if not args.tune:
        missing = {m for m, _ in configs} - set(lrs)
        if missing:
            raise SystemExit(f"--lrs has no lr for {missing}")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    os.makedirs(args.out, exist_ok=True)
    model, tok, pad = load_model(args, device)
    slots = add_slots(model, targets=tuple(args.targets.split(",")), d=args.d)
    print(f"device={device}  adapted modules={len(slots)}")

    for ti, name in enumerate(names):
        path = os.path.join(args.out, re.sub(r"[^\w.-]", "_", name) + ".json")
        if os.path.exists(path):
            print(f"[{ti + 1}/{len(names)}] {name}: done, skipping")
            continue
        t0 = time.time()
        pairs = list(raw[name])
        random.Random(args.data_seed).shuffle(pairs)
        n_all = args.n_train + args.n_dev + args.n_eval
        enc = pairs[:n_all] if args.tiny else encode_tenant(pairs[:n_all], tok, args.max_len)
        tr, dv = enc[: args.n_train], enc[args.n_train: args.n_train + args.n_dev]
        ev = enc[args.n_train + args.n_dev: n_all]

        set_method(slots, "none", 0)
        nll_none, dev_none = evaluate(model, ev, args, pad, device), evaluate(model, dv, args, pad, device)
        runs = []
        for method, r in configs:
            for lr in (grid[method] if args.tune else [lrs[method]]):
                params = set_method(slots, method, r, seed=args.seed)
                ts = time.time()
                dev_best, best_step = train(model, slots, params, tr, dv, lr, args, pad, device, args.seed)
                nll = evaluate(model, ev, args, pad, device)
                n = n_trainable(slots)
                runs.append(dict(config=f"{method}:{r}", method=method, r=r, lr=lr, params=n, bytes_fp16=2 * n,
                                 nll=nll, gain=nll_none - nll, rel_gain=(nll_none - nll) / nll_none,
                                 dev_best=dev_best, dev_rel_gain=(dev_none - dev_best) / dev_none,
                                 best_step=best_step, seconds=time.time() - ts))
                print(f"    {method}:{r:<5} lr={lr:.0e} params={n:>9,} rel gain={runs[-1]['rel_gain']:+.4f} "
                      f"dev rel={runs[-1]['dev_rel_gain']:+.4f} best step {best_step}/{args.steps}")
        set_method(slots, "none", 0)
        res = dict(tenant=name, n_train=len(tr), n_dev=len(dv), n_eval=len(ev), features=features(tr),
                   nll_none=nll_none, dev_none=dev_none, runs=runs, seed=args.seed, tune=args.tune,
                   seconds=time.time() - t0, config=vars(args))
        with open(path, "w") as f:
            json.dump(res, f, indent=1)
        print(f"[{ti + 1}/{len(names)}] {name}: none={nll_none:.4f}  ({res['seconds'] / 60:.1f} min)")


if __name__ == "__main__":
    main()
