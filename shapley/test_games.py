import numpy as np
from games import *

def rand_game(n, seed=0):
    r = np.random.default_rng(seed); g = r.normal(size=1 << n); g[0] = 0; return g

def test_efficiency_and_duality():
    n = 5; v = rand_game(n)
    phi = shapley(v, n)
    assert np.isclose(phi.sum(), v[-1] - v[0])
    assert np.allclose(shapley(deletion_game(v, n), n), phi)   # Prop 1

def test_additive_bias():
    n = 5; v = rand_game(n, 1); e = rand_game(n, 2); e[-1] = 0; e[0] = 0.3
    assert np.allclose(shapley(v + e, n), shapley(v, n) + shapley(e, n))
    assert np.isclose(shapley(e, n).sum(), -e[0])              # Prop 2

def test_duplicates():
    n = 3; v = np.zeros(8)
    for m in range(8): v[m] = 1.0 if (m & 3) else 0.0          # players 0,1 substitutes
    assert np.allclose(shapley(v, n), [.5, .5, 0]); assert np.allclose(loo(v, n), 0)
