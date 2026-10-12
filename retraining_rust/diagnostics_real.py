"""Pre-estimation diagnostics on weekly GitHub data: does the depreciation mechanism appear?
(1) Poisson (log link) of bug counts on weeks-since-release, with offset log(all_issues+1)
    and a linear time trend; (2) logit of release hazard on weeks-since-release.
Cluster (release-cycle) bootstrap CIs. Usage: python diagnostics_real.py data2"""
import sys, glob, csv, json
import numpy as np
from scipy.optimize import minimize

def load(path):
    r = list(csv.DictReader(open(path)))
    n = np.array([int(a["bugs"]) for a in r], float); a_ = np.array([int(a["all_issues"]) for a in r], float)
    d = np.array([int(a["release"]) for a in r]); age = np.zeros(len(r)); c = 0; cyc = np.zeros(len(r), int); k = 0
    for t in range(len(r)):
        age[t] = c; cyc[t] = k
        if d[t]: c = 1; k += 1
        else: c += 1
    return n, a_, d, age, cyc

def pois(y, X, off):
    def f(b):
        eta = np.clip(X @ b + off, -20, 20); return np.sum(np.exp(eta) - y * eta)
    b0 = np.zeros(X.shape[1]); b0[0] = np.log(max(y.mean(), .1))
    return minimize(f, b0, method="BFGS").x

def logit(y, X):
    def f(b):
        z = X @ b; return np.sum(np.logaddexp(0, z) - y * z)
    return minimize(f, np.zeros(X.shape[1]), method="BFGS").x

def est(n, a_, d, age, cyc, idx):
    t = np.arange(len(n))[idx] / 52.0
    X = np.c_[np.ones(idx.sum()), age[idx], t - t.mean()]
    bp = pois(n[idx], X, np.log(a_[idx] + 1))
    bl = logit(d[idx].astype(float), np.c_[np.ones(idx.sum()), np.minimum(age[idx], 8)])
    return bp[1], bl[1]

out = {}
for p in sorted(glob.glob(sys.argv[1] + "/*.csv")):
    n, a_, d, age, cyc = load(p); keep = (age >= 1) & (d == 0) | (d == 1)   # post-decision rows
    allidx = np.ones(len(n), bool)
    g_b, g_h = est(n, a_, d, age, cyc, allidx)
    rng = np.random.default_rng(0); cycles = np.unique(cyc); bs = []
    for _ in range(300):
        pick = rng.choice(cycles, len(cycles)); idx = np.zeros(len(n), bool)
        mask = np.isin(cyc, pick); idx = mask
        if idx.sum() < 30: continue
        # resample by weighting: simple cluster bootstrap via repetition
        rows = np.concatenate([np.where(cyc == c)[0] for c in pick])
        nn, aa, dd, ag, cy = n[rows], a_[rows], d[rows], age[rows], cyc[rows]
        try: bs.append(est(nn, aa, dd, ag, cy, np.ones(len(rows), bool)))
        except Exception: pass
    bs = np.array(bs)
    out[p.split("/")[-1][:-4]] = dict(
        bug_log_rate_per_week_of_age=[float(g_b)] + [float(v) for v in np.percentile(bs[:, 0], [5, 95])],
        release_logit_per_week_of_age=[float(g_h)] + [float(v) for v in np.percentile(bs[:, 1], [5, 95])])
    print(p.split("/")[-1][:-4], json.dumps(out[p.split("/")[-1][:-4]]))
json.dump(out, open("diagnostics_real.json", "w"), indent=1)
