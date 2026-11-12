"""Phase 1 (H1): does a probe's entanglement entropy predict each tenant's capacity need?

For each tenant:
  1. L_none: held-out response NLL of the base model with no adapter
  2. Probe: a short TT-adapter fine-tune at a fixed bond dimension -> entanglement profile of every dW
  3. Sweep: a full fine-tune at each bond dimension r in --ranks -> held-out NLL L_r
  4. Capacity need = smallest r whose gain (L_none - L_r) reaches --frac of the best gain in the sweep
One JSON per tenant goes to --out; reruns skip finished tenants. Then run: python analyze.py

Usage:
  python phase1.py --tiny                                            # CPU smoke test, no downloads
  python phase1.py --data data/twcs_pairs.jsonl --n-tenants 10       # RTX 5070 Laptop (8 GB) defaults
"""
import argparse
import json
import math
import os
import random
import re
import time

import torch
import torch.nn.functional as F

from data import encode_tenant, features, load_jsonl, synthetic_tenants
from tt import adapter_params, add_tt_adapters, bond_profile, reset_adapters


def get_args():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--model", default="Qwen/Qwen2.5-1.5B")
    a.add_argument("--data", default="data/twcs_pairs.jsonl")
    a.add_argument("--tiny", action="store_true", help="random tiny Llama + synthetic tenants on CPU")
    a.add_argument("--out", default="results/phase1")
    a.add_argument("--n-tenants", type=int, default=10)
    a.add_argument("--tenants", default="", help="comma-separated tenant names (overrides --n-tenants)")
    a.add_argument("--min-examples", type=int, default=400)
    a.add_argument("--n-train", type=int, default=320)
    a.add_argument("--n-eval", type=int, default=80)
    a.add_argument("--max-len", type=int, default=256)
    a.add_argument("--bs", type=int, default=4)
    a.add_argument("--lr", type=float, default=2e-3)
    a.add_argument("--steps", type=int, default=300, help="steps per sweep run")
    a.add_argument("--probe-steps", type=int, default=60)
    a.add_argument("--probe-rank", type=int, default=8)
    a.add_argument("--ranks", default="1,2,4,8,16")
    a.add_argument("--d", type=int, default=4, help="number of TT cores per adapter")
    a.add_argument("--targets", default="q_proj,v_proj")
    a.add_argument("--frac", type=float, default=0.9)
    a.add_argument("--energy", type=float, default=0.99)
    a.add_argument("--seed", type=int, default=0)
    a.add_argument("--dtype", default="bf16", choices=["bf16", "fp32"])
    a.add_argument("--no-ckpt", action="store_true", help="disable gradient checkpointing")
    args = a.parse_args()
    if args.tiny:
        args.n_tenants, args.min_examples, args.n_train, args.n_eval = 4, 0, 96, 32
        args.steps, args.probe_steps, args.bs, args.ranks, args.dtype = 80, 30, 8, "1,2,4,8", "fp32"
        args.lr, args.out = 1e-2, "results/phase1_tiny"
    return args


# ---------------------------------------------------------------- model
def load_model(args, device):
    from transformers import AutoModelForCausalLM, AutoTokenizer, LlamaConfig, LlamaForCausalLM

    if args.tiny:
        torch.manual_seed(0)
        cfg = LlamaConfig(vocab_size=64, hidden_size=64, intermediate_size=128, num_hidden_layers=2,
                          num_attention_heads=4, num_key_value_heads=4, max_position_embeddings=64)
        return LlamaForCausalLM(cfg).to(device), None, 0
    dtype = torch.bfloat16 if args.dtype == "bf16" else torch.float32
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(args.model, dtype=dtype).to(device)
    if not args.no_ckpt:
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.config.use_cache = False
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    return model, tok, pad


def collate(batch, pad, max_len, device):
    seqs = [(p + r)[:max_len] for p, r in batch]
    plen = [min(len(p), max_len) for p, _ in batch]
    n = max(map(len, seqs))
    ids = torch.full((len(seqs), n), pad, dtype=torch.long)
    lab = torch.full_like(ids, -100)
    att = torch.zeros_like(ids)
    for i, s in enumerate(seqs):
        ids[i, : len(s)] = torch.tensor(s)
        att[i, : len(s)] = 1
        lab[i, plen[i]: len(s)] = torch.tensor(s[plen[i]:])
    return ids.to(device), att.to(device), lab.to(device)


def response_nll(model, batch, pad, max_len, device):
    """Summed NLL over response tokens and their count; logits only at response positions (saves memory)."""
    ids, att, lab = collate(batch, pad, max_len, device)
    h = model.model(input_ids=ids, attention_mask=att).last_hidden_state[:, :-1]
    tgt = lab[:, 1:]
    m = tgt != -100
    logits = model.lm_head(h[m]).float()
    return F.cross_entropy(logits, tgt[m], reduction="sum"), int(m.sum())


@torch.no_grad()
def evaluate(model, data, args, pad, device):
    model.eval()
    tot, n = 0.0, 0
    for i in range(0, len(data), args.bs):
        s, k = response_nll(model, data[i: i + args.bs], pad, args.max_len, device)
        tot, n = tot + float(s), n + k
    return tot / max(n, 1)


def train(model, adapters, data, steps, args, pad, device, seed):
    params = adapter_params(adapters)
    opt = torch.optim.AdamW(params, lr=args.lr, weight_decay=0.0)
    warm = max(1, steps // 10)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / warm))
    rng = random.Random(seed)
    model.train()
    for _ in range(steps):
        s, k = response_nll(model, rng.sample(data, min(args.bs, len(data))), pad, args.max_len, device)
        (s / max(k, 1)).backward()
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        opt.step()
        sched.step()
        opt.zero_grad(set_to_none=True)


def probe_summary(profiles, probe_rank):
    bonds = [b for prof in profiles.values() for b in prof]
    norm = [b["entropy"] / math.log(min(probe_rank, b["max_rank"])) for b in bonds if min(probe_rank, b["max_rank"]) > 1]
    return dict(
        mean_entropy=sum(b["entropy"] for b in bonds) / len(bonds),
        max_entropy=max(b["entropy"] for b in bonds),
        mean_norm_entropy=sum(norm) / max(len(norm), 1),
        mean_rank_at_energy=sum(b["rank_at_energy"] for b in bonds) / len(bonds),
    )


def capacity_need(sweep, frac):
    best = max(r["gain"] for r in sweep)
    if best <= 0:
        return None
    return min(r["rank"] for r in sweep if r["gain"] >= frac * best)


# ---------------------------------------------------------------- main
def main():
    args = get_args()
    if not args.tiny and not os.path.exists(args.data):
        raise SystemExit(f"data file not found: {args.data}\n"
                         "Make it first (README step 3): python data.py twcs data/twcs.csv data/twcs_pairs.jsonl 200")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    os.makedirs(args.out, exist_ok=True)
    model, tok, pad = load_model(args, device)
    adapters = add_tt_adapters(model, targets=tuple(args.targets.split(",")), ranks=args.probe_rank, d=args.d)
    print(f"device={device}  adapted modules={len(adapters)}  e.g. {next(iter(adapters))}: "
          f"out={next(iter(adapters.values())).out_f} in={next(iter(adapters.values())).in_f}")

    if args.tiny:
        raw = synthetic_tenants(args.n_tenants, args.n_train + args.n_eval, vocab=64)
    else:
        raw = load_jsonl(args.data)
    if args.tenants:
        names = args.tenants.split(",")
    else:
        names = sorted([t for t, v in raw.items() if len(v) >= args.min_examples], key=lambda t: -len(raw[t]))
        names = sorted(names[: args.n_tenants])
    ranks = [int(r) for r in args.ranks.split(",")]
    print(f"{len(names)} tenants, bond dimensions {ranks}")

    for ti, name in enumerate(names):
        path = os.path.join(args.out, re.sub(r"[^\w.-]", "_", name) + ".json")
        if os.path.exists(path):
            print(f"[{ti + 1}/{len(names)}] {name}: done, skipping")
            continue
        t0 = time.time()
        pairs = list(raw[name])
        random.Random(args.seed).shuffle(pairs)
        enc = pairs if args.tiny else encode_tenant(pairs[: args.n_train + args.n_eval], tok, args.max_len)
        tr, ev = enc[: args.n_train], enc[args.n_train: args.n_train + args.n_eval]

        reset_adapters(adapters, args.probe_rank)  # last core zero -> no update
        nll_none = evaluate(model, ev, args, pad, device)

        torch.manual_seed(args.seed)
        reset_adapters(adapters, args.probe_rank)
        train(model, adapters, tr, args.probe_steps, args, pad, device, args.seed)
        profiles = {k: bond_profile(ad.delta(), ad.out_f, ad.in_f, args.energy) for k, ad in adapters.items()}
        probe = dict(rank=args.probe_rank, steps=args.probe_steps, nll=evaluate(model, ev, args, pad, device),
                     summary=probe_summary(profiles, args.probe_rank), modules=profiles)

        sweep = []
        for r in ranks:
            torch.manual_seed(args.seed)
            reset_adapters(adapters, r)
            ts = time.time()
            train(model, adapters, tr, args.steps, args, pad, device, args.seed)
            nll = evaluate(model, ev, args, pad, device)
            sweep.append(dict(rank=r, nll=nll, gain=nll_none - nll, seconds=time.time() - ts,
                              trainable_params=sum(ad.n_params() for ad in adapters.values())))
            print(f"    r={r:<3d} nll={nll:.4f} gain={nll_none - nll:+.4f}")

        res = dict(tenant=name, n_train=len(tr), n_eval=len(ev), features=features(tr), nll_none=nll_none,
                   probe=probe, sweep=sweep, capacity_need=capacity_need(sweep, args.frac),
                   seconds=time.time() - t0, config=vars(args))
        with open(path, "w") as f:
            json.dump(res, f, indent=1)
        s = probe["summary"]
        print(f"[{ti + 1}/{len(names)}] {name}: none={nll_none:.4f} probe norm-entropy={s['mean_norm_entropy']:.3f} "
              f"need={res['capacity_need']}  ({res['seconds'] / 60:.1f} min)")


if __name__ == "__main__":
    main()
