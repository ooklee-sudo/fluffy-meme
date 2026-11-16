"""Economics study, E4: how fast does a brand adapter's benefit decay as the brand's traffic changes, and
how does that compare with retrieval (RAG), whose index can be refreshed at almost no cost?

Weeks are counted from 2017-10-01 (week 0). For each brand:
  - train a LoRA r=1 adapter on pairs from weeks 0-1 (stale adapter); dev = held-out pairs from weeks 0-1
  - for each later week w: relative gain over no personalization of
      stale adapter | RAG-8 with a stale index (weeks 0-1) | RAG-8 with a fresh index (week w-1)
  - in the last evaluated week: a fresh adapter trained on weeks w-2..w-1, to measure what retraining
    recovers (recovery R = stale gain / fresh gain, the R of the real-options model)
Scores use the same prompt and response tokens as Phase 2 / E1. One JSON per brand goes to --out.

Usage:
  python drift.py --list-only
  python drift.py --n-brands 30 --out results/econ_e4
"""
import argparse
import json
import os
import random
import re
import time
from datetime import datetime, timezone

import torch

from adapters import add_slots, set_method
from baselines import tfidf_index, top_k
from data import PROMPT_TEMPLATE, encode_tenant, load_jsonl_time
from phase1 import evaluate
from phase2 import train

START = datetime(2017, 10, 1, tzinfo=timezone.utc)


def week(t):
    return int((datetime.fromisoformat(t) - START).days // 7)


def get_args():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--model", default="Qwen/Qwen2.5-1.5B")
    a.add_argument("--data", default="data/twcs_pairs_time.jsonl")
    a.add_argument("--n-brands", type=int, default=30)
    a.add_argument("--tenants", default="")
    a.add_argument("--first-eval-week", type=int, default=2)
    a.add_argument("--last-eval-week", type=int, default=8)
    a.add_argument("--n-train", type=int, default=320)
    a.add_argument("--n-dev", type=int, default=40)
    a.add_argument("--n-eval", type=int, default=80)
    a.add_argument("--k", type=int, default=8)
    a.add_argument("--lr", type=float, default=3e-3)
    a.add_argument("--steps", type=int, default=300)
    a.add_argument("--eval-every", type=int, default=50)
    a.add_argument("--bs", type=int, default=4)
    a.add_argument("--max-len", type=int, default=256)
    a.add_argument("--demo-len", type=int, default=96)
    a.add_argument("--seed", type=int, default=0)
    a.add_argument("--tiny", action="store_true")
    a.add_argument("--list-only", action="store_true")
    a.add_argument("--out", default="results/econ_e4")
    return a.parse_args()


def eligible(raw, args):
    """Brands with enough pairs in weeks 0-1 for train + dev + in-period eval, and in every eval week."""
    need0 = args.n_train + args.n_dev + args.n_eval
    out = []
    for t, rows in raw.items():
        by = {}
        for p, r, ts in rows:
            by.setdefault(week(ts), []).append((p, r))
        n01 = len(by.get(0, [])) + len(by.get(1, []))
        weeks = range(args.first_eval_week, args.last_eval_week + 1)
        if n01 >= need0 and all(len(by.get(w, [])) >= max(args.n_eval, args.n_train // 2) for w in weeks):
            out.append((t, by))
    return out


def rag_data(ev, index_pairs, tok, args):
    idf, vecs = tfidf_index([p for p, _ in index_pairs])
    demo_ids = [tok(f"Customer: {p}\nAgent: {r}\n\n", add_special_tokens=False)["input_ids"][: args.demo_len]
                for p, r in index_pairs]
    data = []
    for p, r in ev:
        qi = tok(PROMPT_TEMPLATE.format(prompt=p), add_special_tokens=True)["input_ids"][: args.max_len // 2]
        ri = tok(" " + r + tok.eos_token, add_special_tokens=False)["input_ids"][: args.max_len - len(qi)]
        sel = top_k(p, idf, vecs, args.k)[::-1]
        data.append(([x for i in sel for x in demo_ids[i]] + qi, ri))
    return data


def main():
    args = get_args()
    raw = load_jsonl_time(args.data)
    cands = sorted(eligible(raw, args), key=lambda x: -len(raw[x[0]]))
    if args.tenants:
        keep = set(args.tenants.split(","))
        cands = [c for c in cands if c[0] in keep]
    elif len(cands) > args.n_brands:
        cands = [cands[round(i * (len(cands) - 1) / (args.n_brands - 1))] for i in range(args.n_brands)]
    print(f"{len(cands)} brands (eligible: {len(eligible(raw, args))}): {', '.join(sorted(c[0] for c in cands))}")
    print(f"train weeks 0-1, eval weeks {args.first_eval_week}-{args.last_eval_week}, LoRA r=1 lr {args.lr}")
    if args.list_only:
        return

    device = "cuda" if torch.cuda.is_available() else "cpu"
    from transformers import AutoModelForCausalLM, AutoTokenizer, LlamaConfig, LlamaForCausalLM

    tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B" if args.tiny else args.model)
    if args.tiny:
        torch.manual_seed(0)
        model = LlamaForCausalLM(LlamaConfig(vocab_size=len(tok), hidden_size=64, intermediate_size=128,
                                             num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=4,
                                             max_position_embeddings=2048)).to(device)
    else:
        model = AutoModelForCausalLM.from_pretrained(args.model, dtype=torch.bfloat16).to(device)
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.config.use_cache = False
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id
    slots = add_slots(model, targets=("q_proj", "v_proj"))
    ctx_args = argparse.Namespace(bs=args.bs, max_len=args.demo_len * args.k + args.max_len)
    os.makedirs(args.out, exist_ok=True)

    def fit(pairs, dev_pairs):
        params = set_method(slots, "lora", 1, seed=args.seed)
        train(model, slots, params, encode_tenant(pairs, tok, args.max_len), encode_tenant(dev_pairs, tok, args.max_len),
              args.lr, args, pad, device, args.seed)

    for bi, (name, by) in enumerate(cands):
        path = os.path.join(args.out, re.sub(r"[^\w.-]", "_", name) + ".json")
        if os.path.exists(path):
            print(f"[{bi + 1}/{len(cands)}] {name}: done, skipping")
            continue
        t0 = time.time()
        rng = random.Random(args.seed)
        p01 = by.get(0, []) + by.get(1, [])
        rng.shuffle(p01)
        tr, dv = p01[: args.n_train], p01[args.n_train: args.n_train + args.n_dev]
        ev01 = p01[args.n_train + args.n_dev: args.n_train + args.n_dev + args.n_eval]
        evs = {"in-period": ev01}
        for w in range(args.first_eval_week, args.last_eval_week + 1):
            evs[w] = rng.sample(by[w], args.n_eval)

        res = dict(brand=name, weeks={}, n_train=len(tr))
        fit(tr, dv)  # stale adapter
        stale = {}
        for w, ev in evs.items():
            stale[w] = evaluate(model, encode_tenant(ev, tok, args.max_len), args, pad, device)
        set_method(slots, "none", 0)
        model.eval()
        for w, ev in evs.items():
            zero = evaluate(model, encode_tenant(ev, tok, args.max_len), args, pad, device)
            rag_stale = evaluate(model, rag_data(ev, tr, tok, args), ctx_args, pad, device)
            row = dict(zero=zero, lora_stale=stale[w], rag_stale=rag_stale)
            if w != "in-period" and isinstance(w, int):
                prev = [x for x in by.get(w - 1, []) if x not in ev][: args.n_train]
                row["rag_fresh"] = evaluate(model, rag_data(ev, prev, tok, args), ctx_args, pad, device)
            res["weeks"][str(w)] = row
        last = args.last_eval_week
        recent = [x for x in by.get(last - 2, []) + by.get(last - 1, []) if x not in evs[last]]
        rng.shuffle(recent)
        fit(recent[: args.n_train], recent[args.n_train: args.n_train + args.n_dev])
        res["weeks"][str(last)]["lora_fresh"] = evaluate(model, encode_tenant(evs[last], tok, args.max_len), args, pad, device)
        set_method(slots, "none", 0)
        for row in res["weeks"].values():
            for k_ in [x for x in row if x != "zero"]:
                row[k_ + "_rel"] = (row["zero"] - row[k_]) / row["zero"]
        res["seconds"] = time.time() - t0
        with open(path, "w") as f:
            json.dump(res, f, indent=1)
        L = res["weeks"]
        print(f"[{bi + 1}/{len(cands)}] {name}: LoRA stale rel gain in-period {L['in-period']['lora_stale_rel']:+.3f} -> "
              f"week {last} {L[str(last)]['lora_stale_rel']:+.3f} (fresh {L[str(last)]['lora_fresh_rel']:+.3f}); "
              f"RAG fresh week {last} {L[str(last)]['rag_fresh_rel']:+.3f}  ({res['seconds'] / 60:.1f} min)")


if __name__ == "__main__":
    main()
