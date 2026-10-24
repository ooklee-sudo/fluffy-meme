"""Numerical checks for the vendor stage (THEORY.md, P7-P9).

P7  separability: developer willingness to pay kappa*ln(lam0/lam) does not depend on the liability share delta (baseline);
    outside the baseline (heavy-tailed detection) it does - quantified here.
P8  monopoly with kappa ~ U[0, kbar] and fixed quality cost K0/lam: lam_monopoly = 2 * lam_social.
P9  two-type warranty signalling: cheapest separating warranty ratio w* = ln r / r^(1-rho), r = lam_L/lam_H.
"""
import numpy as np
from scipy.optimize import brentq, minimize_scalar

c, theta, s, ell = 1.0, 0.8, 1.0, 50.0
kappa = c / theta


def dev_opt(lam, delta, lam_hat=None):
    A = delta * ell
    lh = lam if lam_hat is None else lam_hat
    e = minimize_scalar(lambda e: c * e + A * lh * s * np.exp(-theta * e), bounds=(0, 80), method="bounded",
                        options={"xatol": 1e-12}).x
    return e, lam * s * np.exp(-theta * e)


def V(lam, delta):
    e, _ = dev_opt(lam, delta)
    return c * e + delta * ell * lam * s * np.exp(-theta * e)


print("P7  baseline: WTP = V(lam0) - V(lam) across liability shares delta  (formula kappa ln(lam0/lam))")
lam0, lam = 3.0, 1.0
for delta in (1.0, 0.7, 0.4, 0.2):
    print(f"  delta={delta}: WTP={V(lam0, delta) - V(lam, delta):.6f}   formula={kappa * np.log(lam0 / lam):.6f}")

print("\nP7  heavy tail S=(1+th u/k)^-k, th=206, k=0.63 (data fit, u = fraction of the suite), cost c*u:")
th_h, k_h, c_h, As_ref = 206.0, 0.63, 1.0, 20.0   # As_ref = ell*s; delta scales it


def V_heavy(lam, delta):
    A = delta * As_ref
    f = lambda u: c_h * u + A * lam * (1 + th_h * u / k_h) ** (-k_h)
    grid = np.linspace(0, 3, 30001)
    u0 = grid[np.argmin(f(grid))]
    r = minimize_scalar(f, bounds=(max(0, u0 - 1e-3), u0 + 1e-3), method="bounded", options={"xatol": 1e-12})
    return r.fun, r.x


base = None
for delta in (1.0, 0.7, 0.4, 0.2):
    w = V_heavy(1.0, delta)[0] - V_heavy(0.5, delta)[0]
    base = w if base is None else base
    print(f"  delta={delta}: WTP(1.0 -> 0.5)={w:.5f}   relative to delta=1: {w / base:.3f}   e*(lam=0.5)={V_heavy(0.5, delta)[1]:.3f}")

print("\nP8  monopoly vs social quality, kappa ~ U[0, kbar], fixed cost K0/lam, N buyers, lam0 = 3")
N, kbar, K0, lam0 = 1.0, 1.0, 0.3, 3.0
g = lambda l: np.log(lam0 / l)
mon = minimize_scalar(lambda l: -(N * kbar * g(l) / 4 - K0 / l), bounds=(0.05, 2.9), method="bounded", options={"xatol": 1e-10})
soc = minimize_scalar(lambda l: -(N * kbar * g(l) / 2 - K0 / l), bounds=(0.05, 2.9), method="bounded", options={"xatol": 1e-10})
print(f"  lam_monopoly={mon.x:.5f} (formula 4K0/(N kbar) = {4 * K0 / (N * kbar):.5f});  "
      f"lam_social={soc.x:.5f} (formula 2K0/(N kbar) = {2 * K0 / (N * kbar):.5f});  ratio={mon.x / soc.x:.4f}")
for name, l, mult in (("monopoly", mon.x, 1 / 4), ("social", soc.x, 1 / 2)):
    pass
welf = lambda l: N * kbar * g(l) / 2 - K0 / l
print(f"  surplus at social quality={welf(soc.x):.5f}; at monopoly quality (all served)={welf(mon.x):.5f}; "
      f"monopoly pricing also excludes types kappa < p/g = kbar/2: extra loss N*kbar*g/8 = {N * kbar * g(mon.x) / 8:.5f}")

print("\nP9  cheapest separating warranty ratio w = phi_v / delta' (two types, lam_L = r lam_H); delta0 = 0.6")
lam0, delta0, lamH = 3.0, 0.6, 0.5
for rho in (0.0, 0.5, 0.8):
    for r in (1.5, np.e, 5.0, 10.0):
        lamL = r * lamH
        pH, pL = kappa * np.log(lam0 / lamH), kappa * np.log(lam0 / lamL)
        lam_hat = lamH ** (1 - rho) * lamL ** rho   # developer partly learns the true (worse) type

        def gap(w):
            d = delta0 / (1 + w)                       # developer's share after the vendor takes phi_v = w d
            Rm = dev_opt(lamL, d, lam_hat)[1]
            return pH - w * d * ell * Rm - pL          # mimicking profit minus honest profit of the L type
        w_num = brentq(gap, 1e-9, 50)
        print(f"  rho={rho} r={r:5.2f}: w*(numeric)={w_num:.5f}  formula ln r / r^(1-rho)={np.log(r) / r ** (1 - rho):.5f}"
              f"  H's gain from separating={kappa * (np.log(r) - w_num):.4f}")
