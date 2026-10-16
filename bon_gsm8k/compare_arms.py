"""Paired comparison of the optimize and control arms from a log.jsonl written by optimize_gsm8k.py.
    python compare_arms.py opt_full
    python compare_arms.py opt_weak --round 6
Differences are optimize minus control, computed per question, with a bootstrap CI over questions."""
import argparse, json, os
import numpy as np

ap = argparse.ArgumentParser(); ap.add_argument("dir"); ap.add_argument("--round", type=int, default=None)
a = ap.parse_args()
log = {}
for line in open(os.path.join(a.dir, "log.jsonl"), encoding="utf-8"):
    r = json.loads(line); log[(r["qid"], r["arm"], r["round"])] = r
R = a.round or max(r for (_, arm, r) in log if arm == "optimize")
qids = sorted({q for (q, arm, r) in log if arm == "optimize" and r == R} & {q for (q, arm, r) in log if arm == "control" and r == R})
rng = np.random.default_rng(0)

def ci(x):
    x = np.asarray(x, float); b = [x[rng.integers(0, len(x), len(x))].mean() for _ in range(5000)]
    return x.mean(), np.percentile(b, 2.5), np.percentile(b, 97.5)

def row(name, vals):
    m, lo, hi = ci(vals); print(f"{name:42s} {m:+.3f}  [{lo:+.3f}, {hi:+.3f}]")

g0 = lambda q: log[(q, "init", 0)]
print(f"{a.dir}: round {R}, {len(qids)} questions (optimize minus control, paired)")
row("accuracy G", [log[(q, "optimize", R)]["G"] - log[(q, "control", R)]["G"] for q in qids])
row("judge score J", [log[(q, "optimize", R)]["J"] - log[(q, "control", R)]["J"] for q in qids])
row("length (chars)", [len(log[(q, "optimize", R)]["text"]) - len(log[(q, "control", R)]["text"]) for q in qids])
bad = lambda q, arm: float(log[(q, arm, R)]["J"] > g0(q)["J"] and log[(q, arm, R)]["G"] < g0(q)["G"])
row("rate J up & G down", [bad(q, "optimize") - bad(q, "control") for q in qids])
print("per-arm G change vs round 0:")
for arm in ("optimize", "control"):
    row("  " + arm, [log[(q, arm, R)]["G"] - g0(q)["G"] for q in qids])
