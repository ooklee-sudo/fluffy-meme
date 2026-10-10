"""Summaries for the positive/negative-control experiment: means, oracle gap, seed-matched paired differences."""
import collections
import json
import sys

import numpy as np

rows = [json.loads(l) for l in open("semantic_hawkes/runs/positive_control.jsonl")]
GEN = ["free", "qwen", "qwencentered", "hash", "qwenperm", "random", "learned"]
SIM = ["ridge", "sim_qwen", "sim_hash", "sim_perm", "sim_random"]
cell = collections.defaultdict(dict)
for r in rows:
    cell[(r["scenario"], r["K"], r["n_train"])][(r["variant"], r["seed"])] = r


def boot_ci(d, B=4000, seed=0):
    rng = np.random.default_rng(seed)
    m = [rng.choice(d, len(d)).mean() for _ in range(B)]
    return np.percentile(m, [2.5, 97.5])


def pair(c, a, b, seeds):
    d = np.array([c[(a, s)]["test_ll"] - c[(b, s)]["test_ll"] for s in seeds])
    lo, hi = boot_ci(d)
    return d.mean(), lo, hi, int((d > 0).sum()), len(d)


want = sys.argv[1:] or sorted({k[:2] for k in cell})
for (sc, K, n), c in sorted(cell.items()):
    if want and f"{sc}:{K}" not in [w for w in want] and want != sorted({k[:2] for k in cell}):
        pass
    seeds = sorted({s for (_, s) in c if all((v, s) in c for v in GEN + SIM)})
    if len(seeds) < 2:
        continue
    orc = np.mean([c[("free", s)]["oracle_ll"] for s in seeds])
    print(f"== {sc}  K={K}  n={n}  seeds={len(seeds)}  oracle={orc:.4f}")
    print("   gen: " + "  ".join(f"{v}={np.mean([c[(v, s)]['test_ll'] for s in seeds]):.4f}" for v in GEN))
    print("   sim: " + "  ".join(f"{v}={np.mean([c[(v, s)]['test_ll'] for s in seeds]):.4f}" for v in SIM))
    out = []
    for a, b in [("qwen", "qwenperm"), ("qwen", "random"), ("qwencentered", "random"), ("qwencentered", "qwenperm"), ("qwen", "free"), ("qwencentered", "free"),
                 ("sim_qwen", "sim_perm"), ("sim_qwen", "sim_random"), ("sim_qwen", "ridge"), ("random", "free")]:
        m, lo, hi, k, N = pair(c, a, b, seeds)
        out.append(f"{a}-{b}={m:+.4f}[{lo:+.3f},{hi:+.3f}]({k}/{N})")
    print("   paired:", "  ".join(out[:4]))
    print("          ", "  ".join(out[4:7]))
    print("          ", "  ".join(out[7:]))
