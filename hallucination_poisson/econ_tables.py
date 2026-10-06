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

# (4) moral hazard in review: per-item effort e in [0,1], cost psi*e^2/2 per reviewed item, reward r per error found
M, psi, r, h = 1000.0, 0.3, 7.5, 100.0       # items reviewed/day, effort cost scale ($/item), reward per error found ($), harm per undetected error ($)
lam0, ci2, g2 = 100.0, 0.63, 25.0
mh = []
for N in range(0, 7):
    lam = lam0 * (1 - ci2) ** N
    rho = lam / M
    e = min(1.0, r * rho / psi)
    handled, undet = e * lam, (1 - e) * lam
    k_naive = pq(stats.poisson(lam), ALPHA)
    k_true = pq(stats.poisson(max(handled, 1e-9)), ALPHA)
    mh.append(dict(N=N, lam=lam, prevalence=rho, effort=e, handled=handled, undetected=undet,
                   k_naive=k_naive, k_true=k_true,
                   cost_believed=CH * k_naive + g2 * N,
                   cost_true_fixed_reward=CH * k_true + h * undet + g2 * N + r * handled,
                   cost_full_vigilance=CH * k_naive + psi * M + g2 * N,
                   reward_needed_full_vigilance=psi / rho))
best = lambda key: int(min(mh, key=lambda x: x[key])["N"])
gate = {}
N = 3; lam = lam0 * (1 - ci2) ** N
for s, gm in ((0.7, 0.2), (0.9, 0.2)):
    e_ng = min(1, r * lam / M / psi); e_g = min(1, r * s * lam / (gm * M) / psi)
    gate[f"s={s},gamma={gm}"] = dict(detected_no_gate=lam * e_ng, detected_gate=s * lam * e_g, ratio=(s * lam * e_g) / (lam * e_ng), s2_over_gamma=s * s / gm)
out["moral_hazard"] = dict(params=dict(M=M, psi=psi, r=r, h=h, lam0=lam0, clearance=ci2, g=g2, alpha=ALPHA),
                           rows=mh, N_star_believed=best("cost_believed"), N_star_true_fixed_reward=best("cost_true_fixed_reward"),
                           N_star_full_vigilance=best("cost_full_vigilance"), gate_N3=gate)
json.dump(out, open("runs/econ_tables.json", "w"), indent=1)
print(json.dumps(out["moral_hazard"], indent=1))
