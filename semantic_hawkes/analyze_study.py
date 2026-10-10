"""Summaries for the controlled type-text study: per-dataset means, seed-matched paired differences, tie diagnostics."""
import collections
import json
import sys

import numpy as np

rows = [json.loads(l) for l in open("semantic_hawkes/runs/type_text_study.jsonl")]
V = ["free", "qwen", "hash", "qwenperm", "random", "learned"]
key = sys.argv[1] if len(sys.argv) > 1 else "test_ll"
by = collections.defaultdict(dict)
for r in rows:
    by[(r["data"], r["n_train"])][(r["variant"], r["seed"])] = r
print(f"metric: {key}  (higher is better; seed-matched; mean over seeds)\n")
for (d, n), cell in sorted(by.items(), key=lambda x: (x[0][0], x[0][1])):
    seeds = sorted({s for (_, s) in cell})
    full = [s for s in seeds if all((v, s) in cell for v in V)]
    if not full:
        continue
    tie = np.mean([cell[("free", s)]["tie_frac"] for s in full])
    print(f"== {d}  n_train={'full' if n == 0 else n}  seeds={full}  tied-event share={tie:.3f}")
    line = []
    for v in V:
        x = [cell[(v, s)][key] for s in full]
        line.append(f"{v}={np.mean(x):.4f}" + (f"±{np.std(x, ddof=1):.4f}" if len(x) > 1 else ""))
    print("   ", "  ".join(line))
    pd = {}
    for a, b in [("qwen", "free"), ("qwen", "qwenperm"), ("qwen", "random"), ("qwen", "learned"), ("qwen", "hash"), ("learned", "free")]:
        d_ = [cell[(a, s)][key] - cell[(b, s)][key] for s in full]
        pd[f"{a}-{b}"] = (np.mean(d_), sum(x > 0 for x in d_), len(d_))
    print("    paired:", "  ".join(f"{k}={m:+.4f}({w}/{t} +)" for k, (m, w, t) in pd.items()))
