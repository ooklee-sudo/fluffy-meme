"""Numerical checks of the propositions in THEORY.md against the simulation in ../sim.py.
usage: python research_program/theory_check.py   (run from llm_realoptions/)
"""
import sys, math
sys.path.insert(0, ".")
import numpy as np
from sim import run, RATIOS, LIFE, WEEK, R_MONTH, H, disc

rng = np.random.default_rng(3)

# Proposition 2: E[min(R1,R2)] = E[R] - E|R1-R2|/2 for iid draws
R = RATIOS
mean_R = R.mean(); gini_md = np.abs(R[:, None] - R[None, :]).mean()
emp_min = np.minimum(R[:, None], R[None, :]).mean()
print(f"P2 identity: E[min]={emp_min:.4f}  E[R]-G/2={mean_R - gini_md / 2:.4f}  (E[R]={mean_R:.3f}, G={gini_md:.3f})")
for c in (0.0, 0.5, 1.0):
    print(f"   c={c}: per-event price multiplier flex={mean_R - (1 - c) * gini_md / 2:.3f} vs rigid={mean_R:.3f}  ratio={(mean_R - (1 - c) * gini_md / 2) / mean_R:.3f}")

# Proposition 1: break-even premium from effort alone. Analytic: (1-phi) * E[K] * E[sum of discounted migration dates]
n = 20000
K_mean = (2 + 4 + 10) / 3                                   # weeks, triangular mean
S = np.zeros(n); cnt = np.zeros(n)
for i in range(n):
    t = rng.choice(LIFE) * rng.uniform(0.2, 1.0)
    while t < H:
        S[i] += disc(int(t)); cnt[i] += 1; t += rng.choice(LIFE) * rng.uniform(0.2, 1.0)
lam = cnt.mean() / H
a_cont = (1 - math.exp(-R_MONTH * H)) / R_MONTH
print(f"P1: mean retirements {cnt.mean():.2f}; E[sum disc]={S.mean():.2f}; Poisson approx lam*a(H)={lam * a_cont:.2f}")
for phi in (0.3, 0.5, 0.8):
    analytic = (1 - phi) * K_mean * S.mean()
    o = run(n, succ_ratio=1.0, phi=phi, premium_w=0.0, emerg=1.0, outage_day=0.0, seed=11)
    sim = ((o["rigid"] - o["flex"]) / WEEK).mean()
    print(f"   phi={phi}: break-even premium analytic {analytic:.2f} weeks, simulated (no emergency surcharge, no outage) {sim:.2f}")

# Proposition 3: switching trigger with renewal. Cost vs theta.
print("P3: mean PV cost (USD) by trigger multiple theta, sigma=0.10, base case, 8000 lifecycles; theta=0 means never switch early")
for th in (0.5, 1.0, 1.5, 2.1, 3.0, 5.0, 10.0):
    o = run(8000, theta_override=th, seed=5)
    print(f"   theta={th:>4}: cost {o['flex_ro'].mean():,.0f}  early switches {o['sw_flex_ro'].mean():.2f}")
o = run(8000, seed=5); print(f"   never switch early: cost {o['flex'].mean():,.0f}")
