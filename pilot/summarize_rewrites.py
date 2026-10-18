"""Per-model summary of a rewrite run, with a cost projection for a larger run.

    python summarize_rewrites.py test.jsonl --plan-cheap 500 --plan-top 200
"""
import argparse, collections, json

TOP = {"openai/gpt-6.1-sol", "anthropic/claude-opus-5.5"}
PROMPTS = 3

ap = argparse.ArgumentParser()
ap.add_argument("path")
ap.add_argument("--plan-cheap", type=int, default=500, help="chunks per prompt per cheap model")
ap.add_argument("--plan-top", type=int, default=200, help="chunks per prompt per top model")
a = ap.parse_args()

rows = [json.loads(l) for l in open(a.path)]
by = collections.defaultdict(list)
for r in rows:
    by[r["model"]].append(r)

print(f"{'model':34s} {'calls':>5s} {'empty':>5s} {'$/call':>8s} {'words':>6s} {'out_tok':>7s} {'reason_tok':>10s} {'projected $':>11s}")
total = 0.0
for m, rs in sorted(by.items()):
    n = len(rs)
    empty = sum(not (r.get("output") or "").strip() for r in rs)
    cost = sum(r["cost_usd"] for r in rs) / n
    words = sum(len((r.get("output") or "").split()) for r in rs) // n
    out_tok = sum(r["usage"].get("completion_tokens", 0) for r in rs) // n
    reason = sum((r["usage"].get("completion_tokens_details") or {}).get("reasoning_tokens", 0) for r in rs) // n
    planned = PROMPTS * (a.plan_top if m in TOP else a.plan_cheap)
    proj = cost * planned
    total += proj
    print(f"{m:34s} {n:5d} {empty:5d} {cost:8.4f} {words:6d} {out_tok:7d} {reason:10d} {proj:11.2f}")
print(f"\nprojected total for plan ({a.plan_cheap}/{a.plan_top} per prompt): ${total:.2f}")
print("(small samples: 3 calls per top model, so top-model projections are rough; add ~30% margin)")
