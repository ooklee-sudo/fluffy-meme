"""Follow-up: (1) allow randomized thresholds so a decentralized equilibrium always exists,
(2) test over-escalation (P_eq >= P_sys) and its cost, (3) robustness of non-monotone value in staffing."""
import math, itertools
import numpy as np
from sim_capacity import build, NINF

k, c, mu, q = 1, 5, 0.054, 0.06

def frontier(tab, nmax=25):
    """Randomization = convex hull of achievable (P, A). Return lower-left hull points."""
    pts = [(tab[n][1], tab[n][0], n) for n in list(range(nmax + 1)) + [NINF]]
    pts.sort()
    return pts

def cost_mix(P, A, Lam, s, h, d):
    lam = Lam * P
    return math.inf if lam >= s else A + P * (h + d / (s - lam))

def best_over_grid(tab, Lam, s, h, d, nmax=25, fine=60, avgwait=None):
    """Search policies mixing adjacent thresholds (n, n+1) with weight x.
    avgwait=None -> system optimum (true cost); else decentralized best response to H=h+d*avgwait."""
    best = (math.inf, None, None)
    ns = list(range(nmax)) + []
    cands = []
    for n in range(nmax):
        for x in np.linspace(0, 1, fine + 1):
            A = (1 - x) * tab[n][0] + x * tab[n + 1][0]
            P = (1 - x) * tab[n][1] + x * tab[n + 1][1]
            cands.append((A, P))
    cands.append(tab[NINF])
    for A, P in cands:
        cst = cost_mix(P, A, Lam, s, h, d) if avgwait is None else A + P * (h + d * avgwait)
        if cst < best[0]:
            best = (cst, A, P)
    return best

def decentralized(tab, Lam, s, h, d, tol=1e-6):
    """Fixed point P = P(best response to wait induced by P), found by bisection on P."""
    cands = []
    for n in range(25):
        for x in np.linspace(0, 1, 61):
            cands.append(((1-x)*tab[n][0]+x*tab[n+1][0], (1-x)*tab[n][1]+x*tab[n+1][1]))
    cands.append(tab[NINF])
    def br_P(P):
        lam = Lam * P
        if lam >= s: return 0.0
        H = h + d / (s - lam)
        return min(cands, key=lambda ap: ap[0] + ap[1] * H)[1]
    lo, hi = 0.0, min(1.0, 0.999 * s / Lam)
    # g(P)=br_P(P)-P is decreasing (higher P -> higher wait -> lower br_P)
    for _ in range(80):
        mid = (lo + hi) / 2
        if br_P(mid) > mid: lo = mid
        else: hi = mid
    P = (lo + hi) / 2
    A = min(cands, key=lambda ap: abs(ap[1] - P))[0]
    # recover A on the frontier for this P
    H = h + d / (s - Lam * P)
    Ab, Pb = min(cands, key=lambda ap: ap[0] + ap[1] * H)
    return Pb, Ab

h, d, s = 20.0, 10.0, 1.0
print("== Over-escalation with randomized thresholds (decentralized vs system optimum) ==")
print(" theta   F   Lam |  P_sys   P_dec  | cost_sys  cost_dec  loss%  | over-escalates?")
tot = ok = 0
for theta, F in [(0.29, 60), (0.29, 100), (0.18, 100), (0.40, 100), (0.12, 100), (0.05, 100)]:
    tab = build(k, c, mu, q, theta, F)
    for Lam in [0.5, 1, 2, 3, 4, 6]:
        cs, As, Ps = best_over_grid(tab, Lam, s, h, d)
        Pd, Ad = decentralized(tab, Lam, s, h, d)
        cd = cost_mix(Pd, Ad, Lam, s, h, d)
        over = Pd >= Ps - 1e-4
        tot += 1; ok += over
        print(f" {theta:4.2f} {F:4d} {Lam:4.1f} | {Ps:6.3f}  {Pd:6.3f} | {cs:8.3f} {cd:8.3f} {100*(cd-cs)/cs:5.2f} | {'yes' if over else 'NO'}")
print(f" over-escalation (P_dec >= P_sys) in {ok}/{tot} cells")

print("\n== Robustness: is value of monitoring single-peaked in staffing s? ==")
def value_curve(theta, F, Lam, h, d, ss):
    tab = build(k, c, mu, q, theta, F)
    out = []
    for s_ in ss:
        cs, _, _ = best_over_grid(tab, Lam, s_, h, d, fine=30)
        stat = min(cost_mix(tab[NINF][1], tab[NINF][0], Lam, s_, h, d), cost_mix(1.0, 0.0, Lam, s_, h, d))
        out.append(max(stat - cs, 0.0))
    return out
ss = [0.6, 0.8, 1, 1.5, 2, 3, 4, 6, 10, 20, 50]
nm = tot2 = 0
for theta, F, Lam, hh, dd in itertools.product([0.12, 0.29, 0.4], [60, 100], [1.0, 3.0], [10.0, 20.0], [5.0, 10.0]):
    v = value_curve(theta, F, Lam, hh, dd, ss)
    peak = int(np.argmax(v))
    interior = 0 < peak < len(v) - 1 and v[peak] > 1e-6
    tot2 += 1; nm += interior
print(f" interior peak in staffing for {nm}/{tot2} parameter configurations")
v = value_curve(0.29, 100, 3.0, 20.0, 10.0, ss)
print(" example curve:", [(s_, round(x, 2)) for s_, x in zip(ss, v)])
