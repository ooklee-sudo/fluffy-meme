"""Closed forms and checks for the heavy-tail case: S(e)=(1+theta e/k)^-k, linear cost c e.  (THEORY.md, P10-P12)

With Z = A lam s theta / c and eps = 1/(k+1):  (1+theta e*/k) = Z^eps,  R* = lam s Z^(-k eps)  (so elasticity eps),
  V(lam)  = (c/theta) [ (k+1) Z^eps - k ]                       developer cost
  W(lam)  = (c/theta) [ (k + 1/delta) Z^eps - k ]               social cost at the privately chosen effort
  WTP     = (c/theta)(1/eps) Q^eps [lam0^eps - lam^eps],  Q = A theta s / c      -> proportional to delta^eps
  psi     = social benefit of adoption / private WTP = (k + 1/delta)/(k + 1)
  L_k     = (c/theta)(ell lam s theta/c)^eps [ (k + 1/delta) delta^eps - (k + 1) ]   externality loss, proportional to lam^eps
  monopoly vs social quality with WTP_nu = nu G(lam), nu ~ U[0, nubar], K = K0/lam:  lam_M/lam_S = (2 psi)^(1/(1+eps))
"""
import numpy as np
from scipy.optimize import minimize_scalar

c, theta, k, s, ell = 1.0, 206.0, 0.63, 1.0, 20.0
eps = 1 / (k + 1)


def solve(lam, delta):
    A = delta * ell
    f = lambda u: c * u + A * lam * s * (1 + theta * u / k) ** (-k)
    grid = np.linspace(0, 3, 60001)
    u0 = grid[np.argmin(f(grid))]
    u = minimize_scalar(f, bounds=(max(0, u0 - 1e-3), u0 + 1e-3), method="bounded", options={"xatol": 1e-13}).x
    S = (1 + theta * u / k) ** (-k)
    return u, c * u + A * lam * s * S, c * u + ell * lam * s * S, lam * s * S


def closed(lam, delta):
    Z = delta * ell * lam * s * theta / c
    return (c / theta) * ((k + 1) * Z ** eps - k), (c / theta) * ((k + 1 / delta) * Z ** eps - k), lam * s * Z ** (-k * eps), Z


print(f"k={k}, eps=1/(k+1)={eps:.4f}")
print("\nV, W, residual density: numeric vs closed form")
for delta in (1.0, 0.5, 0.2):
    for lam in (0.5, 1.0):
        u, Vn, Wn, Rn = solve(lam, delta)
        Vc, Wc, Rc, Z = closed(lam, delta)
        print(f"  delta={delta} lam={lam}: V {Vn:.6f}/{Vc:.6f}  W {Wn:.6f}/{Wc:.6f}  R {Rn:.6f}/{Rc:.6f}  (Z={Z:.1f})")

print("\nWTP (lam0=1 -> lam=0.5): relative to delta=1 vs delta^eps; social benefit / WTP vs psi")
lam0, lam1 = 1.0, 0.5
wtp1 = None
for delta in (1.0, 0.7, 0.4, 0.2):
    wtp = solve(lam0, delta)[1] - solve(lam1, delta)[1]
    ben = solve(lam0, delta)[2] - solve(lam1, delta)[2]
    wtp1 = wtp if wtp1 is None else wtp1
    print(f"  delta={delta}: WTP/WTP(1)={wtp / wtp1:.4f}  delta^eps={delta ** eps:.4f}   "
          f"benefit/WTP={ben / wtp:.4f}  psi=(k+1/delta)/(k+1)={(k + 1 / delta) / (k + 1):.4f}")

print("\nExternality loss L_k(lam, delta) = W(lam; delta) - W(lam; 1) : numeric vs closed form, and scaling in lam")
for delta in (0.5, 0.2):
    for lam in (0.25, 0.5, 1.0):
        Ln = solve(lam, delta)[2] - solve(lam, 1.0)[2]
        Lc = (c / theta) * (ell * lam * s * theta / c) ** eps * ((k + 1 / delta) * delta ** eps - (k + 1))
        print(f"  delta={delta} lam={lam}: L numeric={Ln:.6f}  closed={Lc:.6f}")
Ls = [solve(l, 0.5)[2] - solve(l, 1.0)[2] for l in (0.25, 1.0)]
print(f"  log-log slope of L in lam (delta=0.5): {np.log(Ls[1] / Ls[0]) / np.log(4):.4f}   (eps = {eps:.4f})")

print("\nMonopoly vs social quality, nu ~ U[0, nubar], K=K0/lam, WTP_nu = nu G(lam), G = (lam0^eps - lam^eps)/eps; social benefit = psi * WTP")
N, nubar, K0, lam0 = 1.0, 1.0, 0.05, 3.0
for delta in (1.0, 0.5, 0.2):
    for kk in (0.51, 0.63, 0.78, 3.0, 50.0):
        e_ = 1 / (kk + 1)
        psi = (kk + 1 / delta) / (kk + 1)
        Gk = lambda l: (lam0 ** e_ - l ** e_) / e_   # normalised so that G -> ln(lam0/lam) as k -> infinity
        mon = minimize_scalar(lambda l: -(N * nubar * Gk(l) / 4 - K0 / l), bounds=(1e-4, lam0 - 1e-6), method="bounded", options={"xatol": 1e-12}).x
        soc = minimize_scalar(lambda l: -(psi * N * nubar * Gk(l) / 2 - K0 / l), bounds=(1e-4, lam0 - 1e-6), method="bounded", options={"xatol": 1e-12}).x
        print(f"  delta={delta} k={kk:5.2f}: lam_M/lam_S numeric={mon / soc:.4f}  formula (2 psi)^(1/(1+eps))={(2 * psi) ** (1 / (1 + e_)):.4f}")
