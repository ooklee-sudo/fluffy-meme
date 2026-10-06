"""Parameter-recovery check of the seasonal Hawkes estimator (failure_models.py): no false excitation at alpha=0, recovery otherwise."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from failure_models import Seasonal, hawkes_test, simulate_nhpp  # noqa: E402

rng = np.random.default_rng(3)
T = 24 * 540.0
s = np.where(np.arange(48) < 24, 1.0 + 0.8 * np.sin(np.arange(48) / 24 * np.pi), 0.3)
seas = Seasonal(np.datetime64(pd.Timestamp("2023-03-01")), T, s / s.mean())


def sim_hawkes(mu0, alpha, beta):
    base = simulate_nhpp(mu0, seas, T, rng)
    ev, queue = list(base), list(base)
    while queue:
        t = queue.pop()
        ch = t + rng.exponential(1 / beta, rng.poisson(alpha))
        ch = ch[ch < T]
        ev += list(ch)
        queue += list(ch)
    return np.sort(np.array(ev))


for mu0, alpha, beta in [(0.03, 0.0, 1.0), (0.03, 0.3, 1.0), (0.02, 0.5, 0.5)]:
    th = sim_hawkes(mu0, alpha, beta)
    r = hawkes_test(th, seas, T, n_boot=60, rng=rng)
    print(f"true mu0={mu0} alpha={alpha} beta={beta} (n={len(th)}) -> fit mu0={r['hawkes']['mu0']:.4f} alpha={r['hawkes']['alpha']:.2f} beta={r['hawkes']['beta']:.2f}  bootstrap p={r['bootstrap_p']:.3f}")
