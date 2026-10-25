"""Instance-heterogeneity model for LLM-agent issue resolution.

Each instance i has its own per-attempt success probability p_i. We observe n_i attempts, s_i successes.
  M1  p_i ~ Beta(alpha, beta)                       -> every instance is eventually solvable (reach = 1)
  M2  p_i = 0 w.p. 1-pi, else Beta(alpha, beta)     -> a share 1-pi is out of reach for this agent
Likelihood per instance: beta-binomial (M1) or zero-inflated beta-binomial (M2); uses ALL attempts and
needs no fixed attempt count (so no selection on n_i). Coverage after k attempts:
  C(k) = pi * (1 - B(alpha, beta+k)/B(alpha, beta))          (pi = 1 for M1)

Usage: python3 -I swe_beta_model.py <dir with nebius*.parquet> [n_bootstrap]
"""
import glob
import sys
import numpy as np
import pyarrow.parquet as pq
from scipy.optimize import minimize
from scipy.special import betaln, expit, gammaln, logit
import pandas as pd

d = sys.argv[1]
NB = int(sys.argv[2]) if len(sys.argv) > 2 else 100
rng = np.random.default_rng(1)

parts = [pq.read_table(f, columns=["instance_id", "model_name", "target"]).to_pandas()
         for f in sorted(glob.glob(f"{d}/nebius*.parquet"))]
df = pd.concat(parts, ignore_index=True)
agg = df.groupby(["model_name", "instance_id"]).target.agg(n="size", s="sum").reset_index()
print(f"shards: {len(parts)} | trajectories: {len(df)} | instances: {df.instance_id.nunique()}")


def bb_logpmf(s, n, a, b):
    return gammaln(n + 1) - gammaln(s + 1) - gammaln(n - s + 1) + betaln(s + a, n - s + b) - betaln(a, b)


def nll(theta, s, n, zi):
    a, b = np.exp(theta[0]), np.exp(theta[1])
    lp = bb_logpmf(s, n, a, b)
    if not zi:
        return -lp.sum()
    pi = expit(theta[2])
    ll = np.where(s == 0, np.logaddexp(np.log1p(-pi), np.log(pi) + lp), np.log(pi) + lp)
    return -ll.sum()


def fit(s, n, zi):
    best = None
    for a0, b0, p0 in ((0.3, 3.0, 2.0), (0.1, 1.0, 0.0), (1.0, 8.0, 1.0)):
        x0 = [np.log(a0), np.log(b0)] + ([p0] if zi else [])
        r = minimize(nll, x0, args=(s, n, zi), method="Nelder-Mead", options={"maxiter": 4000, "xatol": 1e-6, "fatol": 1e-8})
        if best is None or r.fun < best.fun:
            best = r
    th = best.x
    return dict(a=np.exp(th[0]), b=np.exp(th[1]), pi=(expit(th[2]) if zi else 1.0), nll=best.fun, k=len(th))


def coverage(f, k):
    return f["pi"] * (1 - np.exp(betaln(f["a"], f["b"] + k) - betaln(f["a"], f["b"])))


rows = []
for model, g in agg.groupby("model_name"):
    s, n = g.s.values.astype(float), g.n.values.astype(float)
    if len(g) < 50:
        continue
    f1, f2 = fit(s, n, False), fit(s, n, True)
    aic1, aic2 = 2 * f1["k"] + 2 * f1["nll"], 2 * f2["k"] + 2 * f2["nll"]
    boots = []
    for _ in range(NB):
        idx = rng.integers(0, len(g), len(g))
        boots.append(fit(s[idx], n[idx], True)["pi"])
    lo, hi = np.percentile(boots, [5.5, 94.5])
    rows.append(dict(model=model, instances=len(g), traj=int(n.sum()), raw_solve_rate=s.sum() / n.sum(),
                     ever_solved=(s > 0).mean(), alpha=f2["a"], beta=f2["b"], reach_pi=f2["pi"],
                     pi_lo=lo, pi_hi=hi, aic_beta=aic1, aic_zibeta=aic2,
                     cov12=coverage(f2, 12), cov100=coverage(f2, 100), cov100_M1=coverage(f1, 100)))
res = pd.DataFrame(rows)
pd.set_option("display.width", 220)
print(res.round(3).T.to_string())
res.to_csv("swe_beta_results.csv", index=False)
