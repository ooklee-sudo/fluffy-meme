"""Asymptotics of the profit function Pi*(A) at the parity point A = 1  (no stakes grid: continuous lognormal).

kappa = a*b*f ~ lognormal (ln kappa ~ N(m, s^2)), c_H = 1.  Tool: rho = A*B/(c0+p).  Adopters (kappa):
  rho>1, A<1 : (1/rho, kappa*)  with  A*h(rho*kappa*) = h(kappa*);   rho>1, A>=1 : (1/rho, inf);
  rho<=1, A>1: (kappa_l, inf)   with  A*h(rho*kappa_l) = h(kappa_l).
Profit  pi = (p-k)/(B b) * E[ ln(rho*kappa) ; kappa in adopters ],  p = A*B/rho - c0.

Run: python3 kink_asymptotics.py
"""
import numpy as np
from scipy.optimize import brentq, minimize_scalar
from scipy.stats import norm

a, b, B, c0, k = 20.0, 0.12, 1.6, 0.8, 0.1
m, s = np.log(a * b * 2.0), 0.9               # ln kappa ~ N(m, s^2): stakes f lognormal(median 2, sigma 0.9)
A0 = 0.5


def h(x):
    return 0.0 if x <= 1 else 1 - (1 + np.log(x)) / x


def EY(y1, y2):
    """E[Y; y1<Y<y2] and P(y1<Y<y2) for Y ~ N(m, s^2)."""
    z1, z2 = (y1 - m) / s, (y2 - m) / s
    P = norm.cdf(z2) - norm.cdf(z1)
    return m * P + s * (norm.pdf(z1) - norm.pdf(z2)), P


def profit(A, rho):
    p = A * B / rho - c0
    if p <= k:
        return 0.0
    if rho > 1:
        lo = -np.log(rho)
        if A >= 1:
            hi = np.inf
        else:
            kap = brentq(lambda x: A * h(rho * x) - h(x), 1 + 1e-12, 1e9)
            hi = np.log(kap)
    else:
        if A <= 1:
            return 0.0
        kap = brentq(lambda x: A * h(rho * x) - h(x), 1.0 / rho, 1e12, xtol=1e-14) if A * h(rho * 1e12) - h(1e12) > 0 else np.inf   # Phi<0 on (1, 1/rho], so bracket from 1/rho
        lo, hi = np.log(kap), np.inf
    e, P = EY(lo, hi)
    return (p - k) / (B * b) * (e + np.log(rho) * P)


def Pi_star(A):
    rmax = A * B / (c0 + k)
    best = (0.0, None)
    for rho in np.concatenate([np.linspace(1 - 0.06, 1 - 1e-6, 120) if A > 1 else [], 1 + np.logspace(-7, np.log10(rmax - 1 - 1e-9), 600)]):
        v = profit(A, rho) if rho > 0 else 0.0
        if v > best[0]:
            best = (v, rho)
    return best


if __name__ == "__main__":
    # 1. closed form at A = 1 : price hugs the demand cliff rho = 1  (p = B - c0)
    e1, P1 = EY(0.0, np.inf)
    M = e1 / (B * b)
    print(f"closed form:  Pi*(1) = (B - c0 - k) * E[ln kappa; kappa>1] / (B b) = {(B - c0 - k) * M:.4f}")
    v, rho = Pi_star(1.0)
    print(f"  continuous numerical Pi*(1) = {v:.4f} at rho = {rho:.6f} (cliff is rho = 1); fine-grid value from the earlier run: 5.770")
    print(f"right derivative  D+ = B*M = E[ln kappa; kappa>1]/b = {B * M:.3f}   (fine-grid slopes 13.5-14.5)")
    for eta in (0.001, 0.004, 0.01, 0.02, 0.04):
        vA, rA = Pi_star(1 + eta)
        print(f"   A = 1+{eta:5.3f}: Pi* = {vA:.4f}  (hugging the cliff: {(( (1+eta)*B - c0 - k) * M):.4f}), optimal rho = {rA:.5f}, slope {(vA - v) / eta:6.2f}")
    # 2. left side
    print("\nleft side: loss Pi*(1) - Pi*(1-delta), exact (continuous) vs reduced model vs leading asymptotics")
    P = B - c0 - k
    def g(x): return np.log(x) / (x - 1 - np.log(x))
    def Ztail(kap): return EY(np.log(kap), np.inf)[0] / (B * b)
    print("  delta  | Pi*(1-delta) exact | loss exact | loss/delta | reduced-model loss/delta | B M exp(s sqrt(2 ln(1/delta))) | optimal eps, r=delta/eps, kappa*")
    for d in (0.1, 0.04, 0.02, 0.01, 0.004, 0.002, 0.001, 1e-4, 1e-5):
        vl, rl = Pi_star(1 - d)
        loss = v - vl
        eps = rl - 1
        def L(lr):
            r = np.exp(lr)
            kap = brentq(lambda x: g(x) - r, 1.0 + 1e-9, 1e12) if g(1e12) < r else 1e12
            return B * d * M * (1 + 1 / r) + P * Ztail(kap)
        rr = minimize_scalar(L, bounds=(np.log(1e-4), np.log(50)), method="bounded")
        r_opt = np.exp(rr.x)
        lead = B * M * np.exp(s * np.sqrt(2 * np.log(1 / d)))
        kap_star = brentq(lambda x: (1 - d) * h(rl * x) - h(x), 1 + 1e-12, 1e9)
        print(f"  {d:6.0e} | {vl:8.4f}           | {loss:8.4f}   | {loss / d:8.1f}   | {rr.fun / d:8.1f}                 | {lead:8.1f}                      | {eps:.5f}, {d / eps:.3f}, {kap_star:.1f}")
