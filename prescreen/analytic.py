"""Stylized model: crossover budget N*(rho) below which twin pre-screening beats testing all K arms.
True logit effects ~ N(0, tau^2); twin score corr rho; binomial A/B on base CTR p0."""
import numpy as np, json, sys
tau, p0, K, m, R = 0.297, 0.015, 5, 2, 40000
rng = np.random.default_rng(3)
Ns = np.unique(np.round(np.logspace(np.log10(500), np.log10(256000), 28)).astype(int))
def regret(rho, N, screen):
    th = tau * rng.standard_normal((R, K)); s = rho * th / tau + np.sqrt(1 - rho**2) * rng.standard_normal((R, K))
    p = 1 / (1 + np.exp(-(np.log(p0 / (1 - p0)) + th)))
    idx = np.argsort(-s, 1)[:, :m] if screen else np.tile(np.arange(K), (R, 1))
    n = N // idx.shape[1]
    c = rng.binomial(n, np.take_along_axis(p, idx, 1))
    pick = np.take_along_axis(idx, (c + rng.uniform(0, .1, c.shape)).argmax(1)[:, None], 1)[:, 0]
    best = p.max(1); return ((best - p[np.arange(R), pick]) / best).mean()
out = {}
for rho in [-0.3, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.7]:
    d = np.array([regret(rho, N, True) - regret(rho, N, False) for N in Ns])
    k = np.argmax(d > 0) if (d > 0).any() else None
    nstar = None if k is None or k == 0 else float(np.exp(np.interp(0, [d[k-1], d[k]], [np.log(Ns[k-1]), np.log(Ns[k])])))
    out[rho] = nstar
    print(f"rho={rho:+.1f}  N* = {('never screens' if k == 0 else 'always') if nstar is None else f'{nstar:,.0f} impressions'}")
json.dump({str(k): v for k, v in out.items()}, open(sys.argv[1], 'w'))
