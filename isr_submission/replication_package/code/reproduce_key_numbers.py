"""Recompute the headline numbers cited in the manuscript and compare with the reported values.

Run from this directory:  python3 reproduce_key_numbers.py        (about 1-3 minutes, no downloads needed)
Prints one line per number: computed value, reported value, OK/MISMATCH.
"""
import sys
import numpy as np
from scipy.optimize import brentq
import kink_asymptotics as K
import vendor_model as VM

A0, B, c0, k, a, b = K.A0, 1.6, 0.8, 0.1, 20.0, 0.12
rows = []


def check(name, got, want, tol):
    ok = abs(got - want) <= tol
    rows.append(ok)
    print(f"{'OK      ' if ok else 'MISMATCH'} {name:58s} computed {got:10.4f}   reported {want:10.4f}")


# --- Table 1: guaranteed exclusion threshold  (1-A) a f - (1+ln(a b f))/b = tau
def fbar(A, tau):
    g = lambda f: (1 - A) * a * f - (1 + np.log(a * b * f)) / b - tau
    return brentq(g, 1.0 / (a * b) * 1.0001 + 1e-9, 1e6) if g(1e6) > 0 else np.nan
# the function is not monotone near its minimum; take the largest root
def fbar_largest(A, tau):
    fs = np.exp(np.linspace(np.log(0.05), np.log(1e5), 400001))
    v = (1 - A) * a * fs - (1 + np.log(a * b * fs)) / b - tau
    idx = np.where(v <= 0)[0]
    i = idx[-1]
    return brentq(lambda f: (1 - A) * a * f - (1 + np.log(a * b * f)) / b - tau, fs[i], fs[i + 1])

for A, tau, want in ((0.5, 0, 2.2), (0.8, 0, 8.3), (0.9, 0, 20.4), (0.95, 0, 47.9), (0.99, 0, 318.3),
                     (0.9, 50, 49.0), (0.99, 200, 1379.4)):
    check(f"Table 1: f-bar at A={A}, tau={tau}", fbar_largest(A, tau), want, 0.06 * max(1, want / 100))

# --- Proposition 7/8: closed forms at parity
P = B - c0 - k
EYp = K.EY(0.0, 12.0) if False else None
sigma, m = 0.9, np.log(4.8)
from scipy.stats import norm
# E[ln kappa; kappa>1] for lognormal(m, sigma): m*Phi(m/s) + s*phi(m/s)
Eln = m * norm.cdf(m / sigma) + sigma * norm.pdf(m / sigma)
M = Eln / (B * b)
check("Pi*(1) = P*M", P * M, 5.7729, 5e-4)
check("Right derivative B*M = E[ln kappa; kappa>1]/b", B * M, 13.195, 5e-3)
theta_hat = 2 * P * M / (1 - A0) ** 2
check("theta-hat = 2PM/(1-A0)^2", theta_hat, 46.18, 5e-3)
check("local lower bound BM/(1-A0)", B * M / (1 - A0), 26.39, 5e-3)
check("entry threshold A_e = (c0+k)/B", (c0 + k) / B, 0.5625, 1e-6)
check("condition Q: E[ln k | k>1] - (1-(c0+k)/B)  (>0)", Eln / norm.cdf(m / sigma) - (1 - (c0 + k) / B), 1.651 - 0.4375, 2e-3)
check("condition Q': B(1+A0) - 2(c0+k)  (>0)", B * (1 + A0) - 2 * (c0 + k), 0.6, 1e-9)

# --- numerical continuous-model values
check("Pi*(1) from numerical optimization", K.Pi_star(1.0)[0], 5.7729, 5e-3)
th = max(K.Pi_star(A)[0] / ((A - A0) ** 2 / 2) for A in np.linspace(0.8, 1.2, 81))
check("max of Pi*(A)/c(A) on a grid (=theta-hat)", th, 46.18, 0.3)

# --- Section 6: price/profit at A = 0.9 and 1.0 (grid-based vendor model)
ps = np.linspace(0.0, 1.5, 751)
prof = lambda A: np.array([VM.profit(p, A=A)[0] for p in ps])
p9, p10 = prof(0.9), prof(1.0)
check("Profit at A=0.9 (linear price)", p9.max(), 1.037, 0.05)
check("Profit at A=1.0 (linear price)", p10.max(), 5.74, 0.1)
check("Profit ratio A=1.0 / A=0.9", p10.max() / p9.max(), 5.5, 0.3)
check("Optimal price at A=1.0", ps[p10.argmax()], 0.80, 0.03)

# --- Proposition 4: lambda* at A=0.9 (from the interval at the optimal price)
p_opt = ps[p9.argmax()]
lo, hi, _ = VM.interval(p_opt, A=0.9)
print(f"          adoption interval of f at A=0.9, price {p_opt:.2f}: ({lo:.3f}, {hi:.3f})")

print(f"\n{sum(rows)}/{len(rows)} checks passed")
sys.exit(0 if all(rows) else 1)
