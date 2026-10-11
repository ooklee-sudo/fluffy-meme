"""Numerical checks for the Online Appendix: Result 4 (debt traps), Result 8 (learning), and the general-form versions of Results 5-7."""
import numpy as np
from math import erf, sqrt, log, exp
ok = True
def check(name, got, want, tol):
    global ok; good = abs(got - want) <= tol; ok &= good
    print(f"{'PASS' if good else 'FAIL'}  {name}: got {got:.4f}, expected {want:.4f}")

# ======================================================= Result 4
_erf = np.vectorize(erf)
Phi = lambda x: 0.5 * (1 + _erf(np.asarray(x, float) / sqrt(2)))
n, p, alpha, r0, gamma, mu, Rm, s, delta, v, lam = 1, 0.9, 0.0, 0.3, 3.0, 0.5, 1.0, 0.25, 1.0, 1.0, 1.0
qq = 0.5; A = n * qq * (1 - (1 - alpha) * p); C = n * qq * (1 - alpha) * p
def F(x): return Phi(np.log(np.maximum(x, 1e-300) / Rm) / s)
def inflow(H, beta): return A + C * F(lam * v * r0 * (1 + gamma * H) / (beta * delta))
Hs = np.linspace(0, 3, 600001)
def zeros(beta):
    g = inflow(Hs, beta) - mu * Hs; idx = np.where(np.sign(g[:-1]) != np.sign(g[1:]))[0]
    return Hs[idx], np.sign(g[idx]), g
# monotone map property: T(H) = (1-mu) H + I(H) is nondecreasing, so g' > -mu and stability iff g' < 0
T = (1 - mu) * Hs + inflow(Hs, 0.75); check("Result 4: map T(H) is nondecreasing", float(np.all(np.diff(T) >= -1e-12)), 1.0, 0)
# exact bistable interval vs union of (beta_1(eps), beta_2(eps))
def b1(e): z = float(-np.sqrt(2) * 0 + 0); 
from statistics import NormalDist
nd = NormalDist()
def b12(e):
    z = nd.inv_cdf(1 - e)
    lo = lam * v * r0 * (1 + gamma * (A + C * e) / mu) / (delta * Rm * exp(-s * z))
    hi = lam * v * r0 * (1 + gamma * (A + C * (1 - e)) / mu) / (delta * Rm * exp(s * z))
    return lo, hi, z
eps = np.linspace(0.001, 0.499, 499); ivs = [(b12(e)[0], b12(e)[1], e) for e in eps if b12(e)[0] < b12(e)[1]]
union_lo, union_hi = min(i[0] for i in ivs), max(i[1] for i in ivs)
bist = [b for b in np.linspace(0.3, 1, 1401) if len(zeros(b)[0]) >= 3]
check("Result 4: lower edge of exact bistable region = min over eps of beta_1", union_lo, min(bist), 0.002)
check("Result 4: upper edge of exact bistable region = max over eps of beta_2", union_hi, max(bist), 0.002)
w = max(ivs, key=lambda i: i[1] - i[0]); check("Result 4: widest single interval at eps ~ 0.14", w[2], 0.14, 0.02)
check("Result 4: widest single interval lower edge 0.659", w[0], 0.659, 0.002); check("Result 4: widest single interval upper edge 0.829", w[1], 0.829, 0.002)
# sufficient condition: for beta strictly inside (beta_1, beta_2) there are three steady states with signs +,-,+,- pattern
beta_test = 0.5 * (w[0] + w[1]); zs, sg, g = zeros(beta_test)
check("Result 4: three steady states inside (beta_1, beta_2)", float(len(zs)), 3.0, 0)
check("Result 4: sign pattern of g around the zeros is (+,-,+) crossing: -, +, -", float(list(sg) == [1.0, -1.0, 1.0]), 1.0, 0)
H_L, H_T = (A + C * w[2]) / mu, (A + C * (1 - w[2])) / mu
check("Result 4: low state <= (A+C eps)/mu", float(zs[0] <= H_L + 1e-9), 1.0, 0); check("Result 4: trap >= (A+C(1-eps))/mu", float(zs[2] >= H_T - 1e-9), 1.0, 0)
# hysteresis: path as beta falls then rises
def simulate_path(betas, H0, T_each=4000):
    H = H0; out = []
    for b in betas:
        for _ in range(T_each): H = (1 - mu) * H + float(inflow(H, b))
        out.append(H)
    return np.array(out)
down = np.linspace(1.0, 0.3, 71); up = down[::-1]
hd = simulate_path(down, 0.1); hu = simulate_path(up, hd[-1])
tip_down = down[np.argmax(hd > 0.5)]; tip_up = up[np.argmax(hu < 0.5)]
print(f"  hysteresis: tips into the trap at beta = {tip_down:.3f} (falling), leaves it at beta = {tip_up:.3f} (rising)")
check("Result 4: tipping point when beta falls ~ 0.646", tip_down, 0.646, 0.011); check("Result 4: exit point when beta rises ~ 0.843", tip_up, 0.843, 0.011)
check("Result 4: hysteresis width positive", float(tip_up > tip_down), 1.0, 0)

# ======================================================= Result 8
q, kappa, kmin, K, B, eta, phi_noticing, v8 = 0.5, 0.1, 0.05, 0.6, 1.0, 0.5, 0.6, 1.0
notice = eta * phi_noticing
def s_insp(qh):                                     # inspection time ~ U[kmin, K]
    x = qh * (1 - notice) * B / v8
    return 0.0 if x <= kmin else min(1.0, (x - kmin) / (K - kmin))
qc = v8 * kmin / ((1 - notice) * B); print(f"  threshold belief q_c = {qc:.4f}")
def step(qh, theta, force=False):
    sI = 1.0 if force else s_insp(qh); return qh + kappa * (sI + theta * (1 - sI)) * (q - qh)
# (b) self-confirming
qh = 0.05
for _ in range(500): qh = step(qh, 0.0)
check("Result 8(b): theta=0, q0 <= q_c: belief never moves", qh, 0.05, 1e-12)
# (a) theta>0 converges; q0>q_c converges
qh = 0.05
for _ in range(2000): qh = step(qh, 0.02)
check("Result 8(a): theta>0 converges to q", qh, q, 1e-3)
qh = 0.08
for _ in range(2000): qh = step(qh, 0.0)
check("Result 8(a): theta=0, q0>q_c converges to q", qh, q, 1e-3)
# (c) mandate of T periods: removes the wedge iff (1-kappa)^T (q-q0) < q - q_c
q0 = 0.05
for Tm in (1, 2, 5, 8, 12):
    qh = q0
    for _ in range(Tm): qh = step(qh, 0.0, force=True)
    for _ in range(3000): qh = step(qh, 0.0)
    predicted = (1 - kappa)**Tm * (q - q0) < q - qc
    print(f"  T={Tm}: converged to q? {abs(qh-q)<1e-3}; condition says {predicted}")
    check(f"Result 8(c): mandate of T={Tm} periods removes the wedge iff the condition holds", float(abs(qh - q) < 1e-3), float(predicted), 0)
qh = q0; qh = step(qh, 0.0, force=True); check("Figure 4 text: one mandatory period moves q_hat from 0.05 to ~0.095", qh, 0.095, 0.001)

# ======================================================= Results 5-7, general forms
rng = np.random.default_rng(4)
def general(beta, ph, la, c_cost, psi, k_dist, nR=4001, eps=0.005, v=1.0, delta=1.0, q=0.5, eta=0.5, r=0.4, a0=0.8):
    z = np.linspace(-6, 6, nR); wR = np.exp(-z**2 / 2); wR /= wR.sum(); R = 1.0 * np.exp(0.5 * z)     # heterogeneous lognormal rework costs
    Dp = ph * q * (1 - eta * ph) * np.maximum(0, beta * delta * R - la * v * r)
    D = q * (1 - eta * ph) * (delta * R - v * r)
    G, M = k_dist                                       # G(x) = P(k <= x), M(x) = int_0^x k dG
    x = Dp / v
    Wp = (Dp * G(x) - v * M(x)); WO = (D * G(x) - v * M(x))
    Wp, WO = float((wR * Wp).sum()), float((wR * WO).sum())
    f = np.linspace(0, 1, 100001)
    J = c_cost(f) - psi(f) * Wp; CO = c_cost(f) - psi(f) * WO
    fD, fO = f[np.argmin(J)], f[np.argmin(CO)]
    # Result 7 general: developer complies iff J(f) - J(fD) <= eps; organisation picks the best compliant f
    comp = (J - J.min()) <= eps + 1e-15; f7 = f[comp][np.argmin(CO[comp])]
    fbar = f[comp].max(); return Wp, WO, fD, fO, f7, fbar
expo = (lambda x: 1 - np.exp(-x / 0.3), lambda x: 0.3 - (x + 0.3) * np.exp(-x / 0.3))              # exponential inspection time, mean 0.3
unif = (lambda x: np.minimum(1, x / 0.6), lambda x: np.where(x < 0.6, x**2 / (2 * 0.6), 0.6 / 2))   # uniform on [0, 0.6]
for nm, ccost in (("quadratic", lambda f: 0.15 * f**2 / 2), ("cubic", lambda f: 0.4 * f**3), ("exp", lambda f: 0.05 * (np.exp(2 * f) - 1))):
    for pm, psi in (("linear", lambda f: 0.8 * f), ("concave", lambda f: 0.8 * (1 - (1 - f)**2))):
        for dn, kd in (("exponential", expo), ("uniform", unif)):
            Wp, WO, fD, fO, f7, fbar = general(0.5, 0.6, 1.2, ccost, psi, kd)
            Wp1, WO1, fD1, fO1, _, _ = general(1.0, 1.0, 1.0, ccost, psi, kd)
            good = (WO >= Wp - 1e-12) and (fO >= fD - 1e-9) and abs(fO1 - fD1) < 1e-9 and (f7 <= fO + 1e-9) and (f7 >= fD - 1e-9) and abs(f7 - min(fO, fbar)) < 2e-5
            ok &= good
            print(f"{'PASS' if good else 'FAIL'}  cost={nm:9s} default={pm:8s} inspection={dn:11s}: W_O={WO:.4f}>=W_p={Wp:.4f}; f_D={fD:.3f} <= f_O={fO:.3f}; no wedge: f_O-f_D={fO1-fD1:.1e}; bypass: f={f7:.3f}=min(f_O, fbar={fbar:.3f})")
print("\nALL APPENDIX CHECKS PASSED" if ok else "\nSOME APPENDIX CHECKS FAILED")
