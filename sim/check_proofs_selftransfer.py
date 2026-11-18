"""Check Lemma A1 and Proposition 3 in the model WITH self-transfer (random parameters).
 (i)   a_c, z_c nondecreasing and P_c nonincreasing in the threshold c
 (ii)  n*(H) and n*(d) nondecreasing; value of verification V(H;d) nondecreasing in H; plateau d(Fu-Fd) z_inf; envelope identity
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
from chain_selftransfer import quantities, NINF

rng = np.random.default_rng(11)
NMAX = 30


def tab(tw, th, k, c, mu, q):
    ns = list(range(NMAX + 1)) + [NINF]
    a, z, P = zip(*[quantities(n, tw, th, k, c, mu, q) for n in ns])
    return np.array(a), np.array(z), np.array(P)


def best(a, z, P, F, H, tol=1e-9):
    """Smallest minimizing threshold, treating costs within tol as tied: neighbouring large thresholds are reached with
    probability below 1e-16 and have identical cost up to rounding, so an exact argmin would flip between them."""
    cs = a + F * z + P * H
    m = float(cs.min())
    return int(np.where(cs <= m + tol)[0].min()), m


bad_i = bad_mono = bad_n = bad_plat = bad_env = bad_d = 0
N = 40
for _ in range(N):
    k = rng.uniform(0.5, 2); c = rng.uniform(1, 8); mu = rng.uniform(0.02, 0.3); q = rng.uniform(0.03, 0.3)
    tw = rng.uniform(0.05, 0.7); th = rng.choice([0.0, rng.uniform(0.05, 0.7)])
    a, z, P = tab(tw, th, k, c, mu, q)
    bad_i += not (np.all(np.diff(a) > -1e-10) and np.all(np.diff(z) > -1e-10) and np.all(np.diff(P) < 1e-10))
    Fu = rng.uniform(40, 200); Fd = rng.uniform(5, 0.6 * Fu); dq = rng.uniform(0.1, 1.0); Fe = dq * Fd + (1 - dq) * Fu
    Hs = np.linspace(1, 600, 240); V = []; prev = -1; ok = True
    for H in Hs:
        n0, c0 = best(a, z, P, Fu, H); n1, c1 = best(a, z, P, Fe, H)
        V.append(c0 - c1); ok &= n0 >= prev; prev = n0
    V = np.array(V)
    bad_mono += bool(np.any(np.diff(V) < -1e-9)); bad_n += (not ok)
    bad_plat += abs(V[-1] - (Fu - Fe) * z[-1]) > 1e-6
    H = Hs[len(Hs) // 3]; fs = np.linspace(Fe, Fu, 3001)
    integ = np.trapezoid([z[best(a, z, P, f, H)[0]] for f in fs], fs)
    bad_env += abs(integ - (best(a, z, P, Fu, H)[1] - best(a, z, P, Fe, H)[1])) > 5e-3 * max(1, abs(integ))
    prev = -1; okd = True
    for d_ in np.linspace(0, 1, 41):
        n, _ = best(a, z, P, d_ * Fd + (1 - d_) * Fu, H)
        okd &= n >= prev; prev = n
    bad_d += (not okd)
print(f"with self-transfer, {N} random parameter sets (half with theta_h = 0):")
print(f"  Lemma A1 monotonicity of a_c, z_c, P_c: violations {bad_i}/{N}")
print(f"  n*(H) nondecreasing: {bad_n}/{N};  n*(d) nondecreasing: {bad_d}/{N}")
print(f"  V(H;d) nondecreasing in H: {bad_mono}/{N};  plateau d(Fu-Fd)z_inf: {bad_plat}/{N};  envelope identity: {bad_env}/{N}")
