"""Numerical verification of the paper's propositions and worked examples (Sections 3-5, 6 P5/P6).

    python theory_checks.py            # prints a PASS/FAIL table, exits non-zero on failure
Random games are used, so passing means the algebra in the proofs matches the code, not that the
statements are merely illustrated by one example.
"""
import itertools
import sys

import numpy as np

import shapley as sh

rng = np.random.default_rng(0)
results = []


def check(name, ok, detail=""):
    results.append((name, bool(ok), detail))


def random_game(n, scale=1.0):
    tab = {S: float(rng.normal() * scale) for S in sh.subsets(range(n))}
    tab[frozenset()] = 0.0
    return sh.as_game(tab)


# --- Proposition 1: duality ----------------------------------------------------------------------
err = 0
for n in (2, 3, 4, 5):
    for _ in range(20):
        v = random_game(n)
        err = max(err, np.abs(sh.shapley(sh.deletion_game(v, n), n) - sh.shapley(v, n)).max())
check("Prop 1  phi(w) = phi(v)", err < 1e-12, f"max err {err:.1e}")
# Banzhaf is also invariant (symmetric weights)
err = max(np.abs(sh.banzhaf(sh.deletion_game(v, n), n) - sh.banzhaf(v, n)).max()
          for n in (3, 4) for v in [random_game(n)])
check("Prop 1 ext.  Banzhaf duality", err < 1e-12, f"max err {err:.1e}")

# --- 3.3 LOO redundancy example ------------------------------------------------------------------
a = 1.0
v = sh.as_game({frozenset(): 0, frozenset({0}): a, frozenset({1}): a, frozenset({0, 1}): a})
check("3.3  redundancy: LOO ~ 0, Shapley = a/2",
      np.allclose(sh.leave_one_out(v, 2), 0) and np.allclose(sh.shapley(v, 2), a / 2))

# --- Proposition 2: replication ------------------------------------------------------------------
err = 0
for n in (2, 3, 4):
    for _ in range(10):
        v = random_game(n)
        for i in range(n):
            err = max(err, abs(sh.replication_gain(v, n, i) - sh.replication_gain_formula(v, n, i)))
check("Prop 2  replication gain = (n+1)^-1 sum w_S (n-1-2s) m_i(S)", err < 1e-12, f"max err {err:.1e}")
a_, b_, c_ = 1.0, 0.7, 1.2
v = sh.as_game({frozenset(): 0, frozenset({0}): a_, frozenset({1}): b_, frozenset({0, 1}): c_})
vp = sh.replicate(v, 2, 0)
phip = sh.shapley(vp, 3)
check("Prop 2  two-player example (2a+c-b)/3, gain (a+b-c)/6",
      abs(phip[0] + phip[2] - (2 * a_ + c_ - b_) / 3) < 1e-12
      and abs(sh.replication_gain(v, 2, 0) - (a_ + b_ - c_) / 6) < 1e-12)
add = sh.as_game({S: 0.3 * len(S) + 0.1 * sum(S) for S in sh.subsets(range(4))})
check("Prop 2  additive game: replication neutral", abs(sh.replication_gain(add, 4, 1)) < 1e-12)
# replication also leaves the sum constant (efficiency) -> others lose exactly the gain
n = 4; v = random_game(n); g = sh.replication_gain(v, n, 0)
before, after = sh.shapley(v, n), sh.shapley(sh.replicate(v, n, 0), n + 1)
check("Prop 2  others lose exactly the replicator's gain",
      abs((before.sum() - before[0]) - (after.sum() - after[0] - after[n]) - g) < 1e-12)

# --- Merging (majority game) ---------------------------------------------------------------------
maj = sh.as_game({S: 1.0 if len(S) >= 2 else 0.0 for S in sh.subsets(range(3))})
phi_m = sh.shapley(sh.merge(maj, 3, 0, 1), 2)
check("3.4  merging in the 3-player majority game: merged player gets 1 (vs 2/3)",
      np.allclose(sh.shapley(maj, 3), 1 / 3) and abs(phi_m[0] - 1) < 1e-12)

# --- Proposition 3: additive bias ----------------------------------------------------------------
worst_dec = worst_sum = 0
for n in (3, 4, 5):
    for _ in range(10):
        U = random_game(n); U0 = sh.as_game({S: U(S) + 0.4 for S in sh.subsets(range(n))})
        eps = random_game(n)
        eps_t = {S: eps(S) for S in sh.subsets(range(n))}; eps_t[frozenset(range(n))] = 0.0  # eps(N)=0
        Uh = lambda T, U0=U0, eps_t=eps_t: U0(T) + eps_t[frozenset(T)]
        r = sh.additive_bias_check(U0, Uh, n)
        worst_dec, worst_sum = max(worst_dec, r["decomposition_err"]), max(worst_sum, r["sum_err"])
check("Prop 3  phi(v_hat) = phi(v) + phi(eps)", worst_dec < 1e-12, f"max err {worst_dec:.1e}")
check("Prop 3  sum phi(v_hat) = v(N) - eps(empty)", worst_sum < 1e-12, f"max err {worst_sum:.1e}")
# special cases of 4.2: eps(T) = sum_{j not in T} r_j  ->  phi_i(eps) = -r_i
n = 4; r_ = np.array([0.1, 0.5, 0.2, 0.9])
epsr = lambda T: sum(r_[j] for j in range(n) if j not in T)
check("4.2  heterogeneous residue: phi_i(eps) = -r_i", np.allclose(sh.shapley(epsr, n), -r_))
# constant shift of the baseline leaves Shapley values unchanged
v = random_game(4); shifted = lambda S: v(S) + 3.0
check("4.2  constant shift in v_hat leaves Shapley values unchanged", np.allclose(sh.shapley(v, 4), sh.shapley(shifted, 4)))

# --- Propositions 4-5 (P5): sequential bias, all n! orders -------------------------------------------
worst_sum = 0; worst_ratio = 0
for n in (3, 4):
    for _ in range(5):
        U = random_game(n)
        table = {}
        def U_seq(prefix, U=U, n=n, table=table):
            if prefix not in table:
                T = frozenset(range(n)) - frozenset(prefix)
                table[prefix] = U(T) + (0.0 if not prefix else rng.normal() * 0.3 * len(prefix))  # path-dependent residual
            return table[prefix]
        r = sh.sequential_bias_check(U, U_seq, n)
        worst_sum = max(worst_sum, r["sum_err"])
        worst_ratio = max(worst_ratio, r["prop5_gap"] - r["prop5_bound"])
check("Prop 4  sum phi_tilde = v(N) - eps_bar(empty)  (P5, exact over all n! orders)", worst_sum < 1e-12, f"max err {worst_sum:.1e}")
check("Prop 5  |phi_tilde - phi - phi(eps_bar)| <= n^-1 sum_{k>=2} delta_k", worst_ratio <= 1e-12, f"max excess {worst_ratio:.1e}")
# path independence => phi_tilde = phi(v) + phi(eps)
n = 4; U = random_game(n); eps_t = {S: float(rng.normal() * 0.2) for S in sh.subsets(range(n))}; eps_t[frozenset(range(n))] = 0.0
U_seq = lambda prefix: U(frozenset(range(n)) - frozenset(prefix)) + eps_t[frozenset(range(n)) - frozenset(prefix)]
r = sh.sequential_bias_check(U, U_seq, n)
check("Prop 5  path independence: phi_tilde = phi(v) + phi(eps)",
      np.allclose(r["phi_tilde"], r["phi"] + sh.shapley(lambda T: eps_t[frozenset(T)], n)) and r["prop5_bound"] < 1e-12)

# --- Proposition 6: audit condition ------------------------------------------------------------
ok = True
for _ in range(2000):
    p, d = rng.uniform(0, 1, 2); F, C, c, b, rho = rng.uniform(0, 5, 5); c = min(c, C)
    exact, approx = -C, -c + b * rho - p * d * F
    ok &= (exact >= approx - 1e-12) == sh.truthful(p, d, F, C, c, b, rho)
check("Prop 6  condition p*delta*F >= (C-c) + beta*rho  <=>  exact removal optimal", ok)

# --- Proposition 7: optimal audit design (brute force over a grid) -----------------------------------
ok = True; worst = 0
for _ in range(25):
    a, e, H = rng.uniform(0.2, 3, 3); C, c, b, rho = rng.uniform(0, 1, 4); c = min(c, C); F_bar = rng.uniform(1.5, 4) + C
    out = sh.optimal_audit(a, e, H, C, c, b, rho, F_bar)
    th = out["theta"]
    if not out["deter_possible"]:
        continue
    ds = np.linspace(max(th, 1e-3), 1, 20001)          # p = theta/delta <= 1  <=>  delta >= theta
    f = a * th / ds + e * ds ** 2 / 2
    worst = max(worst, out["cost"] - f.min())
    ok &= out["delta"] >= th - 1e-12 and out["p"] <= 1 + 1e-12 and abs(out["p"] * out["delta"] - th) < 1e-12
    if out["delta"] < 1 and out["delta"] > th:                          # interior case closed forms
        ok &= abs(out["p"] - th ** (2 / 3) * (e / a) ** (1 / 3)) < 1e-9
        ok &= abs(out["cost"] - 1.5 * e ** (1 / 3) * (a * th) ** (2 / 3)) < 1e-9
check("Prop 7  closed-form (p*, delta*) attains the grid minimum", ok and worst < 1e-6, f"max excess {worst:.1e}")
o1 = sh.optimal_audit(1, 1, 99, .3, .1, .2, .5, 2.0); o2 = sh.optimal_audit(1, .1, 99, .3, .1, .2, .5, 2.0)
o3 = sh.optimal_audit(.1, 1, 99, .3, .1, .2, .5, 2.0)
check("Prop 7  cheaper tests (e down) -> more power, fewer audits; cheaper audits (a down) -> more frequency",
      o2["delta"] > o1["delta"] and o2["p"] < o1["p"] and o3["p"] > o1["p"])

# --- Proposition 8: penalty base ---------------------------------------------------------------------
ok = True
for _ in range(2000):
    p, d, k, phi, C, c, b = rng.uniform(0.05, 2, 7); c = min(c, C) * 0.2
    if not (p * d * k * phi > C - c):
        continue
    rD, rT = sh.tolerable_residue(p, d, k, phi, C, c, b, "developer"), sh.tolerable_residue(p, d, k, phi, C, c, b, "third")
    ok &= abs(rD - rT * b / (b + p * d * k)) < 1e-12 and rD < rT
    for r in (rD * 0.99, rD * 1.01, rT * 0.99, rT * 1.01):
        dev = sh.truthful(p, d, k * (phi - r), C, c, b, r); thr = sh.truthful(p, d, k * phi, C, c, b, r)
        ok &= dev == (r <= rD) and thr == (r <= rT)
check("Prop 8  tolerable residue: developer base = third-party base * beta/(beta + p*delta*k)", ok)

# --- report ------------------------------------------------------------------------------------------
w = max(len(r[0]) for r in results)
for name, ok, detail in results:
    print(f"{'PASS' if ok else 'FAIL'}  {name:<{w}}  {detail}")
bad = [r for r in results if not r[1]]
print(f"\n{len(results) - len(bad)}/{len(results)} checks passed")
sys.exit(1 if bad else 0)
