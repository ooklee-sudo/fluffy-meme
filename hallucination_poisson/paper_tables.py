"""Analytical tables for the paper (no LLM needed): Table 1 recomputed, overdispersion, layer dependence."""
import json
import numpy as np
from scipy import stats
from stats_model import capacity, capacity_nb, exceed_prob_nb

out = {}
# --- Table 1 of the original draft: lambda0=10, c=0.63, $150/unit, $25/layer
lam0, c, ch, cg, al = 10.0, 0.63, 150.0, 25.0, 0.95
t1 = []
for N in range(0, 8):
    lam = lam0 * (1 - c) ** N
    k = capacity(lam, al)
    t1.append({"N": N, "lambda": lam, "k_star": k, "labour": ch * k, "compute": cg * N, "total": ch * k + cg * N})
out["table1"] = t1
out["table1_argmin_N"] = min(t1, key=lambda r: r["total"])["N"]
out["k_zero_threshold"] = float(-np.log(al))  # lambda below which k*=0

# --- Proposition (overdispersion): Poisson capacity plan vs Gamma-mixed (NB) daily counts
od = []
for lam in (3.0, 10.0, 25.0):
    for cv in (0.0, 0.1, 0.2, 0.3, 0.5):
        kp = capacity(lam, al)
        if cv == 0:
            r, ex, kn = np.inf, 1 - al, kp
            ex = float(stats.poisson.sf(kp, lam))
        else:
            r = 1 / cv**2
            ex = exceed_prob_nb(lam, r, kp)
            kn = capacity_nb(lam, r, al)
        phi = 1 + lam * cv**2
        od.append({"lambda": lam, "cv": cv, "phi": phi, "k_poisson": kp, "k_negbin": kn,
                   "exceed_prob_poisson_plan": ex, "k_normal_approx": float(lam + stats.norm.ppf(al) * np.sqrt(lam * phi))})
out["overdispersion"] = od

# --- Proposition (dependence): Frechet bounds on lambda_N for N layers with equal clearance c
dep = []
for N in (1, 2, 3, 4):
    lo = lam0 * max(0.0, 1 - N * c)
    ind = lam0 * (1 - c) ** N
    hi = lam0 * (1 - c)
    dep.append({"N": N, "lambda_lower": lo, "lambda_indep": ind, "lambda_upper": hi,
                "k_lower": capacity(lo, al), "k_indep": capacity(ind, al), "k_upper": capacity(hi, al)})
out["dependence_bounds"] = dep
json.dump(out, open("runs/paper_tables.json", "w"), indent=1)
print("Table 1 argmin N =", out["table1_argmin_N"], "| k*=0 once lambda <=", round(out["k_zero_threshold"], 4))
for r in t1: print(r)
for r in od: print({k: round(v, 3) if isinstance(v, float) else v for k, v in r.items()})
for r in dep: print(r)
