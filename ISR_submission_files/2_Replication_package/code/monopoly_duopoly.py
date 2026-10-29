"""Sections 5 to 7.4: monopoly owner (Tables 5 and 7), symmetric duopoly (one-third rule numbers) and the asymmetric
duopoly profile of Numerical Finding 1 (Figure 4). All with the paper's baseline parameters.

  python code/monopoly_duopoly.py
"""
import math

import numpy as np
from scipy.optimize import brentq, minimize_scalar

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from real_options import Params, beta

RHO, CN, VBAR, B, PSI, C, THETA, N = 0.10, 1.0, 40.0, 7.0, 6.0, 2.0, 0.5, 1.0
G, SIGMA = 0.20, 0.40


# ---------------- monopoly (uniform values on [0, VBAR])
def Em_static(mu, R):
    k = CN / ((1 - R) * VBAR)
    return mu * CN / RHO * (1 - k * (RHO + mu) / 2)


def v_dynamic(mu, R):
    be = beta(Params(rho=RHO, mu=mu, g=G, sigma=SIGMA, C_N=CN))
    return be / (be - 1) * CN * (RHO + mu - G) / (1 - R)


def Em_dynamic(mu, R):
    vh = min(v_dynamic(mu, R), VBAR)
    return ((1 - R) * mu / (RHO * (RHO + mu)) * vh ** 2 / 2 + mu * CN / RHO * (VBAR - vh)) / VBAR


def optimum(R, theta, Em):
    f = lambda m: -(PSI * m - C * m * m / 2 + theta * N * (B * m - Em(m, R)))
    return minimize_scalar(f, bounds=(1e-3, 8), method="bounded", options={"xatol": 1e-10}).x


def dEm(mu, R, h=1e-6):
    return (Em_static(mu + h, R) - Em_static(mu - h, R)) / (2 * h)


def mu_duopoly_symmetric(R, H=10.0):
    F = lambda mu: H / (4 * mu) + (N / 3) * (B - dEm(mu, R)) - C * mu
    return brentq(F, 0.05, 5)


# ---------------- asymmetric duopoly (Numerical Finding 1)
Z_, ETA = 0.1, 10.0
V = np.linspace(0, VBAR, 2001)
W = np.ones_like(V); W[0] = W[-1] = 0.5; W /= W.sum()


def surplus(mu, R):
    vh = CN * (RHO + mu) / (1 - R)
    return B * mu - np.where(V >= vh, mu * CN / RHO, (1 - R) * V * mu / (RHO * (RHO + mu)))


def price_equilibrium(s1, s2, iters=400):
    p = np.array([ETA, ETA])
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        for _ in range(iters):
            ph1 = 1 / (1 + np.exp(np.clip(((s2 - p[1]) - (s1 - p[0])) / ETA, -50, 50)))
            D1, D2, X = (W * ph1).sum(), (W * (1 - ph1)).sum(), (W * ph1 * (1 - ph1)).sum()
            p = 0.5 * p + 0.5 * np.array([ETA * D1 / X, ETA * D2 / X])
    return p, ph1, (D1, D2)


def payoffs(a1, a2, H):
    (m1, R1), (m2, R2) = a1, a2
    p, ph1, (D1, D2) = price_equilibrium(surplus(m1, R1), surplus(m2, R2))
    Z = lambda R: Z_ * R * R / (1 - R)
    return (p[0] * D1 + H * m1 / (m1 + m2) - C * m1 ** 2 / 2 - Z(R1),
            p[1] * D2 + H * m2 / (m1 + m2) - C * m2 ** 2 / 2 - Z(R2), p, ph1)


def asymmetric_check(H=20.0, a1=(2.50, 0.96), a2=(1.38, 0.08), grid_mu=np.linspace(0.2, 4, 39), grid_R=np.linspace(0, 0.98, 50)):
    P1, P2, p, ph1 = payoffs(a1, a2, H)
    br1 = max(payoffs((m, r), a2, H)[0] for m in grid_mu for r in grid_R)
    br2 = max(payoffs(a1, (m, r), H)[1] for m in grid_mu for r in grid_R)
    mean_v = ((W * ph1 * V).sum() / (W * ph1).sum(), (W * (1 - ph1) * V).sum() / (W * (1 - ph1)).sum())
    return dict(payoffs=(P1, P2), best_response_payoffs=(br1, br2), prices=tuple(p), mean_value=mean_v, phi=ph1)


if __name__ == "__main__":
    print("Table 5 / Table 7 (static and dynamic-threshold proxy)")
    print(f"{'R':>4}{'muV static':>12}{'muV dyn':>10}{'muP static':>12}{'muP dyn':>10}")
    for R in (0.3, 0.5, 0.7, 0.8):
        print(f"{R:>4}{optimum(R, THETA, Em_static):>12.3f}{optimum(R, THETA, Em_dynamic):>10.3f}"
              f"{optimum(R, 1.0, Em_static):>12.3f}{optimum(R, 1.0, Em_dynamic):>10.3f}")
    print("\nSymmetric duopoly mu* (H = 10): " + ", ".join(f"R={R}: {mu_duopoly_symmetric(R):.3f}" for R in (0.3, 0.5, 0.7, 0.8)))
    a = asymmetric_check()
    print("\nAsymmetric profile at H = 20:  (mu,R) = (2.50,0.96) vs (1.38,0.08)")
    print(f"  payoffs {a['payoffs'][0]:.2f}, {a['payoffs'][1]:.2f}; best-response payoffs on the grid {a['best_response_payoffs'][0]:.2f}, {a['best_response_payoffs'][1]:.2f}")
    print(f"  prices {a['prices'][0]:.1f}, {a['prices'][1]:.1f}; mean adapter value of choosers {a['mean_value'][0]:.1f}, {a['mean_value'][1]:.1f}")
