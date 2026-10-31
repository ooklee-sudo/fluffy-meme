"""Table 5 of the manuscript: optimal screening depth under common-difficulty dependence (Proposition 4(c)).
Beta-distributed catch probability with mean c and correlation rho between layers; lambda_N = lambda0 * prod_{k<N} ((1-c)s+k)/(s+k), s=(1-rho)/rho.
Run: python econ_dependence.py   (writes results/table5.json)"""
import json, os
import numpy as np
from scipy import special, stats

C, L0, CH, G, ALPHA = 0.63, 10.0, 150, 25, 0.95
kp = lambda lam: int(stats.poisson.ppf(ALPHA, lam)) if lam > 0 else 0


def lam(n, rho):
    if n == 0: return L0
    if rho <= 0: return L0 * (1 - C) ** n
    if rho >= 1: return L0 * (1 - C)
    s = (1 - rho) / rho
    return L0 * float(np.exp(special.betaln(C * s, (1 - C) * s + n) - special.betaln(C * s, (1 - C) * s)))


def cost(rho, kmin):
    return [CH * max(kmin, kp(lam(n, rho))) + G * n for n in range(41)]


rows = []
n_ind = {km: int(np.argmin(cost(0, km))) for km in (0, 1)}
for rho in (0, .02, .05, .1, .2, .3, .5, 1):
    r = {"rho": rho, "lam3": round(lam(3, rho), 2), "k3": kp(lam(3, rho))}
    for km in (0, 1):
        f = cost(rho, km); n = int(np.argmin(f))
        r[f"N_kmin{km}"] = n; r[f"cost_kmin{km}"] = f[n]; r[f"extra_kmin{km}"] = f[n_ind[km]] - f[n]
    rows.append(r); print(r)
json.dump(rows, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "table5.json"), "w"), indent=1)
