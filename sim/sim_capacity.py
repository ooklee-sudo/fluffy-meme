"""Numerical check of Extension A (capacity-limited reviewers) and B (verification).

Per-task model (derailment only, alpha=0, mu known), threshold policy "hand off
when the error count N >= n at the start of a step":
  step cost k + c*e, e~Poisson(mu); finish w.p. q; if finished, pay F*pi_N
  with pi_N = 1-(1-theta)^N.
Per-task expected cost = A_n + P_n * H, with P_n = P(hand off), A_n = cost
excluding the hand-off cost, both computed exactly from a Markov chain.
"""
import math
import numpy as np

NINF = 150  # proxy for "never hand off"


def pois(mu, emax=40):
    p = np.array([math.exp(-mu) * mu**e / math.factorial(e) for e in range(emax + 1)])
    return p


def AP(n, k, c, mu, q, theta, F, emax=40):
    """Return (A_n, P_n)."""
    if n == 0:
        return 0.0, 1.0
    p = pois(mu, emax)
    pi = lambda N: 1 - (1 - theta) ** N
    T = np.zeros((n, n))
    bA = np.zeros(n)
    bP = np.zeros(n)
    for N in range(n):
        bA[N] = k + c * mu
        for e in range(emax + 1):
            M = N + e
            bA[N] += q * F * pi(M) * p[e]
            if M < n:
                T[N, M] += (1 - q) * p[e]
            else:
                bP[N] += (1 - q) * p[e]
    I = np.eye(n)
    A = np.linalg.solve(I - T, bA)[0]
    P = np.linalg.solve(I - T, bP)[0]
    return A, P


def closed_form_N(k, c, mu, q, theta, F, H):
    r = 1 - (q * H - k - c * mu) / (q * F)
    if q * H <= k + c * mu:
        return 0
    if r <= 0:
        return None
    rhs = r * math.exp(mu * theta)
    N = 0
    while (1 - theta) ** N > rhs:
        N += 1
    return N


def best_n(tab, H, nmax):
    costs = [tab[n][0] + tab[n][1] * H for n in range(nmax + 1)]
    return int(np.argmin(costs)), min(costs)


def build(k, c, mu, q, theta, F, nmax=25):
    tab = {n: AP(n, k, c, mu, q, theta, F) for n in range(nmax + 1)}
    tab[NINF] = AP(NINF, k, c, mu, q, theta, F)
    return tab


# ---------------------------------------------------------------- check 0
def check_closed_form():
    print("== Check 0: Markov chain vs closed form (Prop 6) ==")
    k, c, mu, q, H = 1, 5, 0.054, 0.06, 40
    bad = 0
    for theta in [0.05, 0.1, 0.18, 0.29, 0.4]:
        for F in [60, 100]:
            tab = build(k, c, mu, q, theta, F)
            nb, _ = best_n(tab, H, 25)
            # treat "never" as n=NINF
            cinf = tab[NINF][0]
            if cinf <= tab[nb][0] + tab[nb][1] * H + 1e-9:
                nb = "inf"
            cf = closed_form_N(k, c, mu, q, theta, F, H)
            ok = (cf == nb) or (cf is None and nb == "inf")
            bad += (not ok)
            print(f" theta={theta:4.2f} F={F:3d}  chain n*={nb}  closed form N*={cf}  {'OK' if ok else 'DIFF'}")
    print(" mismatches:", bad)


# ---------------------------------------------------------------- A
def cost_total(tab, n, Lam, s, h, d):
    A, P = tab[n]
    lam = Lam * P
    if lam >= s:
        return math.inf
    return A + P * (h + d / (s - lam))


def sys_opt(tab, Lam, s, h, d, nmax=25):
    cands = list(range(nmax + 1)) + [NINF]
    cs = [cost_total(tab, n, Lam, s, h, d) for n in cands]
    i = int(np.argmin(cs))
    return cands[i], cs[i]


def equilibria(tab, Lam, s, h, d, nmax=25):
    """n such that n is a best response to the average wait it itself induces."""
    cands = list(range(nmax + 1)) + [NINF]
    eq = []
    for n in cands:
        lam = Lam * tab[n][1]
        if lam >= s:
            continue
        H = h + d / (s - lam)
        costs = {m: tab[m][0] + tab[m][1] * H for m in cands}
        if costs[n] <= min(costs.values()) + 1e-12:
            eq.append(n)
    return eq


def check_A():
    print("\n== Extension A: capacity ==")
    k, c, mu, q = 1, 5, 0.054, 0.06
    h, d = 20.0, 10.0
    summary = []
    for (theta, F) in [(0.29, 60), (0.29, 100), (0.18, 100), (0.40, 100), (0.12, 100)]:
        tab = build(k, c, mu, q, theta, F)
        print(f"\n-- theta={theta}, F={F}; P_1={tab[1][1]:.3f} P_2={tab[2][1]:.3f} P_3={tab[3][1]:.3f}")
        print("  Lam    s | n_sys  n_eq(list) | cost_sys  cost_at_eq   over-escalation?")
        for s in [1.0]:
            for Lam in [0.5, 1, 2, 3, 4, 6]:
                ns, cs = sys_opt(tab, Lam, s, h, d)
                eq = equilibria(tab, Lam, s, h, d)
                ce = [cost_total(tab, n, Lam, s, h, d) for n in eq]
                flag = ""
                if eq:
                    # over-escalation = eq threshold lower than system optimum
                    flag = "eq<sys (over-escalates)" if min(eq) < ns else ("eq==sys" if ns in eq else "eq>sys")
                print(f"  {Lam:4.1f} {s:4.1f} |  {str(ns):>4}  {str(eq):>12} | {cs:8.3f}  {str(['%.3f'%x for x in ce]):>16}  {flag}")
                summary.append((theta, F, Lam, ns, eq))
    return summary


def check_A_monotone():
    print("\n-- n_sys vs load Lam (theta=0.29,F=100), fine grid --")
    k, c, mu, q = 1, 5, 0.054, 0.06
    h, d, s = 20.0, 10.0, 1.0
    tab = build(k, c, mu, q, 0.29, 100)
    prev = -1
    mono = True
    out = []
    for Lam in np.linspace(0.3, 8, 40):
        ns, _ = sys_opt(tab, Lam, s, h, d)
        out.append((round(Lam, 2), ns))
        v = NINF if ns == NINF else ns
        if v < prev:
            mono = False
        prev = v
    print(" ", out)
    print("  n_sys nondecreasing in load:", mono)


def value_vs_staffing():
    print("\n-- value of monitoring vs staffing s (theta=0.29, F=100, Lam=3) --")
    k, c, mu, q = 1, 5, 0.054, 0.06
    h, d, Lam = 20.0, 10.0, 3.0
    tab = build(k, c, mu, q, 0.29, 100)
    rows = []
    for s in [0.8, 0.9, 1.0, 1.2, 1.5, 2, 3, 5, 10, 30]:
        ns, cs = sys_opt(tab, Lam, s, h, d)
        stat = min(cost_total(tab, NINF, Lam, s, h, d), cost_total(tab, 0, Lam, s, h, d))
        rows.append((s, ns, stat - cs))
        print(f"  s={s:5.1f}  n_sys={str(ns):>4}  static_best={stat:8.3f}  sys_cost={cs:8.3f}  value={stat-cs:7.3f}")
    vals = [r[2] for r in rows]
    inc = any(vals[i + 1] > vals[i] + 1e-9 for i in range(len(vals) - 1))
    dec = any(vals[i + 1] < vals[i] - 1e-9 for i in range(len(vals) - 1))
    print("  value rises somewhere:", inc, "| falls somewhere:", dec, "-> nonmonotone:", inc and dec)


# ---------------------------------------------------------------- B
def check_B():
    print("\n== Extension B: verification quality d ==")
    k, c, mu, q, H, theta = 1, 5, 0.054, 0.06, 40, 0.29
    Fd, Fu = 30.0, 120.0
    prev = -1
    mono = True
    for dd in [0, 0.25, 0.5, 0.75, 1.0]:
        Feff = dd * Fd + (1 - dd) * Fu
        tab = build(k, c, mu, q, theta, Feff)
        nb, _ = best_n(tab, H, 25)
        if tab[NINF][0] <= tab[nb][0] + tab[nb][1] * H + 1e-9:
            nb = NINF
        cf = closed_form_N(k, c, mu, q, theta, Feff, H)
        print(f"  d={dd:4.2f}  F_eff={Feff:6.1f}  chain n*={'inf' if nb==NINF else nb}  closed form={cf}")
        v = 10**6 if nb == NINF else nb
        mono &= v >= prev
        prev = v
    print("  n* nondecreasing in d:", mono)


if __name__ == "__main__":
    check_closed_form()
    check_A()
    check_A_monotone()
    value_vs_staffing()
    check_B()
