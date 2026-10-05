"""Exact cooperative-game analysis on tables indexed by coalition bitmask.

A game is a 1-D array g[mask], mask in [0, 2**n); bit i set <=> player i in S.
"""
import itertools
import math
import numpy as np


def popcount(n):
    return np.array([bin(m).count("1") for m in range(1 << n)])


def shapley(g, n):
    """Exact Shapley values phi_i(g) (does not need g[0]=0)."""
    g = np.asarray(g, float)
    w = [math.factorial(s) * math.factorial(n - s - 1) / math.factorial(n) for s in range(n)]
    pc = popcount(n)
    phi = np.zeros(n)
    for m in range(1 << n):
        for i in range(n):
            if not (m >> i) & 1:
                phi[i] += w[pc[m]] * (g[m | (1 << i)] - g[m])
    return phi


def loo(g, n):
    """Leave-one-out w({i}) = g(N) - g(N\\i)."""
    full = (1 << n) - 1
    return np.array([g[full] - g[full ^ (1 << i)] for i in range(n)])


def deletion_game(v, n):
    """w(R) = v(N) - v(N\\R)."""
    full = (1 << n) - 1
    return np.array([v[full] - v[full ^ r] for r in range(1 << n)])


def sequential_shapley(order_values):
    """Mean marginal over sampled permutations. order_values: list of (perm, vals)
    where vals[k] = estimated utility after removing perm[:k] from the full model
    (vals[0]=full-model utility). Marginal of perm[k] = vals[k]-vals[k+1]."""
    n = len(order_values[0][0])
    phi = np.zeros(n); cnt = np.zeros(n)
    for perm, vals in order_values:
        for k, p in enumerate(perm):
            phi[p] += vals[k] - vals[k + 1]; cnt[p] += 1
    return phi / cnt
