"""Economics study, experiment E1: in-context personalization baselines, scored on exactly the same
evaluation tokens as the adapters of Phase 2.

For each tenant (same split as Phase 2: data seed 0, 320 train, 40 dev, 80 eval) and each method:
  zero        no personalization (must equal Phase 2's nll_none; checked when Phase 2 results exist)
  fewshot-k   k random examples from the tenant's own training pairs placed before the question
  rag-k       the k training pairs whose customer text is most similar to the question (TF-IDF cosine)
The response tokens and their truncation are identical to the adapter evaluation, so NLL and relative
gain are directly comparable. Context tokens per request are recorded: they drive inference cost.

Usage:
  python baselines.py --tenants-from results/phase2_s0 --out results/econ_e1
  python baselines.py --tiny                                  # CPU smoke test
"""
import argparse
import json
import math
import os
import random
import re
import time
from collections import Counter

import torch

from data import PROMPT_TEMPLATE, load_jsonl
from phase1 import evaluate

WORD = re.compile(r"[a-z0-9']+")


def tfidf_index(texts):
    docs = [Counter(WORD.findall(t.lower())) for t in texts]
    df = Counter(w for d in docs for w in d)
    n = len(docs)
    idf = {w: math.log((1 + n) / (1 + c)) + 1 for w, c in df.items()}
    vecs = []
    for d in docs:
        v = {w: c * idf[w] for w, c in d.items()}
        norm = math.sqrt(sum(x * x for x in v.values())) or 1.0
        vecs.append({w: x / norm for w, x in v.items()})
    return idf, vecs


def top_k(query, idf, vecs, k):
    q = Counter(WORD.findall(query.lower()))
    qv = {w: c * idf.get(w, 0.0) for w, c in q.items()}
    norm = math.sqrt(sum(x * x for x in qv.values())) or 1.0
    scores = [sum(qv[w] / norm * v.get(w, 0.0) for w in qv) for v in vecs]
    return sorted(range(len(vecs)), key=lambda i: -scores[i])[:k]


def get_args():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--model", default="Qwen/Qwen2.5-1.5B")
    a.add_argument("--data", default="data/twcs_pairs.jsonl")
    a.add_argument("--tenants-from", default="results/phase2_s0")
    a.add_argument("--tenants", default="")
    a.add_argument("--methods", default="zero,fewshot-4,fewshot-8,rag-4,rag-8")
    a.add_argument("--n-train", type=int, default=320)
    a.add_argument("--n-dev", type=int, default=40)
    a.add_argument("--n-eval", type=int, default=80)
    a.add_argument("--max-len", type=int, default=256, help="same as Phase 2: query + response budget")
    a.add_argument("--demo-len", type=int, default=96, help="max tokens per in-context example")
    a.add_argument("--bs", type=int, default=4)
    a.add_argument("--data-seed", type=int, default=0)
    a.add_argument("--dtype", default="bf16", choices=["bf16", "fp32"])
    a.add_argument("--tiny", action="store_true")
    a.add_argument("--out", default="results/econ_e1")
    return a.parse_args()


def main():
    args = get_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    from transformers import AutoModelForCausalLM, AutoTokenizer, LlamaConfig, LlamaForCausalLM

    tok = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-1.5B" if args.tiny else args.model)
    if args.tiny:
        torch.manual_seed(0)
        model = LlamaForCausalLM(LlamaConfig(vocab_size=len(tok), hidden_size=64, intermediate_size=128,
                                             num_hidden_layers=2, num_attention_heads=4, num_key_value_heads=4,
                                             max_position_embeddings=2048)).to(device)
        args.dtype = "fp32"
    else:
        model = AutoModelForCausalLM.from_pretrained(
            args.model, dtype=torch.bfloat16 if args.dtype == "bf16" else torch.float32).to(device)
    model.eval()
    pad = tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id

    raw = load_jsonl(args.data)
    if args.tenants:
        names = args.tenants.split(",")
    else:
        names = sorted(json.load(open(os.path.join(args.tenants_from, f)))["tenant"]
                       for f in os.listdir(args.tenants_from) if f.endswith(".json"))
    methods = args.methods.split(",")
    os.makedirs(args.out, exist_ok=True)
    print(f"{len(names)} tenants, methods {methods}, device {device}")

    for ti, name in enumerate(names):
        path = os.path.join(args.out, re.sub(r"[^\w.-]", "_", name) + ".json")
        if os.path.exists(path):
            print(f"[{ti + 1}/{len(names)}] {name}: done, skipping")
            continue
        t0 = time.time()
        pairs = list(raw[name])
        random.Random(args.data_seed).shuffle(pairs)
        n_all = args.n_train + args.n_dev + args.n_eval
        tr = pairs[: args.n_train]
        ev = pairs[args.n_train + args.n_dev: n_all]
        idf, vecs = tfidf_index([p for p, _ in tr])
        demo_ids = [tok(f"Customer: {p}\nAgent: {r}\n\n", add_special_tokens=False)["input_ids"][: args.demo_len]
                    for p, r in tr]
        res = dict(tenant=name, n_train=len(tr), n_eval=len(ev), methods={})
        for m in methods:
            kind, k = (m.split("-") + ["0"])[:2]
            k = int(k)
            rng = random.Random(1000 + ti)
            data, ctx = [], []
            for j, (p, r) in enumerate(ev):
                qi = tok(PROMPT_TEMPLATE.format(prompt=p), add_special_tokens=True)["input_ids"][: args.max_len // 2]
                ri = tok(" " + r + tok.eos_token, add_special_tokens=False)["input_ids"][: args.max_len - len(qi)]
                if kind == "zero":
                    sel = []
                elif kind == "fewshot":
                    sel = rng.sample(range(len(tr)), k)
                elif kind == "rag":
                    sel = top_k(p, idf, vecs, k)[::-1]  # most similar example last, next to the question
                else:
                    raise SystemExit(f"unknown method {m}")
                demos = [t for i in sel for t in demo_ids[i]]
                data.append((demos + qi, ri))
                ctx.append(len(demos) + len(qi))
            ev_args = argparse.Namespace(bs=args.bs, max_len=args.demo_len * max(k, 1) + args.max_len)
            nll = evaluate(model, data, ev_args, pad, device)
            res["methods"][m] = dict(nll=nll, context_tokens=sum(ctx) / len(ctx))
        z = res["methods"].get("zero", {}).get("nll")
        for m, v in res["methods"].items():
            v["rel_gain"] = (z - v["nll"]) / z if z else None
        ref = os.path.join(args.tenants_from, re.sub(r"[^\w.-]", "_", name) + ".json")
        if z is not None and os.path.exists(ref):
            res["phase2_nll_none"] = json.load(open(ref))["nll_none"]
        res["seconds"] = time.time() - t0
        with open(path, "w") as f:
            json.dump(res, f, indent=1)
        line = "  ".join(f"{m} {v['rel_gain']:+.3f} ({v['context_tokens']:.0f} tok)" for m, v in res["methods"].items())
        chk = f"  [zero vs Phase 2 nll_none: {z:.4f} vs {res['phase2_nll_none']:.4f}]" if "phase2_nll_none" in res else ""
        print(f"[{ti + 1}/{len(names)}] {name}: {line}{chk}  ({res['seconds'] / 60:.1f} min)")


if __name__ == "__main__":
    main()
