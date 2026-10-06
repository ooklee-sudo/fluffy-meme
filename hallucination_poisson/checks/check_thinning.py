"""Numerical check of Proposition 3: Fano factor of an independently thinned over-dispersed count is 1 + p(F - 1)."""
import numpy as np

rng = np.random.default_rng(1)
for p in (0.6, 0.1, 0.01):
    M = rng.gamma(1 / 0.5 ** 2, 0.5 ** 2, 200000)
    N = rng.poisson(100 * M)
    F = N.var() / N.mean()
    Np = rng.binomial(N, p)
    print(f"p={p}: F={F:.2f} thinned Fano={Np.var() / Np.mean():.3f} formula={1 + p * (F - 1):.3f}")
