"""Pre-estimation diagnostics on weekly GitHub data: does the depreciation mechanism appear?
(1) Poisson (log link) of bug counts on weeks-since-release, offset log(all_issues+1), linear time trend;
(2) logit of release hazard on weeks-since-release (age capped at 8).
Cluster (release-cycle) bootstrap SEs that keep each row's original calendar time.
Eligibility is fixed in advance: >= MIN_REL releases and >= MIN_WEEKS weeks. Reports every repo
(including ineligible ones, flagged) and a random-effects (DerSimonian-Laird) pooled slope.
Usage: python diagnostics_real.py data_dir [--min-rel 10] [--min-weeks 80]"""
import sys, glob, csv, json, argparse
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
    return n, a_, d, age, cyc, np.arange(len(r)) / 52.0

def pois(y, X, off):
    def f(b):
        eta = np.clip(X @ b + off, -20, 20); return np.sum(np.exp(eta) - y * eta)
    b0 = np.zeros(X.shape[1]); b0[0] = np.log(max(y.mean(), .1))
    return minimize(f, b0, method="BFGS").x

def logit(y, X):
    def f(b):
        z = X @ b; return np.sum(np.logaddexp(0, z) - y * z)
    return minimize(f, np.zeros(X.shape[1]), method="BFGS").x

def est(n, a_, d, age, t):
    X = np.c_[np.ones(len(n)), age, t - t.mean()]
    bp = pois(n, X, np.log(a_ + 1))
    bl = logit(d.astype(float), np.c_[np.ones(len(n)), np.minimum(age, 8)])
    return bp[1], bl[1]

def dl(b, se):
    b, se = np.array(b), np.array(se); w = 1 / se**2; fe = np.sum(w * b) / w.sum()
    q = np.sum(w * (b - fe) ** 2); tau2 = max(0, (q - (len(b) - 1)) / (w.sum() - (w**2).sum() / w.sum())) if len(b) > 1 else 0
    w2 = 1 / (se**2 + tau2); m = np.sum(w2 * b) / w2.sum(); s = np.sqrt(1 / w2.sum()); return m, s, tau2

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("dir"); ap.add_argument("--min-rel", type=int, default=10)
    ap.add_argument("--min-weeks", type=int, default=80); ap.add_argument("--boot", type=int, default=300); a = ap.parse_args()
    out, el = {}, []
    for p in sorted(glob.glob(a.dir + "/*.csv")):
        name = p.replace("\\", "/").split("/")[-1][:-4]
        n, a_, d, age, cyc, t = load(p)
        rec = dict(weeks=len(n), releases=int(d.sum()), median_cycle=float(np.median(np.diff(np.where(d == 1)[0]))) if d.sum() > 1 else None,
                   eligible=bool(d.sum() >= a.min_rel and len(n) >= a.min_weeks))
        if rec["eligible"]:
            gb, gh = est(n, a_, d, age, t)
            rng = np.random.default_rng(0); cycles = np.unique(cyc); bs = []
            for _ in range(a.boot):
                rows = np.concatenate([np.where(cyc == c)[0] for c in rng.choice(cycles, len(cycles))])
                try: bs.append(est(n[rows], a_[rows], d[rows], age[rows], t[rows]))
                except Exception: pass
            bs = np.array(bs); se = bs.std(axis=0, ddof=1)
            rec.update(bug_slope=float(gb), bug_se=float(se[0]), hazard_slope=float(gh), hazard_se=float(se[1]))
            el.append(rec)
        out[name] = rec
        print(name, json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in rec.items()}))
    if len(el) >= 2:
        pb = dl([r["bug_slope"] for r in el], [r["bug_se"] for r in el]); ph = dl([r["hazard_slope"] for r in el], [r["hazard_se"] for r in el])
        out["_pooled"] = dict(k=len(el), bug=dict(est=pb[0], se=pb[1], tau2=pb[2]), hazard=dict(est=ph[0], se=ph[1], tau2=ph[2]),
                              share_bug_positive=float(np.mean([r["bug_slope"] > 0 for r in el])), share_hazard_positive=float(np.mean([r["hazard_slope"] > 0 for r in el])))
        print("POOLED", json.dumps(out["_pooled"], default=float))
    json.dump(out, open("diagnostics_real.json", "w"), indent=1)

if __name__ == "__main__":
    main()
