"""Validate analysis.py on synthetic data with known generating process.

Checks: (1) dispersion test size under true Poisson, (2) power under NB,
(3) AIC selects the true family, (4) clustered samples (shared task effect)
look overdispersed if the task effect is ignored.
"""
import numpy as np

from analysis import dispersion_tests, fit_models

rng = np.random.default_rng(0)
N, REPS = 300, 100


def gen(kind, n):
    mu = 1.5
    if kind == "poisson":
        return rng.poisson(mu, n)
    if kind == "negbin":  # gamma-Poisson, alpha=0.8
        a = 0.8
        return rng.poisson(rng.gamma(1 / a, mu * a, n))
    if kind == "zip":  # 40% structural zeros
        return np.where(rng.random(n) < 0.4, 0, rng.poisson(mu * 2, n))
    if kind == "task_effect":  # 30 tasks x 10 samples, shared lognormal task rate
        lam = np.repeat(rng.lognormal(np.log(mu), 0.9, n // 10), 10)
        return rng.poisson(lam)


print(f"N={N}, reps={REPS}, alpha=0.05 one-sided Cameron-Trivedi\n")
print(f"{'truth':12s} {'CT reject':>10s} {'pearson':>8s}   AIC winner counts")
for kind in ["poisson", "negbin", "zip", "task_effect"]:
    rej, pr, wins = 0, [], {}
    for _ in range(REPS):
        y = gen(kind, N)
        d = dispersion_tests(y)
        rej += d["ct_p_one_sided"] < 0.05
        pr.append(d["pearson_ratio"])
        w = fit_models(y).iloc[0]["model"]
        wins[w] = wins.get(w, 0) + 1
    print(f"{kind:12s} {rej / REPS:10.2f} {np.mean(pr):8.2f}   {dict(sorted(wins.items()))}")
