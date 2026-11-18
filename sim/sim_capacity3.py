"""Extension A (exact equilibrium, M/M/c + arrival variability) and Extension B (endogenous verification).

Policy set: thresholds n = 0,1,...,NMAX and NINF ("never"). A policy has per-task (P, A) = (hand-off
prob, cost excluding hand-off). A randomized policy is a mixture of thresholds, so the achievable set is the
CONVEX HULL of the points (P_n, A_n). Using the hull (not just adjacent thresholds) removes the artifacts of
the earlier script.

Key facts used
  A_n(F) = a_n + F * z_n   (linear in the wrong-output cost F; z_n = prob. of a derailed completion)
  System optimum:   min_P  Ahull(P) + P h + d * Lam^{-1} * L(Lam P),  L(lam)=lam*W(lam)
  Decentralized:    Wardrop equilibrium: each task best-responds to the AVERAGE wait W(lam).
                    FOC:  -Ahull'(P) = h + d W(Lam P)           (decentralized)
                          -Ahull'(P) = h + d (L)'(Lam P)        (system)   with L' = W + lam W' > W
"""
import math
import numpy as np
from sim_capacity import AP, NINF

K, C, MU, Q = 1.0, 5.0, 0.054, 0.06
NMAX = 25


# ------------------------------------------------------------------ per-task primitives
def az_table(theta, nmax=NMAX):
    """Return arrays P_n, a_n, z_n for n in 0..nmax and NINF (last entry)."""
    ns = list(range(nmax + 1)) + [NINF]
    P, a, z = [], [], []
    for n in ns:
        A0, Pn = AP(n, K, C, MU, Q, theta, 0.0)
        A1, _ = AP(n, K, C, MU, Q, theta, 1.0)
        P.append(Pn); a.append(A0); z.append(A1 - A0)
    return np.array(P), np.array(a), np.array(z), ns


def lower_hull(P, A):
    """Lower convex hull vertices (sorted by P)."""
    pts = sorted(zip(P, A))
    hull = []
    for p in pts:
        while len(hull) >= 2:
            (x1, y1), (x2, y2) = hull[-2], hull[-1]
            if (x2 - x1) * (p[1] - y1) - (y2 - y1) * (p[0] - x1) <= 1e-15:
                hull.pop()
            else:
                break
        hull.append(p)
    hp = np.array([h[0] for h in hull]); ha = np.array([h[1] for h in hull])
    return hp, ha


class Hull:
    def __init__(self, P, A):
        self.hp, self.ha = lower_hull(P, A)
        self.pmin, self.pmax = self.hp[0], self.hp[-1]

    def A(self, p):
        return np.interp(p, self.hp, self.ha)

    def slope(self, p):
        """A'(p) (right-derivative), piecewise constant."""
        i = np.clip(np.searchsorted(self.hp, p, side="right") - 1, 0, len(self.hp) - 2)
        return (self.ha[i + 1] - self.ha[i]) / (self.hp[i + 1] - self.hp[i])


# ------------------------------------------------------------------ queue models
def erlang_c(nsrv, a):
    """Prob. of waiting in M/M/c with offered load a = lam/mu (requires a < nsrv)."""
    if a <= 0:
        return 0.0
    # stable recursion via Erlang-B
    b = 1.0
    for i in range(1, nsrv + 1):
        b = a * b / (i + a * b)
    rho = a / nsrv
    return b / (1 - rho * (1 - b))


def sojourn(lam, nsrv, m, ca2=1.0, cs2=1.0, include_service=True):
    """Delay cost base for an escalated task (Allen-Cunneen approximation for G/G/c; exact for M/M/c
    when ca2=cs2=1). m = per-reviewer service rate. include_service=True returns time in system (used in
    the M/M/1 tables of section 1, as in the first script); False returns queueing delay only, which is the
    right choice when the reviewer's working time is already inside the hand-off cost h."""
    base = 1.0 / m if include_service else 0.0
    if lam <= 0:
        return base
    if lam >= nsrv * m:
        return math.inf
    a = lam / m
    wq_mmc = erlang_c(nsrv, a) / (nsrv * m - lam)
    return 0.5 * (ca2 + cs2) * wq_mmc + base


class Queue:
    def __init__(self, nsrv=1, m=1.0, ca2=1.0, cs2=1.0, Lam=1.0, include_service=True):
        self.nsrv, self.m, self.ca2, self.cs2, self.Lam = nsrv, m, ca2, cs2, Lam
        self.include_service = include_service
        self.cap = nsrv * m

    def W(self, P):
        P = np.asarray(P, dtype=float)
        return np.array([sojourn(self.Lam * p, self.nsrv, self.m, self.ca2, self.cs2, self.include_service) for p in np.atleast_1d(P)])

    def pstab(self):
        return min(1.0, 0.9995 * self.cap / self.Lam)


# ------------------------------------------------------------------ solvers
def solve(hull, Q_, h, d, grid=6001):
    """Return dict with system optimum and decentralized equilibrium over the hull."""
    pmax = min(hull.pmax, Q_.pstab())
    if pmax <= hull.pmin:
        # even the loosest policy overloads reviewers -> only feasible P are the never/near-never ones
        pmax = hull.pmin
    Ps = np.linspace(hull.pmin, pmax, grid)
    W = Q_.W(Ps)
    A = hull.A(Ps)
    sys_cost = A + Ps * h + d * Ps * W        # per task; L/Lam = P*W
    i_sys = int(np.argmin(sys_cost))
    # decentralized: phi(P) = -A'(P) - (h + d W(P)); equilibrium = sup{P: phi >= 0}
    mid = 0.5 * (Ps[:-1] + Ps[1:])
    phi = -hull.slope(mid) - (h + d * 0.5 * (W[:-1] + W[1:]))
    ok = np.where(phi >= 0)[0]
    j = ok[-1] + 1 if len(ok) else 0
    j = min(j, len(Ps) - 1)
    dec_cost = sys_cost[j]
    return dict(P_sys=Ps[i_sys], cost_sys=sys_cost[i_sys], P_dec=Ps[j], cost_dec=dec_cost,
                P_hi=pmax, W_sys=W[i_sys], W_dec=W[j])


# ================================================================== experiments
def exp_equilibrium_table():
    print("== 1. Exact equilibrium (convex hull of policies), M/M/1, same 36 cells as before ==")
    h, d = 20.0, 10.0
    viol = 0; tot = 0; worst_loss = 0
    rows = []
    for theta, F in [(0.29, 60), (0.29, 100), (0.18, 100), (0.40, 100), (0.12, 100), (0.05, 100)]:
        Pn, an, zn, _ = az_table(theta)
        H = Hull(Pn, an + F * zn)
        for Lam in [0.5, 1, 2, 3, 4, 6]:
            r = solve(H, Queue(1, 1.0, 1, 1, Lam), h, d)
            tot += 1
            over = r["P_dec"] >= r["P_sys"] - 1e-3
            viol += (not over)
            loss = 100 * (r["cost_dec"] - r["cost_sys"]) / r["cost_sys"]
            worst_loss = max(worst_loss, loss)
            rows.append((theta, F, Lam, r["P_sys"], r["P_dec"], loss, over))
            flag = "" if over else "  <-- VIOLATION"
            print(f" th={theta:4.2f} F={F:3d} Lam={Lam:3.1f}  P_sys={r['P_sys']:.3f}  P_dec={r['P_dec']:.3f}  loss={loss:5.2f}%{flag}")
    print(f" violations of P_dec >= P_sys: {viol}/{tot}; worst decentralized loss {worst_loss:.1f}%")
    # the two earlier exception cells
    for theta, F, Lam in [(0.29, 100, 4.0), (0.40, 100, 6.0)]:
        Pn, an, zn, _ = az_table(theta)
        H = Hull(Pn, an + F * zn)
        r = solve(H, Queue(1, 1.0, 1, 1, Lam), h, d)
        print(f" earlier exception th={theta} F={F} Lam={Lam}: P_sys={r['P_sys']:.3f}, P_dec={r['P_dec']:.3f}, "
              f"cost_dec={r['cost_dec']:.2f} (finite)")


def exp_queues():
    print("\n== 2. M/M/c with arrival variability (Allen-Cunneen), queueing-delay cost only, fixed total capacity = 1 ==")
    h, d = 20.0, 10.0
    theta, F = 0.29, 100
    Pn, an, zn, _ = az_table(theta)
    H = Hull(Pn, an + F * zn)
    print(" servers c, per-server rate = 1/c (total capacity constant); ca2 = arrival SCV, cs2 = 1")
    print(" Lam  c  ca2 |  P_sys   P_dec  gap(P_dec-P_sys) | W_sys   W_dec  | loss%")
    allgood = True
    for Lam in [2.0, 4.0]:
        for c_ in [1, 2, 5, 10]:
            for ca2 in [1.0, 2.0, 4.0]:
                r = solve(H, Queue(c_, 1.0 / c_, ca2, 1.0, Lam, include_service=False), h, d, grid=3001)
                loss = 100 * (r["cost_dec"] - r["cost_sys"]) / r["cost_sys"]
                allgood &= r["P_dec"] >= r["P_sys"] - 1e-3
                print(f" {Lam:3.1f} {c_:2d} {ca2:4.1f} | {r['P_sys']:.3f}  {r['P_dec']:.3f}   {r['P_dec']-r['P_sys']:.3f}        "
                      f"| {r['W_sys']:6.2f} {r['W_dec']:6.2f} | {loss:5.2f}")
    print(" P_dec >= P_sys in all queue configurations:", allgood)

    print("\n -- monitoring value vs number of reviewers (per-reviewer rate fixed = 0.5; Lam=3) --")
    for ca2 in [1.0, 3.0]:
        vals = []
        for c_ in [1, 2, 3, 4, 5, 6, 8, 10, 15, 25]:
            Q_ = Queue(c_, 0.5, ca2, 1.0, 3.0, include_service=False)
            r = solve(H, Q_, h, d, grid=3001)
            # static choices: never hand off, or always hand off (feasible only if Lam < capacity)
            pmax = Q_.pstab()
            cands = []
            cands.append(H.ha[0] + H.hp[0] * (h + d * Q_.W(H.hp[0])[0]) if H.hp[0] * Q_.Lam < Q_.cap else math.inf)
            if 1.0 <= pmax:
                cands.append(0.0 + 1.0 * (h + d * Q_.W(1.0)[0]))
            val = max(min(cands) - r["cost_sys"], 0.0)
            vals.append((c_, round(val, 2)))
        print(f" ca2={ca2}: {vals}")


# ------------------------------------------------------------------ Extension B
def cost_nd(an, zn, Pn, H_eff, Fu, Fd, dq, kappa):
    Feff = dq * Fd + (1 - dq) * Fu
    return an + Feff * zn + Pn * H_eff + kappa * dq**2


def exp_verification():
    print("\n== 3. Endogenous verification investment v(d)=kappa*d^2 ==")
    theta, Fu, Fd, kappa = 0.29, 100.0, 30.0, 25.0
    Pn, an, zn, ns = az_table(theta)
    ds = np.linspace(0, 1, 101)

    def best(H_eff, kap=kappa):
        out = (math.inf, None, None)
        for i, n in enumerate(ns):
            for dq in ds:
                c_ = cost_nd(an[i], zn[i], Pn[i], H_eff, Fu, Fd, dq, kap)
                if c_ < out[0]:
                    out = (c_, n, dq)
        return out

    print(" -- (a) joint optimum (n*, d*) as the hand-off cost H varies --")
    print("   H     n*    d*    cost   | cost with d=0   gain from verification")
    gains = []
    for Hc in [5, 10, 20, 30, 40, 60, 100, 200, 500]:
        c1, n1, d1 = best(Hc)
        c0 = min(an[i] + Fu * zn[i] + Pn[i] * Hc for i in range(len(ns)))
        gains.append(c0 - c1)
        print(f"  {Hc:4d}  {('inf' if n1==NINF else n1)!s:>4}  {d1:4.2f}  {c1:7.2f} | {c0:7.2f}        {c0-c1:6.2f}")
    mono = all(gains[i + 1] >= gains[i] - 1e-9 for i in range(len(gains) - 1))
    print("  value of verification nondecreasing in H:", mono)

    print(" -- (b) comparative statics: d*(n) and n*(d) (substitutes) --")
    Hc = 40.0
    for i, n in enumerate(ns[:6] + [NINF]):
        j = ns.index(n)
        dd = [cost_nd(an[j], zn[j], Pn[j], Hc, Fu, Fd, x, kappa) for x in ds]
        print(f"   n={'inf' if n==NINF else n}: z_n={zn[j]:.4f}  best d given n = {ds[int(np.argmin(dd))]:.2f}")
    prev = -1; okn = True
    for dq in [0, 0.25, 0.5, 0.75, 1.0]:
        cs = [cost_nd(an[i], zn[i], Pn[i], Hc, Fu, Fd, dq, 0.0) for i in range(len(ns))]
        nb = ns[int(np.argmin(cs))]
        print(f"   d={dq:4.2f}: best n = {'inf' if nb==NINF else nb}")
        v = 10**6 if nb == NINF else nb
        okn &= v >= prev; prev = v
    print("   n*(d) nondecreasing:", okn)

    print(" -- (c) crowd-out: value of the count rule (vs best static) with and without verification --")
    print("   H     monitoring value, d=0   monitoring value, d=d*(joint)")
    for Hc in [10, 20, 30, 40, 60, 100, 200]:
        def static_best(dq):
            Feff = dq * Fd + (1 - dq) * Fu
            allh = Hc                                   # always hand off (n=0)
            never = an[-1] + Feff * zn[-1]              # never hand off
            return min(allh, never)
        def mon_val(dq):
            cs = min(cost_nd(an[i], zn[i], Pn[i], Hc, Fu, Fd, dq, 0.0) for i in range(len(ns)))
            return static_best(dq) - cs
        _, _, dstar = best(Hc)
        print(f"  {Hc:4d}   {mon_val(0.0):8.3f}                {mon_val(dstar):8.3f}")

    print(" -- (d) staffing vs verification: M/M/1, optimal d as reviewer capacity s grows (Lam=3, system optimum) --")
    h, dd_ = 20.0, 10.0
    rows = []
    for s_ in [0.7, 0.9, 1.2, 1.6, 2.2, 3.5, 6, 12]:
        Q_ = Queue(1, s_, 1.0, 1.0, 3.0)
        bestc = (math.inf, None, None, None)
        for dq in np.linspace(0, 1, 21):
            Feff = dq * Fd + (1 - dq) * Fu
            Hh = Hull(Pn, an + Feff * zn)
            r = solve(Hh, Q_, h, dd_, grid=1501)
            tot = r["cost_sys"] + kappa * dq**2
            if tot < bestc[0]:
                bestc = (tot, dq, r["P_sys"], r["P_dec"])
        rows.append((s_, round(bestc[1], 2), round(bestc[2], 3)))
    print("   (s, d*, P_sys):", rows)
    dstars = [r[1] for r in rows]
    print("   d* nonincreasing in staffing s:", all(dstars[i + 1] <= dstars[i] + 1e-9 for i in range(len(dstars) - 1)))

    print(" -- (e) fixed-cost verification adoption: adopt iff gain >= fixed cost; adoption region in H --")
    dbar, kfix = 0.8, 6.0
    for Hc in [5, 10, 20, 30, 40, 60, 100, 200, 500]:
        c0 = min(an[i] + Fu * zn[i] + Pn[i] * Hc for i in range(len(ns)))
        Feff = dbar * Fd + (1 - dbar) * Fu
        c1 = min(an[i] + Feff * zn[i] + Pn[i] * Hc for i in range(len(ns))) + kfix
        n0 = ns[int(np.argmin([an[i] + Fu * zn[i] + Pn[i] * Hc for i in range(len(ns))]))]
        n1 = ns[int(np.argmin([an[i] + Feff * zn[i] + Pn[i] * Hc for i in range(len(ns))]))]
        print(f"   H={Hc:4d}: {'ADOPT' if c1 < c0 else 'skip '}  n*(no ver)={'inf' if n0==NINF else n0} -> n*(ver)={'inf' if n1==NINF else n1}   net gain {c0-c1:6.2f}")


def exp_verification_extra():
    theta, Fu, Fd = 0.29, 100.0, 30.0
    Pn, an, zn, ns = az_table(theta)
    ds = np.linspace(0, 1, 101)
    print("\n== 3b. Crowd-out sensitivity to the verification cost kappa (v(d)=kappa*d^2) ==")
    print("  monitoring value (count rule vs best static) without / with jointly-optimal verification")
    for kappa in [2.0, 5.0, 10.0, 25.0]:
        row = []
        for Hc in [40, 60, 80, 100]:
            def val(dq):
                Feff = dq * Fd + (1 - dq) * Fu
                stat = min(Hc, an[-1] + Feff * zn[-1])
                return stat - min(an[i] + Feff * zn[i] + Pn[i] * Hc for i in range(len(ns)))
            tot = [min(an[i] + (dq*Fd+(1-dq)*Fu) * zn[i] + Pn[i] * Hc for i in range(len(ns))) + kappa*dq**2 for dq in ds]
            dstar = ds[int(np.argmin(tot))]
            row.append(f"H={Hc}: {val(0):5.2f}->{val(dstar):5.2f} (d*={dstar:.2f})")
        print(f"  kappa={kappa:5.1f}  " + "   ".join(row))

    print("\n== 3c. Regime map: best control portfolio over (H, fixed verification cost) ==")
    print("  verification quality dbar=0.8 at fixed cost K per task; entries: E=always escalate, C=count rule,")
    print("  N=never escalate; '+V' = adopt verification")
    dbar = 0.8
    Fv = dbar * Fd + (1 - dbar) * Fu
    Ks = [0.5, 1, 2, 4, 6, 10]
    Hs = [10, 20, 30, 40, 60, 80, 100, 150, 300]
    print("   K\\H " + " ".join(f"{h_:>5d}" for h_ in Hs))
    for Kfix in Ks:
        line = []
        for Hc in Hs:
            opts = {}
            for tag, F_, add in [("", Fu, 0.0), ("+V", Fv, Kfix)]:
                cs = [an[i] + F_ * zn[i] + Pn[i] * Hc + add for i in range(len(ns))]
                i = int(np.argmin(cs)); n = ns[i]
                typ = "E" if n == 0 else ("N" if n == NINF else "C")
                opts[tag] = (cs[i], typ + tag)
            line.append(min(opts.values())[1])
        print(f"  {Kfix:5.1f} " + " ".join(f"{x:>5s}" for x in line))


if __name__ == "__main__":
    exp_equilibrium_table()
    exp_queues()
    exp_verification()
    exp_verification_extra()
