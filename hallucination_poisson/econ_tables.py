"""Economic-interpretation numbers for the paper: newsvendor service level, cost of misspecification,
cost of the independence assumption, and factor-substitution comparative statics. Writes runs/econ_tables.json."""
import json, numpy as np
from scipy import stats

CH = 150.0            # $ per capacity unit per day (scenario value used throughout the paper)
ALPHA = 0.95

def nb(lam, c):
    r = 1.0 / c**2
    return stats.nbinom(r, r / (r + lam))

def pq(dist, a):
    return int(dist.ppf(a))

def exp_short(dist, k, hi=4000):
    x = np.arange(k + 1, hi)
    return float(np.sum((x - k) * dist.pmf(x)))

def cost(dist, k, cu):
    return CH * k + cu * exp_short(dist, k)

def opt_k(dist, cu):
    # newsvendor: smallest k with P(X > k) <= CH/Cu
    return pq(dist, 1 - CH / cu) if cu > CH else 0

out = {"C_h": CH}
out["implied_shortfall_cost"] = {str(a): CH / (1 - a) for a in (0.5, 0.8, 0.9, 0.95, 0.99)}

# (1) cost of ignoring over-dispersion at the optimal service level for Cu = C_h/(1-alpha)
cu = CH / (1 - ALPHA)
rows = []
for lam in (10, 25, 120.7):
    for c in (0.3, 0.44):
        tru = nb(lam, c); poi = stats.poisson(lam)
        kp, kn, km = opt_k(poi, cu), opt_k(tru, cu), int(lam)
        cn, cpl, cm = cost(tru, kn, cu), cost(tru, kp, cu), cost(tru, km, cu)
        rows.append(dict(lam=lam, c=c, k_poisson=kp, k_true=kn, k_mean=km, cost_true_opt=cn, cost_poisson_plan=cpl, cost_mean_plan=cm,
                         excess_poisson_pct=100 * (cpl / cn - 1), excess_mean_pct=100 * (cm / cn - 1)))
out["misspecification"] = dict(Cu=cu, rows=rows)

# (2) cost of the independence assumption for a 3-layer cascade (lambda0=10, clearance .63)
l0, ci = 10.0, 0.63
res = []
for N in (2, 3, 4):
    indep = l0 * (1 - ci) ** N
    upper = l0 * (1 - ci)
    lo = max(0.0, 1 - N * ci) * l0
    kind = opt_k(stats.poisson(indep), cu)
    row = dict(N=N, lam_lower=lo, lam_indep=indep, lam_upper=upper, k_indep_plan=kind)
    for nm, lam in (("indep", indep), ("upper", upper)):
        d = stats.poisson(lam)
        row[f"cost_at_{nm}_truth"] = cost(d, kind, cu)
        row[f"opt_k_{nm}"] = opt_k(d, cu)
        row[f"opt_cost_{nm}"] = cost(d, opt_k(d, cu), cu)
    res.append(row)
out["independence_error"] = dict(Cu=cu, rows=res)

# (3) factor substitution: optimal depth against the labour/compute cost ratio (alpha constraint, as in Proposition 5)
g = 25.0
sub = []
for ch in (25, 50, 100, 150, 300, 600, 1200):
    best = {}
    for kmin in (0, 1):
        f = []
        for N in range(0, 9):
            lam = l0 * (1 - ci) ** N
            k = pq(stats.poisson(lam), ALPHA)
            f.append(ch * max(kmin, k) + g * N)
        best[kmin] = int(np.argmin(f))
    sub.append(dict(C_h=ch, theta=ch / g, N_star_kmin0=best[0], N_star_kmin1=best[1]))
out["factor_substitution"] = sub
json.dump(out, open("runs/econ_tables.json", "w"), indent=1)
print(json.dumps(out, indent=1)[:3000])
