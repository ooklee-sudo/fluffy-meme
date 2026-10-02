"""Check of Proposition 3: optimal switching band between two vendors when the cost gap is an arithmetic Brownian motion.
Holding the vendor with saving flow s (the other vendor's cost minus mine, per month), s ~ ABM(0, sigma^2); switching costs K and maps s -> -s.
Theory: switch when s reaches -b, with b solving kappa*b - tanh(kappa*b) = kappa*r*K/2, kappa = sqrt(2r)/sigma. NPV rule: b_npv = r*K/2.
Small-band approximation: b ~ (3*K*sigma^2/4)^(1/3).
usage: python research_program/band_check.py
"""
import math
import numpy as np
from scipy.optimize import brentq

r = 0.10 / 12      # monthly discount rate
K = 20000.0        # switching cost, USD
sigma = 1000.0     # USD per month per sqrt(month)
kappa = math.sqrt(2 * r) / sigma
f = lambda x: x - math.tanh(x) - kappa * r * K / 2
x = brentq(f, 1e-9, 50); b_star = x / kappa
b_npv = r * K / 2; b_approx = (3 * K * sigma ** 2 / 4) ** (1 / 3)
print(f"theory: b* = {b_star:,.0f} USD/month; NPV band r*K/2 = {b_npv:,.0f}; cube-root approximation {b_approx:,.0f}")

# simulation: value of band policy b, infinite-horizon PV approximated by T months, start at s = 0 holding vendor 1
rng = np.random.default_rng(1)
dt = 0.1; T = 900.0; n_paths = 3000; steps = int(T / dt)
def pv(b):
    s = np.zeros(n_paths); tot = np.zeros(n_paths); nsw = np.zeros(n_paths)
    for k in range(steps):
        t = k * dt; d = math.exp(-r * t)
        tot += d * s * dt
        s += sigma * math.sqrt(dt) * rng.standard_normal(n_paths)
        hit = s <= -b
        if hit.any():
            tot[hit] -= d * K; s[hit] = -s[hit]; nsw += hit
    return tot.mean(), nsw.mean() / T * 12
print("band b (USD/month) | mean PV payoff (USD) | switches per year")
for b in (b_npv, 0.5 * b_star, b_star, 1.5 * b_star, 2.5 * b_star):
    seed_state = rng.bit_generator.state
    p, sw = pv(b); print(f"{b:>10,.0f} {'(NPV)' if b == b_npv else ('(b*)' if b == b_star else ''):6} | {p:>12,.0f} | {sw:6.2f}")
