"""Discrete-time Hawkes model with a gamma-distributed baseline per trajectory (heterogeneity) and a step trend.
P(error at step t) = 1 - exp(-lambda_t),  lambda_t = mu_i * (1 + t)^gamma + alpha * S_t,  S_t = sum_{s<t} delta^(t-1-s) e_s,
mu_i ~ Gamma(shape k, scale theta) integrated out on a log grid. Branching ratio n = alpha / (1 - delta).
Nested models: Poisson-type (no RE, alpha=0), RE only (alpha=0), Hawkes only (no RE), RE + Hawkes.
python3 -I hawkes_re.py events.parquet out.json"""
import sys, json
import numpy as np, pandas as pd
from scipy.optimize import minimize
from scipy.stats import gamma as G
from scipy.special import logsumexp
rng = np.random.default_rng(0)
df = pd.read_parquet(sys.argv[1]); df = df[df.n_steps >= 6].reset_index(drop=True)
GRID = np.exp(np.linspace(np.log(1e-4), np.log(6.0), 32)); LG = np.log(GRID); DLG = np.gradient(LG)
def pad(seqs):
    seqs = [e[:60] for e in seqs]                                                          # first 60 steps
    T = max(map(len, seqs)); E = np.zeros((len(seqs), T)); M = np.zeros((len(seqs), T))
    for i, e in enumerate(seqs): E[i, :len(e)] = e; M[i, :len(e)] = 1
    return E, M
def excite(E, delta):
    S = np.zeros_like(E); acc = np.zeros(E.shape[0])
    for t in range(E.shape[1]): S[:, t] = acc; acc = acc * delta + E[:, t]
    return S
def nll(th, E, M, re=True, hawkes=True):
    gam = th[0]; alpha = np.exp(th[1]) if hawkes else 0.0; delta = 1 / (1 + np.exp(-th[2])) if hawkes else 0.5
    tt = np.arange(E.shape[1]); trend = (1.0 + tt) ** gam; S = excite(E, delta) if hawkes else 0 * E
    if re:
        k, sc = np.exp(th[3]), np.exp(th[4])
        lw = G.logpdf(GRID, k, scale=sc) + LG + np.log(DLG); lw -= logsumexp(lw)              # quadrature weights in log mu
        lam = GRID[None, None, :] * trend[None, :, None] + alpha * S[:, :, None]            # N x T x Q
        ll = (E[:, :, None] * np.log(np.clip(-np.expm1(-lam), 1e-12, 1)) - (1 - E[:, :, None]) * lam) * M[:, :, None]
        return -logsumexp(ll.sum(1) + lw[None, :], axis=1).sum()
    mu = np.exp(th[3]); lam = mu * trend[None, :] + alpha * S
    return -((E * np.log(np.clip(-np.expm1(-lam), 1e-12, 1)) - (1 - E) * lam) * M).sum()
def fit(E, M, re, hawkes):
    x0 = [0.0, np.log(0.2), 1.0, np.log(1.0), np.log(0.1)] if re else [0.0, np.log(0.2), 1.0, np.log(0.1)]
    f = lambda th: nll(th, E, M, re, hawkes)
    r = minimize(f, x0, method="L-BFGS-B", options=dict(maxiter=200))
    th = r.x; out = dict(nll=round(float(r.fun), 1), gamma_trend=round(float(th[0]), 3), k=len(th) - (0 if hawkes else 2))
    if hawkes:
        a, d = float(np.exp(th[1])), float(1 / (1 + np.exp(-th[2]))); out.update(alpha=round(a, 3), delta=round(d, 3), branching=round(a / (1 - d), 3))
    if re:
        k, sc = float(np.exp(th[3])), float(np.exp(th[4])); out.update(re_shape=round(k, 3), re_scale=round(sc, 4), re_mean=round(k * sc, 4), re_cv=round(1 / np.sqrt(k), 3))
    else: out.update(mu=round(float(np.exp(th[3])), 4))
    return out, th
res = {}
for mdl, grp in df.groupby("model"):
    idx = grp.index.values; idx = rng.choice(idx, size=min(1200, len(idx)), replace=False)
    E, M = pad([np.array(df.errors[i], float) for i in idx]); r = {}
    for name, re_, hk in (("poisson_trend", False, False), ("re_only", True, False), ("hawkes_only", False, True), ("re_hawkes", True, True)):
        r[name] = fit(E, M, re_, hk)[0]; print(mdl, name, r[name], flush=True)
    r["LR_hawkes_given_re"] = round(2 * (r["re_only"]["nll"] - r["re_hawkes"]["nll"]), 1)
    r["LR_re_given_hawkes"] = round(2 * (r["hawkes_only"]["nll"] - r["re_hawkes"]["nll"]), 1)
    r["n_traj"] = len(idx); res[mdl] = r
# bootstrap interval of the branching ratio for the largest group (trajectory resampling)
mdl = df.model.value_counts().index[0]; idx = df[df.model == mdl].index.values; bs = []
for b in range(12):
    s = rng.choice(idx, size=1000, replace=True); E, M = pad([np.array(df.errors[i], float) for i in s])
    bs.append(fit(E, M, True, True)[0]["branching"])
res["bootstrap_branching_" + mdl] = dict(mean=round(float(np.mean(bs)), 3), lo=round(float(np.percentile(bs, 2.5)), 3), hi=round(float(np.percentile(bs, 97.5)), 3), reps=len(bs), size=1000)
json.dump(res, open(sys.argv[2], "w"), indent=1); print(json.dumps(res, indent=1))
