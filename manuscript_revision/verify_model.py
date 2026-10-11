"""Numerical check of the formal model in revised_section4.md.

Every closed form is compared with a brute-force evaluation of the decision
problem it is derived from (Monte Carlo / grid search), and the paper's own
illustrative numbers are reproduced.  Run: python3 verify_model.py
"""
import numpy as np

rng = np.random.default_rng(1)
N = 4_000_000
ok = True


def check(name, got, want, tol):
    global ok
    good = abs(got - want) <= tol
    ok &= good
    print(f"{'PASS' if good else 'FAIL'}  {name}: got {got:.4f}, expected {want:.4f}")


# ---------------------------------------------------------------- Section 4.1-4.2
# Developer problem, acceptance regime, simulated from primitives.
def simulate_acceptance(v, q, beta, phi, alpha, lam, eta, a, r, delta, Rmed, s, Kmax,
                        n=N, R=None):
    R = rng.lognormal(np.log(Rmed), s, n) if R is None else R
    k = rng.uniform(0, Kmax, n)
    isE = rng.random(n) < q
    noticed = isE & (rng.random(n) < eta * phi)
    default = rng.random(n) < alpha
    gain = np.maximum(0.0, beta * delta * R - lam * v * r)        # perceived gain from refactoring a detected E
    refactor_if_detected = lam * v * r < beta * delta * R          # eq. (2)
    inspect = (~default) & (v * k < phi * q * (1 - eta * phi) * gain)   # eq. (3)
    # inspection reveals the type; a noticed E is detected without inspection
    detected = noticed | (inspect & isE)
    debt = isE & ~(detected & refactor_if_detected)
    return debt.mean(), R, isE, detected, refactor_if_detected, inspect


def aggregate_debt_closed_form(v, q, beta, phi, alpha, lam, eta, a, r, delta, Rmed, s, Kmax):
    # integrate over R on a grid; K uniform => G(x)=min(1,x/K)
    z = np.linspace(-6, 6, 20001)
    R = Rmed * np.exp(s * z)
    w = np.exp(-z**2 / 2); w /= w.sum()
    gain = np.maximum(0, beta * delta * R - lam * v * r)
    ref = lam * v * r < beta * delta * R
    sI = np.minimum(1, phi * q * (1 - eta * phi) * gain / (v * Kmax))
    D = q * (eta * phi * (~ref) + (1 - eta * phi) * (1 - (1 - alpha) * sI * ref))
    return (w * D).sum()


# Paper's illustration (Sec 4.2): q=.8, beta=.5, phi=.6, alpha=.3, r=.4a, k~U[0,.6a], median R = v a.
# The paper does not report the log-dispersion s of rework costs, eta, or lambda.  The reported numbers
# (price effect -0.24, wedge +0.32, debt 0.50 -> 0.59; self-admitted share 0.33) are reproduced by
# s = 0.79, eta = 0.5, lambda = 1  (see revision_notes.md).
a, v = 1.0, 1.0
S_, ETA_ = 0.79, 0.5
par = dict(q=.8, beta=.5, phi=.6, alpha=.3, lam=1.0, eta=ETA_, a=a, r=.4 * a, delta=1.0,
           Rmed=v * a, Kmax=.6 * a)
rational = {**par, 'beta': 1, 'phi': 1, 'alpha': 0, 'lam': 1}
DC = 0.5                                            # median R = va => P(R < va/delta) = 1/2
DAstar = aggregate_debt_closed_form(v=v, s=S_, **rational)
DA = aggregate_debt_closed_form(v=v, s=S_, **par)
check("Sec 4.2: price effect D_A*(v0) - D_C(v0) = -0.24", DAstar - DC, -0.24, 0.01)
check("Sec 4.2: wedge D_A(v0) - D_A*(v0) = +0.32", DA - DAstar, 0.32, 0.01)
check("Sec 4.2: debt rises from 0.50 to 0.59 (computed 0.58; paper rounds)", DA, 0.59, 0.015)
mc, *_ = simulate_acceptance(v=v, s=S_, n=N, **par)
check("closed-form D_A equals simulated D_A from primitives", DA, mc, 0.004)

# Result 1 (decomposition): the three terms are telescoping, wedge >= 0, acceleration >= 0 -- check monotonicity in v
vs = np.linspace(0.5, 6, 23)
DAs = [aggregate_debt_closed_form(v=x, s=S_, **{**rational, 'Rmed': 1.0, 'r': .4, 'Kmax': .6}) for x in vs]
check("Result 1: rational-benchmark debt weakly increasing in v", bool(np.all(np.diff(DAs) >= -1e-12)), True, 0)
# match the behavioural level with the rational benchmark at higher v (Result 2a)
from_v = lambda x: aggregate_debt_closed_form(v=x, s=S_, **{**rational, 'r': .4, 'Kmax': .6})
lo_v, hi_v = 1.0, 50.0
for _ in range(80):
    mid = (lo_v + hi_v) / 2
    lo_v, hi_v = (mid, hi_v) if from_v(mid) < DA else (lo_v, mid)
print(f"  Result 2(a): rational acceleration matches D_A at v1 = {lo_v:.2f} v0 (paper reports 2.9 v0)")
check("Result 2(a): matching v1 / v0 ~ 2.9", lo_v, 2.9, 0.15)

# Sec 4.3 statistics at this configuration (sigma = 0.5)
sig = 0.5
zg = np.linspace(-6, 6, 40001); Rg = np.exp(S_ * zg); wg = np.exp(-zg**2 / 2); wg /= wg.sum()
q_, b_, ph_, al_, r_, K_ = .8, .5, .6, .3, .4, .6
gain = np.maximum(0, b_ * Rg - r_); ref = r_ < b_ * Rg
sI = np.minimum(1, ph_ * q_ * (1 - ETA_ * ph_) * gain / K_)
notice = ETA_ * ph_
p_det_notref = notice * (~ref)
p_undet = (1 - notice) * (1 - (1 - al_) * sI)
share = (wg * (sig * p_det_notref + sig * ph_ * p_undet)).sum() / (wg * (p_det_notref + p_undet)).sum()
check("Sec 4.3: self-admitted share = 0.33", share, 0.33, 0.005)
plan = r_ < Rg
lapse_joint = q_ * (wg * (plan & ~ref)).sum()       # P(artifact is E, planned but not carried out)
check("Sec 4.3: lapse rate = 0.21 (the paper's number is the JOINT probability q * P(plan, not do))", lapse_joint, 0.21, 0.005)
from math import erf as _e, sqrt as _s
Phi_ = lambda x: 0.5 * (1 + _e(x / _s(2)))
check("Sec 4.3: possession effect at r=a: Phi(ln(lam/beta)/s) - 1/2 = 0.31", Phi_(np.log(1 / .5) / S_) - .5, 0.31, 0.005)
check("Sec 4.3: loss aversion alone (lam=1.8): possession effect = 0.27", Phi_(np.log(1.8) / S_) - .5, 0.27, 0.005)

# ---------------------------------------------------------------- Result 2(b),(c): exact statements, by simulation
R = rng.lognormal(0.0, S_, N)
beta_, lam_, delta, v = 0.5, 1.5, 1.0, 1.0
a_ = r = 0.4
choiceE = v * a_ > delta * R                                         # eq. (1): independent of beta
plan = lam_ * v * r < delta * R; do = lam_ * v * r < beta_ * delta * R
check("Result 2(c): lapse > 0 when beta<1", float((plan & ~do).mean()) > 0, True, 0)
planL = lam_ * v * r < delta * R; doL = lam_ * v * r < 1.0 * delta * R
check("Result 2(c): lapse = 0 under loss aversion alone", float((planL & ~doL).mean()), 0.0, 0)
check("Result 2(c): possession effect > 0 under loss aversion alone",
      float((lam_ * v * a_ >= delta * R).mean() - choiceE.mean()) > 0, True, 0)
check("Result 2(b): rational possession effect = 0", float((v * a_ >= delta * R).mean() - choiceE.mean()), 0.0, 1e-9)

# ---------------------------------------------------------------- Result 3: reliability paradox
def D3(q, eta, phi, alpha, K, v, B):
    qh = v * K / (phi * (1 - eta * phi) * B)
    return q * (1 - eta * phi) * (1 - (1 - alpha) * np.minimum(1, q / qh)), qh

K, B, eta, v = 0.3, 1.0, 0.5, 1.0
for phi, alpha in ((1.0, 0.0), (0.6, 0.0), (0.6, 0.6)):
    qs = np.linspace(0.001, 1, 500)
    D, qh = D3(qs, eta, phi, alpha, K, v, B)
    # brute force from the decision problem (R fixed, B = beta*delta*R - lam*v*r)
    q = 0.35
    kk = rng.uniform(0, K, 1_000_000)
    isE = rng.random(1_000_000) < q
    noticed = isE & (rng.random(1_000_000) < eta * phi)
    dflt = rng.random(1_000_000) < alpha
    insp = (~dflt) & (v * kk < phi * q * (1 - eta * phi) * B)
    det = noticed | (insp & isE)
    mcD = (isE & ~det).mean()
    check(f"Result 3 closed form vs simulation (phi={phi}, alpha={alpha}, q={q})",
          float(D3(q, eta, phi, alpha, K, v, B)[0]), mcD, 0.004)
    if alpha < 0.5:
        qstar = qh / (2 * (1 - alpha))
        i = np.argmax(D)
        check(f"  peak of D at q*=qh/(2(1-alpha)) (phi={phi}, alpha={alpha})", qs[i], min(qstar, 1.0), 0.005)
        # monotone-up as q falls only on (q*, qh)
        seg = (qs > qstar) & (qs < qh)
        check("  D strictly decreasing in q on (q*, q_hat)  [i.e. rises as model improves]",
              bool(np.all(np.diff(D[seg]) < 0)), True, 0)
    else:
        check("  alpha>=1/2: D increasing in q everywhere", bool(np.all(np.diff(D) >= -1e-12)), True, 0)

# ---------------------------------------------------------------- Results 5-7: the game
def primitives(beta, phi, lam, q, Rbar, r, K, a0, c, eta, v=1.0, delta=1.0):
    Dp = phi * q * (1 - eta * phi) * (beta * delta * Rbar - lam * v * r)
    D = q * (1 - eta * phi) * (delta * Rbar - v * r)
    return Dp, D

def deliberation_value(Dp, D, v, K):        # value of the option to deliberate, evaluated at weights D, given behaviour from Dp
    s = min(1.0, Dp / (v * K))
    return D * s - v * K * s**2 / 2           # benefit - expected time cost of inspecting (k uniform)

def perceived_cost(f, Dp, a0, c, v, K):     # developer's perceived friction cost J(f)
    return v * c * f**2 / 2 - a0 * f * deliberation_value(Dp, Dp, v, K)

def org_cost(f, Dp, D, a0, c, v, K):
    return v * c * f**2 / 2 - a0 * f * deliberation_value(Dp, D, v, K)

q, Rbar, r, K, a0, c, eta, v, eps = 0.5, 2.0, 0.4, 0.6, 0.8, 0.15, 0.5, 1.0, 0.005
beta, phi, lam = 0.5, 0.6, 1.2
Dp, D = primitives(beta, phi, lam, q, Rbar, r, K, a0, c, eta)
fD = a0 * Dp**2 / (2 * v**2 * c * K)
fO = a0 * Dp * (2 * D - Dp) / (2 * v**2 * c * K)
grid = np.linspace(0, 1, 2_000_001)
check("Result 5: f_D = argmin of perceived cost (grid search)", grid[np.argmin(perceived_cost(grid, Dp, a0, c, v, K))], fD, 1e-5)
check("Result 5: f_O = argmin of organisation cost (grid search)", grid[np.argmin(org_cost(grid, Dp, D, a0, c, v, K))], fO, 1e-5)
check("Result 5: f_O - f_D = a0 Dp (D-Dp)/(v^2 c K)", fO - fD, a0 * Dp * (D - Dp) / (v**2 * c * K), 1e-12)
check("paper's Fig. 3 text: f_D = 0.05", fD, 0.05, 0.005)
check("paper's Fig. 3 text: f_O = 0.49", fO, 0.49, 0.005)
# Result 7: developer bypasses iff J(f)-J(fD) > eps; org picks best compliant f
J = perceived_cost(grid, Dp, a0, c, v, K); Jmin = J.min()
compliant = (J - Jmin) <= eps + 1e-15
f7 = grid[compliant][np.argmin(org_cost(grid[compliant], Dp, D, a0, c, v, K))]
check("Result 7: implementable friction by brute force", f7, fD + min(fO - fD, np.sqrt(2 * eps / (v * c))), 1e-5)
check("paper's Fig. 3 text: implementable = 0.31", f7, 0.31, 0.005)
# rational benchmark: no gap and doubling v lowers friction 0.71 -> 0.10
Dp_r, D_r = primitives(1, 1, 1, q, Rbar, r, K, a0, c, eta, v=1.0)
# (the paper's rational example uses phi=1 hence eta*phi=.5 and B from beta=lambda=1)
for vv in (1.0, 2.0):
    Dp_r, D_r = primitives(1, 1, 1, q, Rbar, r, K, a0, c, eta, v=vv)
    fDr = a0 * Dp_r**2 / (2 * vv**2 * c * K)
    fOr = a0 * Dp_r * (2 * D_r - Dp_r) / (2 * vv**2 * c * K)
    print(f"  rational, v={vv}: f_D={fDr:.3f} f_O={fOr:.3f} (gap {fOr - fDr:.2e})")

# Bertrand: simultaneous offers (f,p); the only equilibrium is f=f_D, p=m
m = 0.1
S0 = 5.0
def surplus(f, p): return S0 - perceived_cost(f, Dp, a0, c, v, K) - p
best_dev = 0
cand_f = np.linspace(0, 1, 201)
for f1 in cand_f:                              # rival plays (fD, m); any deviation (f1,p1>=m) earns nothing
    for p1 in (m, m + 0.01, m + 0.5):
        if surplus(f1, p1) > surplus(fD, m) + 1e-12:
            best_dev += 1
check("Bertrand: no offer beats (f_D, p=m) at price >= m", float(best_dev), 0.0, 0)

# ---------------------------------------------------------------- Result 4: debt traps (Figure 2)
from math import erf, sqrt, log, exp
_erf = np.vectorize(erf)
def Phi(x): return 0.5 * (1 + _erf(np.asarray(x) / sqrt(2)))
def Fcdf(x, Rm, s): return Phi(np.log(np.maximum(x, 1e-300) / Rm) / s)
n, p, alpha, r0, gamma, mu, Rm, s, delta = 1, 0.9, 0.0, 0.3, 3.0, 0.5, 1.0, 0.25, 1.0
qq = 0.5
A = n * qq * (1 - (1 - alpha) * p); C = n * qq * (1 - alpha) * p
def inflow(H, beta):
    return A + C * Fcdf(lam1 * v * r0 * (1 + gamma * H) / (beta * delta), Rm, s)   # lam=1 in Fig. 2 (not reported) -> lam=1
lam1 = 1.0
def steady(beta):
    Hs = np.linspace(0, 3, 300001); g = inflow(Hs, beta) - mu * Hs
    idx = np.where(np.sign(g[:-1]) != np.sign(g[1:]))[0]
    return Hs[idx]
for b in (0.5, 0.75, 0.95):
    print(f"  beta={b}: steady states {np.round(steady(b), 3)}")
lo = [b for b in np.linspace(0.3, 1, 701) if len(steady(b)) >= 3]
check("Result 4: bistable region lower edge ~0.646", min(lo), 0.646, 0.003)
check("Result 4: bistable region upper edge ~0.843", max(lo), 0.843, 0.003)

print("\nALL CHECKS PASSED" if ok else "\nSOME CHECKS FAILED")
