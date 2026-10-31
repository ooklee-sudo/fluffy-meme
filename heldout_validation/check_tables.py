"""Independent recomputation of Tables 1-4, 6 and 7 of the manuscript and numerical checks of Propositions 4 and 5.
Prints OK/MISMATCH against the numbers printed in the manuscript. Run: python check_tables.py"""
import numpy as np
from scipy import stats, special

A = 0.95
kp = lambda l: int(stats.poisson.ppf(A, l)) if l > 0 else 0


def kmix(l, c):
    if c == 0: return kp(l)
    r = 1 / c ** 2; return int(stats.nbinom.ppf(A, r, r / (r + l)))


def exc(l, c, k):
    if c == 0: return stats.poisson.sf(k, l)
    r = 1 / c ** 2; return stats.nbinom.sf(k, r, r / (r + l))


def eshort(l, k, c=0):
    ks = np.arange(0, int(l * 10 + 400))
    pm = stats.poisson.pmf(ks, l) if c == 0 else stats.nbinom.pmf(ks, 1 / c ** 2, (1 / c ** 2) / (1 / c ** 2 + l))
    return float(np.sum(np.maximum(ks - k, 0) * pm))


bad = 0
def chk(name, got, want):
    global bad
    ok = got == want; bad += not ok
    print(("OK       " if ok else "MISMATCH ") + name, got, "" if ok else f"(manuscript: {want})")

# Table 1 (selected rows)
for l, c, kpois, kmx, pe in ((10, .3, 15, 18, 11.0), (10, .5, 15, 21, 16.4), (25, .3, 33, 41, 16.7), (25, .5, 33, 50, 23.0)):
    chk(f"T1 lam={l} c={c}", (kp(l), kmix(l, c), round(100 * exc(l, c, kp(l)), 1)), (kpois, kmx, pe))
# Table 2/3
chk("T2 k* indep N=1..4", [kp(10 * .37 ** n) for n in range(1, 5)], [7, 4, 2, 1])
f0 = [150 * kp(10 * .37 ** n) + 25 * n for n in range(8)]; f1 = [150 * max(1, kp(10 * .37 ** n)) + 25 * n for n in range(8)]
chk("T3 totals k_min=0", f0, [2250, 1075, 650, 375, 250, 275, 150, 175]); chk("T3 argmin", (int(np.argmin(f0)), int(np.argmin(f1))), (6, 4))
# Table 4
chk("T4 N* k_min=0", [int(np.argmin([ch * kp(10 * .37 ** n) + 25 * n for n in range(13)])) for ch in (25, 50, 100, 150, 300, 600, 1200)], [3, 4, 6, 6, 6, 6, 6])
# Table 6
for l, c, w in ((10, .3, (18, 15, 10, 3070, 9.4, 117)), (120.7, .44, (221, 139, 120, 38669, 65.3, 114))):
    cost = lambda k: 150 * k + 3000 * eshort(l, k, c)
    kt = kmix(l, c); opt = cost(kt)
    chk(f"T6 lam={l} c={c}", (kt, kp(l), int(l), round(opt), round(100 * (cost(kp(l)) / opt - 1), 1), round(100 * (cost(int(l)) / opt - 1))), w)
# Table 7
for N, w in ((2, (4, 650, 2462)), (3, (2, 351, 5823)), (4, (1, 200, 8324))):
    lam_n = 10 * .37 ** N; k = kp(lam_n)
    chk(f"T7 N={N}", (k, round(150 * k + 3000 * eshort(lam_n, k)), round(150 * k + 3000 * eshort(3.7, k))), w)
# Proposition 4(b): exact identity
rng = np.random.default_rng(1); err = 0
for _ in range(2000):
    c1, c2 = rng.uniform(.05, .95, 2); p11 = rng.uniform(max(0, c1 + c2 - 1), min(c1, c2))
    phi = (p11 - c1 * c2) / np.sqrt(c1 * (1 - c1) * c2 * (1 - c2)); none = 1 - c1 - c2 + p11
    err = max(err, abs(none / ((1 - c1) * (1 - c2)) - (1 + phi * np.sqrt(c1 * c2 / ((1 - c1) * (1 - c2))))))
print("Prop 4(b) identity, max abs error over 2000 random draws:", err); bad += err > 1e-9
# Proposition 4(c): closed form vs Monte Carlo, monotone in rho
c, rho, N = .63, .2, 3; s = (1 - rho) / rho; th = rng.beta(c * s, (1 - c) * s, 2_000_000)
cf = float(np.exp(special.betaln(c * s, (1 - c) * s + N) - special.betaln(c * s, (1 - c) * s)))
print("Prop 4(c) closed form vs Monte Carlo:", round(cf, 4), round(float(np.mean((1 - th) ** N)), 4)); bad += abs(cf - np.mean((1 - th) ** N)) > 2e-3
# Proposition 5(b): optimum sits at the first N of its capacity level (random instances)
import random; random.seed(0); viol = 0
for _ in range(3000):
    l0 = random.uniform(1, 60); cc = random.uniform(.2, .8); ch = random.uniform(20, 400); g = random.uniform(5, 80); km = random.choice([0, 1, 2])
    K = [max(km, kp(l0 * (1 - cc) ** n)) for n in range(25)]; f = [ch * K[n] + g * n for n in range(25)]; n = int(np.argmin(f))
    viol += n > 0 and K[n] == K[n - 1]
print("Prop 5(b) violations:", viol); bad += viol
print("ALL CHECKS PASSED" if bad == 0 else f"{int(bad)} PROBLEM(S)")
