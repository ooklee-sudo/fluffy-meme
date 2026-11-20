"""Same tasks against a cloud model through OpenRouter (OpenAI-compatible), with cost and PII exposure.

  export OPENROUTER_API_KEY=...
  python -m quant_cost.api_baseline --model qwen/qwen-2.5-72b-instruct --n 100

Prices are read from https://openrouter.ai/api/v1/models (USD per token) unless overridden with
--price-in / --price-out (USD per 1M tokens). Output schema matches bench.py so analyze.py can combine them.
"""
import argparse
import json
import os
import statistics
import time
import urllib.request

from .bench import SYSTEM, pct, wilson
from .tasks import build_tasks

BASE = "https://openrouter.ai/api/v1"


def _req(path, key=None, body=None):
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode() if body else None, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)


def price_of(model):
    for m in _req("/models")["data"]:
        if m["id"] == model:
            p = m["pricing"]
            return float(p["prompt"]) * 1e6, float(p["completion"]) * 1e6
    raise SystemExit(f"model {model!r} not found on OpenRouter; pass --price-in/--price-out")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--label")
    ap.add_argument("--tasks", default="ticket,extract,arith")
    ap.add_argument("--task-file", action="append", default=[])
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--price-in", type=float, help="USD per 1M prompt tokens")
    ap.add_argument("--price-out", type=float, help="USD per 1M completion tokens")
    ap.add_argument("--out-dir", default="results/quant_cost")
    args = ap.parse_args()

    key = os.environ.get("OPENROUTER_API_KEY", "")
    pin, pout = (args.price_in, args.price_out) if args.price_in is not None and args.price_out is not None \
        else price_of(args.model)
    label = args.label or "api_" + args.model.replace("/", "_")
    print(f"[{label}] price in/out = ${pin}/{pout} per 1M tokens")

    res = {"meta": {"label": label, "kind": "api", "model": args.model, "price_in_per_m": pin,
                    "price_out_per_m": pout, "date": time.strftime("%Y-%m-%d %H:%M:%S")},
           "tasks": {}, "records": {}}
    for task in build_tasks([t for t in args.tasks.split(",") if t], args.n, args.seed, args.task_file):
        recs = []
        for it in task["items"]:
            t = time.perf_counter()
            r = _req("/chat/completions", key, {
                "model": args.model, "temperature": 0, "max_tokens": task["max_tokens"],
                "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": it["prompt"]}]})
            dt = time.perf_counter() - t
            out = r["choices"][0]["message"]["content"] or ""
            u = r["usage"]
            s = task["score"](out, it)
            recs.append({"score": s, "correct": s == 1.0, "prompt_tokens": u["prompt_tokens"],
                         "completion_tokens": u["completion_tokens"], "latency_s": dt, "output": out[:300],
                         "cost_usd": (u["prompt_tokens"] * pin + u["completion_tokens"] * pout) / 1e6,
                         "pii_sent": sum(p in it["prompt"] for p in it["pii"])})
        n = len(recs)
        ok = sum(r["correct"] for r in recs)
        lo, hi = wilson(ok, n)
        res["tasks"][task["name"]] = {
            "n": n, "sensitivity": task["sensitivity"], "acc": ok / n, "acc_ci95": [lo, hi],
            "mean_score": statistics.mean(r["score"] for r in recs),
            "mean_prompt_tokens": statistics.mean(r["prompt_tokens"] for r in recs),
            "mean_completion_tokens": statistics.mean(r["completion_tokens"] for r in recs),
            "latency_mean_s": statistics.mean(r["latency_s"] for r in recs),
            "latency_p95_s": pct([r["latency_s"] for r in recs], 0.95),
            "cost_usd_per_req": statistics.mean(r["cost_usd"] for r in recs),
            "pii_entities_sent_per_req": statistics.mean(r["pii_sent"] for r in recs)}
        res["records"][task["name"]] = recs
        s = res["tasks"][task["name"]]
        print(f"  {task['name']:8s} acc={s['acc']:.3f}  lat={s['latency_mean_s']:.2f}s  "
              f"$/1k req={1000*s['cost_usd_per_req']:.3f}  PII/req={s['pii_entities_sent_per_req']:.1f}")

    os.makedirs(args.out_dir, exist_ok=True)
    path = os.path.join(args.out_dir, f"{label}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    print("wrote", path)


if __name__ == "__main__":
    main()
