"""Verification for Appendix F: equilibrium conditions against unilateral deviations, expected judge score by simulation, and the
no-exploitation threshold beta_d. Run: python multitask_check.py"""
import numpy as np
import endogenous_exploit as E
from multitask_explore import equilibria, beta_d
MN = E.MN
p = dict(sig=1.0, Delta=1.0, kappa=4.0, psi=1.0, theta=0.7, g=1.0, rho_s=0.6, d=2.0, cs=0.01, cG=0.05)
def U(a, e, N, phi, beta):
    Q = 1 - (1 - e) ** N
    J = (p['theta'] * a + p['sig'] * MN[N]) * (1 - Q * phi) + Q * (1 - phi) * p['Delta']
    return beta * J - p['psi'] / 2 * a ** 2 - N * p['kappa'] / 2 * e ** 2
# 1. unilateral-deviation check on grids
for N, phi, beta in ((4, 0.4, 0.5), (4, 0.0, 1.0), (4, 0.4, 1.1)):
    for e, a in equilibria(N, phi, beta, p):
        ag = np.linspace(0, 3, 6001); eg = np.linspace(0, 1, 6001)
        ba = ag[int(np.argmax([U(x, e, N, phi, beta) for x in ag]))]; be = eg[int(np.argmax([U(a, x, N, phi, beta) for x in eg]))]
        print(f"N={N} phi={phi} beta={beta}: eq (e={e}, a={a}); best a given e = {ba:.3f}; best e given a = {be:.4f}")
# 2. simulation of the expected judge score of what ships
rng = np.random.default_rng(3); N, e, a, phi, reps = 6, 0.07, 0.4, 0.4, 1_000_000
top = rng.normal(size=(reps, N)).max(axis=1) * p['sig'] + p['theta'] * a
ex = (rng.random((reps, N)) < e).any(axis=1); det = rng.random(reps) < phi
J = np.where(ex, np.where(det, 0.0, top + p['Delta']), top)
Q = 1 - (1 - e) ** N
print("E[J ship] simulation", round(J.mean(), 4), " formula", round((p['theta'] * a + p['sig'] * MN[N]) * (1 - Q * phi) + Q * (1 - phi) * p['Delta'], 4))
# 3. no-exploitation threshold
for N, phi in ((4, 0.4), (4, 0.2), (8, 0.4)):
    bd = beta_d(N, phi, p); print(f"N={N} phi={phi}: beta_d={bd:.3f}")
    for b in (0.9 * bd, 1.02 * bd):
        eq = equilibria(N, phi, b, p); print(f"   beta={b:.3f}: equilibria (e,a)={eq}")
# 4. e as a function of beta, N=4, with and without inspection
for phi in (0.0, 0.4):
    print(f"phi={phi}: ", [(b, equilibria(4, phi, b, p)[0][0]) for b in (0.1, 0.3, 0.5, 0.7, 0.9, 1.1)])
