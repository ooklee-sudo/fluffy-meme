"""Add a normalized 'output_clean' to every rewrite and report how often each model needed cleaning.

    python normalize_rewrites.py rewrites.jsonl rewrites_clean.jsonl
Raw outputs are kept in 'output'. Use 'output_clean' for the detector.
"""
import collections, json, sys
from textnorm import normalize

src, dst = sys.argv[1], sys.argv[2]
changed, total, shrink = collections.Counter(), collections.Counter(), collections.Counter()
with open(dst, "w") as f:
    for line in open(src):
        r = json.loads(line)
        raw = " ".join((r.get("output") or "").split())
        r["output_clean"] = normalize(r.get("output"))
        key = (r["model"], r["prompt_type"])
        total[key] += 1
        changed[key] += raw != r["output_clean"]
        shrink[key] += 1 - len(r["output_clean"]) / max(1, len(raw))
        f.write(json.dumps(r) + "\n")
print(f"{'model':34s} {'prompt':8s} {'n':>5s} {'% changed':>9s} {'% text removed':>14s}")
for k in sorted(total):
    n = total[k]
    print(f"{k[0]:34s} {k[1]:8s} {n:5d} {100*changed[k]/n:9.1f} {100*shrink[k]/n:14.1f}")
