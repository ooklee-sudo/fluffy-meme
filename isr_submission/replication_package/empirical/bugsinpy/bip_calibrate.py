"""Final BugsInPy summary: reach A(K) with project-cluster bootstrap, leave-one-project-out sensitivity, and the adoption-window bound kappa-bar(A)
(solution of h(kappa) = A; the upper end of the adoption window for a tool that is very cheap relative to humans; infinite for A >= 1)."""
import glob, json, os, sys
import numpy as np
from scipy.optimize import brentq
HERE = os.path.dirname(os.path.abspath(__file__))
h = lambda x: 0.0 if x <= 1 else 1 - (1 + np.log(x)) / x
kbar = lambda A: np.inf if A >= 1 else (np.nan if A <= 0 else brentq(lambda k: h(k) - A, 1 + 1e-9, 1e12))
data = [json.load(open(p)) for p in sorted(glob.glob(f"{HERE}/work/study_results/*.json"))]
models = sorted({m for d in data for m in d["models"]}); K = 6; rng = np.random.default_rng(0)
def det(d, m, k):
    at = d["models"].get(m, {}).get("attempts", []); return any(x["detected"] for x in at[:k]) if len(at) >= k else None
projects = sorted({d["bug"].split("/")[0] for d in data})
print(f"{len(data)} bugs; projects: " + ", ".join(f"{p} ({sum(d['bug'].startswith(p + '/') for d in data)})" for p in projects))
for m in models:
    for k in (1, 3, 6):
        rows = [(d["bug"].split("/")[0], det(d, m, k)) for d in data if det(d, m, k) is not None]
        by = {p: np.array([v for q, v in rows if q == p], float) for p in projects if any(q == p for q, _ in rows)}
        allv = np.concatenate(list(by.values())); A = allv.mean()
        bs = []
        for _ in range(3000):
            ps = rng.choice(list(by), len(by))                       # resample projects, then bugs within each
            v = np.concatenate([by[p][rng.integers(0, len(by[p]), len(by[p]))] for p in ps]); bs.append(v.mean())
        lo, hi = np.percentile(bs, [2.5, 97.5])
        loo = {p: np.concatenate([by[q] for q in by if q != p]).mean() for p in by}
        kb = lambda x: "inf" if np.isinf(x) else f"{x:.1f}"
        print(f"{m:32s} K={k}: A={A:.2f} (project-cluster 95% CI {lo:.2f}-{hi:.2f}), n={len(allv)}; leave-one-project-out range {min(loo.values()):.2f}-{max(loo.values()):.2f}; kappa-bar(A)={kb(kbar(A))} [{kb(kbar(max(lo,1e-3)))}, {kb(kbar(min(hi,0.999)))}]")
