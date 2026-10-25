"""Repeated-simulation calibration check for the NegBin hierarchical NHPP model.

For R replicate datasets (fixed 'true' parameters from nhpp_llm_econ.TRUE) refit the model and record
whether the 89% central interval covers the truth, for model parameters and for the economic
quantity V = C*_human - C*_LLM at complexity -1/0/+1. Also reports the rank of the truth within the
posterior draws (uniform if calibrated) and how often P(V>0) points at the right sign.

Run: python3 coverage_check.py [R]
"""
import sys
import numpy as np
import pandas as pd
import pymc as pm
import nhpp_llm_econ as M

R = int(sys.argv[1]) if len(sys.argv) > 1 else 60
KEYS = ["b0", "b_llm", "b_cx", "b_int", "g0", "g_llm", "g_cx", "s_u", "s_v", "alpha"]
rows = []
for r in range(R):
    M.RNG = np.random.default_rng(1000 + r)
    cx, proj, llm, Y, t = M.simulate()
    with M.build(cx, proj, llm, Y, t, True):
        idata = pm.sample(600, tune=800, chains=4, cores=4, target_accept=0.9,
                          random_seed=r, progressbar=False)
    post = idata.posterior.to_dataset().stack(s=("chain", "draw"))
    div = int(idata.sample_stats["diverging"].sum())
    rec = {"rep": r, "div": div}
    for k in KEYS:
        d = post[k].values
        lo, hi = np.percentile(d, [5.5, 94.5])
        rec[f"{k}_cov"] = int(lo <= M.TRUE[k] <= hi)
        rec[f"{k}_rank"] = float((d < M.TRUE[k]).mean())
    for cx0 in (-1.0, 0.0, 1.0):
        _, Cs, _ = M.economics(idata.posterior, cx0)
        _, Ct = M.truth(cx0)
        V, Vt = Cs[0] - Cs[1], Ct[0] - Ct[1]
        lo, hi = np.percentile(V, [5.5, 94.5])
        rec[f"V{cx0:+.0f}_cov"] = int(lo <= Vt <= hi)
        rec[f"V{cx0:+.0f}_rank"] = float((V < Vt).mean())
        rec[f"V{cx0:+.0f}_signok"] = int(((V > 0).mean() > 0.5) == (Vt > 0))
    rows.append(rec)
    print(f"rep {r + 1}/{R} done (div={div})", flush=True)

df = pd.DataFrame(rows)
df.to_csv("coverage_results.csv", index=False)
print("\n=== Coverage of nominal 89% intervals (R=%d) ===" % R)
for c in [c for c in df.columns if c.endswith("_cov")]:
    print(f"{c[:-4]:8s} {df[c].mean():.2f}")
print("\n=== Rank-uniformity (KS p-value vs U(0,1)); small p => miscalibrated ===")
from scipy.stats import kstest
for c in [c for c in df.columns if c.endswith("_rank")]:
    print(f"{c[:-5]:8s} mean rank {df[c].mean():.2f}  KS p={kstest(df[c], 'uniform').pvalue:.3f}")
print("\n=== Sign of adoption value recovered by P(V>0)>0.5 ===")
for c in [c for c in df.columns if c.endswith("_signok")]:
    print(f"{c[:-7]:8s} {df[c].mean():.2f}")
print("\nreps with divergences:", int((df['div'] > 0).sum()))
