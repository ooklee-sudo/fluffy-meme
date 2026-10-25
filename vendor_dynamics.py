"""Extensions of the endogenous-reach model: (1) two vendors investing simultaneously, (2) learning from usage,
(3) private reach with liability as the commitment device.

Common set-up (see ai_vendor_investment.md): human technology (a,b,c_H=1); AI tool with reach A, speed B*b, firm cost c0
+ usage price p; stakes f ~ lognormal; vendor cost k per unit; investment cost I(A) = (theta/2)(A - A0)^2, A0 = 0.5.
A coarse stakes grid (4000 points) is used for speed; the checks at the top confirm the earlier numbers.

Run: python3 vendor_dynamics.py [part]     part in {check, race, learn, private}
"""
import sys
import numpy as np
import vendor_model as VM

a, b, B, c0, kv = VM.a, VM.b, VM.B, VM.c0, VM.kv
A0 = 0.5
n = 4000
FC = VM.FGRID[: 5 * n].reshape(n, 5)[:, 2]
WC = VM.W[: 5 * n].reshape(n, 5).sum(1)
h = VM.h
SH = FC * a * h(a * b * FC / 1.0)
PS = np.linspace(0.0, 3.0, 151)


def tool(A, p):
    """Net saving of the tool and optimal budget for reach A at usage price p."""
    c = c0 + p
    return FC * A * a * h(A * a * B * b * FC / c), VM.Tstar(A * a, B * b, c, FC)


def stage2(A):
    best = (0.0, None, 0.0, 0.0)
    for p in PS[PS > kv]:
        S, T = tool(A, p)
        ad = S > SH + 1e-9
        pr = float(((p - kv) * T * ad * WC).sum())
        if pr > best[0]:
            best = (pr, p, float((np.where(ad, S - SH, 0) * WC).sum()), float((ad * WC).sum()))
    return best


def duopoly(A1, A2, grid=np.linspace(0.12, 2.0, 60)):
    S1 = np.array([tool(A1, p) for p in grid], dtype=object)
    s1 = np.array([tool(A1, p)[0] for p in grid]); t1 = np.array([tool(A1, p)[1] for p in grid])
    s2 = np.array([tool(A2, p)[0] for p in grid]); t2 = np.array([tool(A2, p)[1] for p in grid])
    m = len(grid)
    P1 = np.zeros((m, m)); P2 = np.zeros((m, m)); CS = np.zeros((m, m))
    for i in range(m):
        for j in range(m):
            c1 = (s1[i] >= s2[j]) & (s1[i] > SH + 1e-9)
            c2 = (s2[j] > s1[i]) & (s2[j] > SH + 1e-9)
            P1[i, j] = ((grid[i] - kv) * t1[i] * c1 * WC).sum(); P2[i, j] = ((grid[j] - kv) * t2[j] * c2 * WC).sum()
            CS[i, j] = (np.where(c1, s1[i] - SH, np.where(c2, s2[j] - SH, 0.0)) * WC).sum()
    ne = [(i, j) for i in range(m) for j in range(m)
          if P1[i, j] >= P1[:, j].max() - 1e-12 and P2[i, j] >= P2[i, :].max() - 1e-12]
    i, j = max(ne, key=lambda x: P1[x] + P2[x])
    return P1[i, j], P2[i, j], CS[i, j], grid[i], grid[j], len(ne)


if __name__ == "__main__":
    part = sys.argv[1] if len(sys.argv) > 1 else "all"
    if part in ("check", "all"):
        print("check vs earlier (fine grid): Pi*(0.90)=1.037, Pi*(1.00)=5.69-5.77, Pi*(1.10)=7.287")
        for A in (0.9, 1.0, 1.1):
            r = stage2(A); print(f"   coarse grid A={A}: Pi*={r[0]:.3f} price={r[1]:.2f} CS={r[2]:.3f} share={r[3]:.2f}")


# =============================================================== (1) two vendors investing simultaneously
def race():
    G = [0.5, 0.7, 0.8, 0.9, 1.0, 1.1, 1.3]
    k = len(G)
    U = np.zeros((k, k)); CSm = np.zeros((k, k))
    for i in range(k):
        for j in range(i + 1):
            if G[i] <= 0.55 and G[j] <= 0.55:
                continue
            p1, p2, cs, _, _, _ = duopoly(G[i], G[j])
            U[i, j], U[j, i] = p1, p2
            CSm[i, j] = CSm[j, i] = cs
    mono = [stage2(A) for A in G]
    print("payoff matrix U[own reach, rival reach] (stage-2 Nash profits, before investment cost):")
    print("        rival: " + "  ".join(f"{g:5.2f}" for g in G))
    for i in range(k):
        print(f"  own {G[i]:.2f}:   " + "  ".join(f"{U[i, j]:5.2f}" for j in range(k)))
    print("monopoly profit Pi*(A):  " + "  ".join(f"{m[0]:5.2f}" for m in mono))
    print("\ninvestment game: payoff_i = U(A_i, A_j) - (theta/2)(A_i - 0.5)^2 ; pure-strategy Nash equilibria")
    print(" theta | equilibria (A1,A2)                      | max reach | monopolist would choose | social optimum (A1,A2)")
    for th in (200, 100, 80, 60, 50, 46, 40, 30, 20, 10):
        cost = [0.5 * th * (g - A0) ** 2 for g in G]
        eq = [(i, j) for i in range(k) for j in range(k)
              if U[i, j] - cost[i] >= max(U[m, j] - cost[m] for m in range(k)) - 1e-9
              and U[j, i] - cost[j] >= max(U[m, i] - cost[m] for m in range(k)) - 1e-9]
        eq_u = sorted({tuple(sorted((G[i], G[j]), reverse=True)) for i, j in eq})
        mono_choice = G[int(np.argmax([mono[m][0] - cost[m] for m in range(k)]))]
        best_w = max(((U[i, j] + U[j, i] + CSm[i, j] - cost[i] - cost[j], i, j) for i in range(k) for j in range(i, k)))
        print(f"  {th:4d} | " + ", ".join(f"({x:.2f},{y:.2f})" for x, y in eq_u)[:40].ljust(40) +
              f"| {max(max(x) for x in eq_u) if eq_u else float('nan'):.2f}      |  {mono_choice:.2f}"
              f"                   | ({G[best_w[1]]:.2f},{G[best_w[2]]:.2f})")


# =============================================================== (2) learning from usage
def learn():
    delta = 0.9
    As = np.round(np.arange(0.5, 1.301, 0.02), 3)
    pi_star = {A: stage2(A)[0] for A in As}
    Pgrid = np.linspace(0.0, 1.6, 33)
    def Pi_star(A):
        return np.interp(A, As, [pi_star[x] for x in As])
    def period1(A, p):
        S, T = tool(A, p)
        ad = S > SH + 1e-9
        return float(((p - kv) * T * ad * WC).sum()), float((ad * WC).sum())
    print("two periods, discount 0.9; reach next period A2 = min(1.3, A1 + lam * adoption share in period 1)")
    print(" lam | theta^ (invests iff theta<=theta^) | at theta=60: A1*, p1*, A2 | at theta=46: A1*, p1*, A2 | static (lam=0) p1 for same A1")
    res = {}
    for lam in (0.0, 0.15, 0.3, 0.6):
        cache = {(A, p): period1(A, p) for A in As for p in Pgrid}
        def best(th):
            top = (-1e9, None)
            for A in As:
                for p in Pgrid:
                    pr, s = cache[(A, p)]
                    A2 = min(1.3, A + lam * s)
                    tot = pr + delta * Pi_star(A2) - 0.5 * th * (A - A0) ** 2
                    if tot > top[0]:
                        top = (tot, (A, p, A2, s))
            return top
        ths = np.exp(np.linspace(np.log(20), np.log(400), 90))
        reach_any = [t for t in ths if best(t)[1][2] >= 1.0 - 1e-9]       # parity reached by period 2
        th_hat = max(reach_any) if reach_any else float("nan")
        r60, r46 = best(60)[1], best(46)[1]
        res[lam] = th_hat
        print(f" {lam:.2f} |   {th_hat:6.0f}                      | {r60[0]:.2f}, {r60[1]:.2f}, {r60[2]:.2f}          | {r46[0]:.2f}, {r46[1]:.2f}, {r46[2]:.2f}")
    print("(theta^ here = the largest cost at which the vendor reaches parity A>=1 by period 2)")


# =============================================================== (3) private reach + liability as commitment
def private():
    print("Private reach: the vendor invests secretly; firms cannot observe A. Contract = (usage price p, fixed damages D paid with")
    print("prob. phi if the tool fails). Firms hold rational expectations about the investment the contract induces.")
    print("Without liability the vendor's revenue depends only on beliefs, so it has no reason to invest (A=A0).")
    print(" phi  theta | best (p, D) | induced A | adopters | vendor profit | public-reach benchmark (observable A)")
    ps = np.linspace(0.12, 2.0, 60)
    Ds = np.concatenate([[0.0], np.linspace(2, 120, 60)])
    for phi in (1.0, 0.5):
        for th in (80, 60, 46, 35, 25):
            best = (0.0, None)
            for D in Ds:
                for p in ps:
                    Ae = A0
                    for _ in range(25):                      # fixed point: A = min(1, A0 + phi*D*s/theta)
                        S, T = tool(Ae, p)
                        ad = (S + phi * max(0.0, 1 - Ae) * D > SH + 1e-9)
                        s = float((ad * WC).sum())
                        An = min(1.0, A0 + phi * D * s / th)
                        if abs(An - Ae) < 1e-4: Ae = An; break
                        Ae = An
                    S, T = tool(Ae, p)
                    ad = (S + phi * max(0.0, 1 - Ae) * D > SH + 1e-9)
                    s = float((ad * WC).sum())
                    prof = float((((p - kv) * T - phi * max(0.0, 1 - Ae) * D) * ad * WC).sum()) - 0.5 * th * (Ae - A0) ** 2
                    if prof > best[0]:
                        best = (prof, (p, D, Ae, s))
            pub = max(stage2(A)[0] - 0.5 * th * (A - A0) ** 2 for A in np.round(np.arange(0.5, 1.301, 0.02), 3))
            if best[1] is None:
                print(f" {phi:.1f}  {th:5d} |   no viable contract: A stays at {A0}     |   -   |   0.000 | {pub:.3f}")
            else:
                p, D, Ae, s = best[1]
                print(f" {phi:.1f}  {th:5d} | ({p:.2f}, {D:5.1f}) |   {Ae:.2f}   |  {s:.2f}   |   {best[0]:.3f}   | {pub:.3f}")


if __name__ == "__main__" and len(sys.argv) > 1:
    {"race": race, "learn": learn, "private": private}.get(sys.argv[1], lambda: None)()
