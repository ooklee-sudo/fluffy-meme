"""Aggregate results/seeds*/<pair>_s<k>.json into mean, SD and 95% t-intervals for R_C, R_A (and C_A/C_N).

  python aggregate_seeds.py results/seeds_gpu
"""
import glob
import json
import os
import re
import sys
from collections import defaultdict

import numpy as np
from scipy import stats

d = sys.argv[1] if len(sys.argv) > 1 else "results/seeds_gpu"
by = defaultdict(list)
for f in sorted(glob.glob(os.path.join(d, "*_s*.json"))):
    r = json.load(open(f))
    rec = r["recovery"][0]
    by[r["pair"]].append((int(re.search(r"_s(\d+)\.json$", f).group(1)), rec["R_C"], rec["R_A"], r["C_A_over_C_N"]))
out = {}
print(f"{'pair':<22}{'n':>3} {'R_C mean [95% CI]':>26} {'R_A mean [95% CI]':>26} {'R_A-R_C>0':>10} {'C_A/C_N':>8}")
for pair, v in by.items():
    a = np.array([x[1:] for x in v])
    n = len(a)
    t = stats.t.ppf(0.975, n - 1)
    ci = lambda x: (x.mean(), x.mean() - t * x.std(ddof=1) / np.sqrt(n), x.mean() + t * x.std(ddof=1) / np.sqrt(n), x.std(ddof=1))
    c, ac = ci(a[:, 0]), ci(a[:, 1])
    diff = a[:, 1] - a[:, 0]
    out[pair] = dict(n=n, R_C=dict(zip(("mean", "lo", "hi", "sd"), c)), R_A=dict(zip(("mean", "lo", "hi", "sd"), ac)),
                     seeds_act_better=int((diff > 0).sum()), C_ratio=float(a[:, 2].mean()),
                     R_C_all=a[:, 0].tolist(), R_A_all=a[:, 1].tolist())
    print(f"{pair:<22}{n:>3} {c[0]:8.3f} [{c[1]:.3f},{c[2]:.3f}] {ac[0]:8.3f} [{ac[1]:.3f},{ac[2]:.3f}] {int((diff > 0).sum()):>7}/{n} {a[:, 2].mean():8.3f}")
json.dump(out, open(os.path.join(d, "summary.json"), "w"), indent=2)
