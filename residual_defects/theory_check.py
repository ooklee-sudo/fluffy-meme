"""Numerical checks of the propositions in THEORY.md (baseline: S(e)=exp(-theta e), C(e)=c e, size s).

P2  marginal value of quality is c/(theta lam), the same privately, socially and at first best (no dependence on A)
P2b deadweight loss of the externality L(delta) = (c/theta)(1/delta - 1 + ln delta), independent of lam
P3  with lam known to the developer the vendor's warranty payout does not depend on lam
P4  with beliefs lam_hat(lam) the payout elasticity in lam is 1 - rho, rho = d ln lam_hat / d ln lam
P5  lemons fixed point with a gamma pool
C1  simulated Gamma-Poisson learning: elasticity of E[R | lam] in lam
"""
import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import gammaincc, gamma as gamma_fn

c, theta, s, ell = 1.0, 0.8, 1.0, 50.0


def dev_opt(lam, delta, lam_hat=None):
    """Developer picks e using belief lam_hat (default: the true lam); returns e, residual density at the true lam."""
    A = delta * ell
    lh = lam if lam_hat is None else lam_hat
    f = lambda e: c * e + A * lh * s * np.exp(-theta * e)
    e = minimize_scalar(f, bounds=(0, 60), method="bounded", options={"xatol": 1e-12}).x
    return e, lam * s * np.exp(-theta * e)


def V(lam, delta):
    e, _ = dev_opt(lam, delta)
    return c * e + delta * ell * lam * s * np.exp(-theta * e)


def W(lam, delta):  # social cost at the privately chosen e
    e, R = dev_opt(lam, delta)
    return c * e + ell * R


def dnum(fun, x, h=1e-4):
    return (fun(x * (1 + h)) - fun(x * (1 - h))) / (2 * x * h)


print("P2  marginal value of quality dV/dlam, dW/dlam vs c/(theta lam)")
for delta in (1.0, 0.7, 0.4):
    for lam in (0.5, 2.0):
        print(f"  delta={delta} lam={lam}: dV={dnum(lambda x: V(x, delta), lam):.5f} "
              f"dW={dnum(lambda x: W(x, delta), lam):.5f}  c/(theta lam)={c / (theta * lam):.5f}")

print("\nP2b deadweight loss W(lam, delta) - W(lam, 1) vs (c/theta)(1/delta - 1 + ln delta)")
for delta in (0.7, 0.4, 0.2):
    for lam in (0.5, 2.0):
        print(f"  delta={delta} lam={lam}: numeric={W(lam, delta) - W(lam, 1.0):.5f}  "
              f"formula={(c / theta) * (1 / delta - 1 + np.log(delta)):.5f}")

print("\nP3  warranty payout phi_v*l*E[R] with lam known (phi=0.2, phi_v=0.3 => delta=0.5)")
for lam in (0.3, 1.0, 3.0):
    _, R = dev_opt(lam, 0.5)
    print(f"  lam={lam}: E[R]={R:.5f}  payout={0.3 * ell * R:.5f}  formula phi_v c/(delta theta)={0.3 * c / (0.5 * theta):.5f}")

print("\nP4  payout elasticity in lam under belief lam_hat = lam0 (lam/lam0)^rho  (expect 1 - rho)")
lam0 = 1.0
for rho in (0.0, 0.3, 0.7, 1.0):
    def R_of(l):
        return dev_opt(l, 0.5, lam_hat=lam0 * (l / lam0) ** rho)[1]
    print(f"  rho={rho}: numeric elasticity={np.log(R_of(1.5) / R_of(1.0)) / np.log(1.5):.4f}  expected={1 - rho:.4f}")

print("\nP5  lemons: types lam ~ Gamma(2, rate 2) (mean 1), outside option lam0=3, cost k(lam)=kappa*max(0,1-lam/4)")
a, b, lam_out = 2.0, 2.0, 3.0


def tail_mean(x):  # E[lam | lam >= x] for Gamma(a, rate b)
    return (a / b) * gammaincc(a + 1, b * x) / gammaincc(a, b * x)


def G(x, kappa):
    return (c / theta) * np.log(lam_out / tail_mean(x)) - kappa * max(0.0, 1 - x / 4.0)


xs = np.linspace(1e-6, 6, 60001)
for kappa in (0.8, 1.2, 1.6, 2.0, 3.0):
    g = np.array([G(x, kappa) for x in xs])
    roots = xs[:-1][np.sign(g[:-1]) != np.sign(g[1:])]
    full = G(1e-6, kappa) >= 0
    desc = "full participation" if full else ""
    for r in roots:
        share = gammaincc(a, b * r)
        desc += f" threshold x={r:.3f} (types lam<x exit; participating share={share:.2f}, pool mean={tail_mean(r):.2f})"
    print(f"  kappa={kappa}: WTP(all)={(c / theta) * np.log(lam_out / 1.0):.3f}  {desc or 'market collapses (no x with G>=0)'}")

print("\nC1  Gamma-Poisson learning simulation: elasticity of E[R_tau | lam] in lam (1 - rho_hat)")
rng = np.random.default_rng(1)
A, alpha, beta0, n = 35.0, 2.0, 1.0, 30000
rstar = c / (A * theta)
lam = rng.gamma(alpha, 1 / beta0, n)
N = rng.poisson(lam * s)
T = [np.sort(rng.exponential(1 / theta, k)) for k in N]


def stop(times, r):
    tp = 0.0
    for d in range(len(times) + 1):
        tn = times[d] if d < len(times) else np.inf
        Sp = np.exp(-theta * tp)
        if s * Sp * (alpha + d) / (beta0 + s * (1 - Sp)) <= r:
            return tp
        Ss = r * (beta0 + s) / (s * (alpha + d + r))
        ts = -np.log(Ss) / theta
        if ts < tn:
            return ts
        tp = tn
    return tp


tau = np.array([stop(T[i], rstar) for i in range(n)])
Rtau = np.array([(T[i] > tau[i]).sum() for i in range(n)])
edges = np.quantile(lam, np.linspace(0, 1, 11))
xm, ym = [], []
for i in range(10):
    m = (lam >= edges[i]) & (lam <= edges[i + 1])
    xm.append(lam[m].mean()); ym.append(Rtau[m].mean())
slope = np.polyfit(np.log(xm), np.log(ym), 1)[0]
print(f"  decile means of lam: {np.round(xm, 2)}")
print(f"  decile E[R_tau|lam]: {np.round(ym, 4)}")
print(f"  log-log slope = {slope:.3f}  (0 = full offsetting, 1 = none)  => implied belief responsiveness rho_hat = {1 - slope:.3f}")
print(f"  unconditional E[R_tau]={Rtau.mean():.4f} vs r*={rstar:.4f}")
