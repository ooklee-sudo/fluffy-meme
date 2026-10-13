"""Exhaustive checks of the analytical results for the simplified alternating-move game.

Environment: two firms, inelastic demand D per period (up to the highest price), a finite price set, no
service-level penalty, capacities fixed.  Firms alternate; the mover picks a price that stays in force until its next
move.  A pure Markov strategy maps the rival's price to the mover's own price.  We enumerate every pure profile
(s_A, s_B), compute values by solving the induced Markov chain exactly, and test the one-shot-deviation condition.
"""
import itertools
import numpy as np


def alloc(KA, KB, D, pa, pb):
    if pa < pb:
        dA, dB = D, 0.0
    elif pa == pb:
        dA = dB = D / 2
    else:
        dA, dB = 0.0, D
    qA = min(KA, dA + max(0.0, dB - KB))
    qB = min(KB, dB + max(0.0, dA - KA))
    return qA, qB


def flows(prices, c, KA, KB, D):
    n = len(prices)
    fA = np.zeros((n, n)); fB = np.zeros((n, n))
    for i, pa in enumerate(prices):
        for j, pb in enumerate(prices):
            qA, qB = alloc(KA, KB, D, pa, pb)
            fA[i, j] = (pa - c) * qA
            fB[i, j] = (pb - c) * qB
    return fA, fB


def values(sA, sB, fA, fB, beta):
    """State (q, r): mover q in {0,1}, rival price index r. Returns V[i][q][r] for firms i = 0, 1."""
    n = fA.shape[0]
    idx = lambda q, r: q * n + r
    P = np.zeros((2 * n, 2 * n)); rA = np.zeros(2 * n); rB = np.zeros(2 * n)
    for q in (0, 1):
        for r in range(n):
            p = sA[r] if q == 0 else sB[r]                   # mover's new price
            pa, pb = (p, r) if q == 0 else (r, p)            # prices in force (A, B)
            rA[idx(q, r)], rB[idx(q, r)] = fA[pa, pb], fB[pa, pb]
            P[idx(q, r), idx(1 - q, p)] = 1.0
    M = np.eye(2 * n) - beta * P
    return np.linalg.solve(M, rA).reshape(2, n), np.linalg.solve(M, rB).reshape(2, n)


def is_mpe(sA, sB, fA, fB, beta, tol=1e-9):
    n = fA.shape[0]
    VA, VB = values(sA, sB, fA, fB, beta)
    V = (VA, VB)
    for q in (0, 1):
        for r in range(n):
            cur = V[q][q, r]
            for p in range(n):
                pa, pb = (p, r) if q == 0 else (r, p)
                fl = fA[pa, pb] if q == 0 else fB[pa, pb]
                dev = fl + beta * V[q][1 - q, p]
                if dev > cur + tol:
                    return False, V
    return True, V


def all_pure_mpe(prices, c, KA, KB, D, beta):
    fA, fB = flows(prices, c, KA, KB, D)
    n = len(prices)
    out = []
    for sA in itertools.product(range(n), repeat=n):
        for sB in itertools.product(range(n), repeat=n):
            ok, V = is_mpe(sA, sB, fA, fB, beta)
            if ok:
                out.append((sA, sB, V))
    return out


def long_run(sA, sB, n, start=(0, 0), steps=60):
    """Price path (mover, price index) under the profile, starting with A to move facing price index start[1]."""
    q, r = start
    path = []
    for _ in range(steps):
        p = sA[r] if q == 0 else sB[r]
        path.append((q, p))
        r, q = p, 1 - q
    return path


if __name__ == "__main__":
    # --- two prices, ample capacities: characterise symmetric pure MPE -------------------
    D, c = 1.0, 0.0
    for L, H in ((1.0, 1.5), (1.0, 1.8), (1.0, 2.2)):
        r = H / L
        print(f"two prices L={L} H={H}  r=m_H/m_L={r:.2f}")
        for beta in (0.2, 0.5, 0.6, 0.7, 0.9):
            eq = all_pure_mpe([L, H], c, 10, 10, D, beta)
            names = []
            for sA, sB, V in eq:
                if sA == sB:
                    names.append({(0, 0): "always-L", (1, 1): "always-H", (0, 1): "match", (1, 0): "anti-match"}[tuple(sA)])
                else:
                    names.append(f"asym{sA}/{sB}")
            lo, hi = max(2 - r, 0), 1 / r
            print(f"  beta={beta}: MPE = {names}   predicted match iff {lo:.2f} <= beta <= {hi:.2f}")


# ======================================================================================
# Verification of Propositions 4 and 5 (two prices, ample / scarce capacities)
# ======================================================================================
def name_profile(sA, sB):
    if sA == sB:
        return {(0, 0): "always-L", (1, 1): "always-H", (0, 1): "match", (1, 0): "anti-match"}[tuple(sA)]
    return "asym"


def steady_flows(sA, sB, fA, fB, start_mover):
    """Flows in the last simulated period (steady state) when `start_mover` moves first, prices (H, H) in force."""
    q, rv, fl = start_mover, 1, None
    for _ in range(41):
        p = sA[rv] if q == 0 else sB[rv]
        pa, pb = (p, rv) if q == 0 else (rv, p)
        fl = (fA[pa, pb], fB[pa, pb])
        rv, q = p, 1 - q
    return fl


def verify_propositions(verbose=True):
    import json, os
    D, c, L = 1.0, 0.0, 1.0
    tol = 1e-9
    out = {"prop4": {"points": 0, "mismatches": []}, "prop5": {}}
    # ---- Proposition 4: ample capacities, two prices -----------------------------------
    for r in np.arange(1.02, 1.99, 0.02):
        H = L * r
        for beta in np.arange(0.02, 0.99, 0.02):
            lo, hi = 2 - r, 1 / r
            if abs(beta - lo) < 1e-6 or abs(beta - hi) < 1e-6:
                continue
            eq = all_pure_mpe([L, H], c, 10.0, 10.0, D, beta)
            got = sorted(name_profile(sA, sB) for sA, sB, _ in eq)
            exp = sorted(["always-L"] + (["match"] if lo <= beta <= hi else []))
            out["prop4"]["points"] += 1
            if got != exp:
                out["prop4"]["mismatches"].append({"r": round(float(r), 2), "beta": round(float(beta), 2), "got": got, "expected": exp})
    # ---- Proposition 5: (a, s) subgame, E1 profile -------------------------------------
    pts = mism = 0
    guarantee_ok = True
    n_const = n_cycle = 0
    e1_bad = []
    for r in np.arange(1.02, 1.99, 0.02):
        H = L * r
        l, h = 0.5 * L * D, 0.5 * H * D
        fA, fB = flows([L, H], c, 0.5 * D, D, D)         # A scarce, B ample
        for beta in np.arange(0.02, 0.99, 0.02):
            lo, hi = r - 1, (2 - r) / (r - 1)
            if min(abs(beta - lo), abs(beta - hi)) < 1e-6:
                continue
            E1 = ((0, 0), (1, 0))                         # sA(L)=sA(H)=L ; sB(L)=H, sB(H)=L   (index 0 = L, 1 = H)
            ok, _ = is_mpe(E1[0], E1[1], fA, fB, beta)
            pts += 1
            if ok != (lo <= beta <= hi):
                mism += 1; e1_bad.append((round(float(r), 2), round(float(beta), 2)))
            if ok:
                fl = steady_flows(E1[0], E1[1], fA, fB, 0)
                if abs(fl[0] - l) > tol or abs(fl[1] - h) > tol:
                    mism += 1; e1_bad.append(("flows", round(float(r), 2), round(float(beta), 2)))
            # guarantee: in every pure MPE whose price outcome settles on constant prices, the scarce firm's flow is at least l;
            # pure MPE with price cycles exist in this subgame and are only counted
            for sA, sB, _ in all_pure_mpe([L, H], c, 0.5 * D, D, D, beta):
                for sm in (0, 1):
                    path = long_run(sA, sB, 2, (sm, 1), steps=40)
                    constant = len(set(p for _, p in path[-8:])) == 1 or all(path[-8:][i][1] == path[-8:][0][1] if path[-8:][i][0] == path[-8:][0][0] else True for i in range(8)) and len({p for q_, p in path[-8:] if q_ == 0}) == 1 and len({p for q_, p in path[-8:] if q_ == 1}) == 1
                    if constant:
                        n_const += 1
                        if steady_flows(sA, sB, fA, fB, sm)[0] < l - 1e-9:
                            guarantee_ok = False
                    else:
                        n_cycle += 1
    out["prop5"]["E1_points"] = pts
    out["prop5"]["E1_mismatches"] = mism
    out["prop5"]["E1_bad_examples"] = e1_bad[:5]
    out["prop5"]["scarce_flow_at_least_l_in_every_constant_price_pure_MPE"] = guarantee_ok
    out["prop5"]["pure_MPE_outcomes_constant_vs_cyclic"] = [n_const, n_cycle]
    # ---- Proposition 5: (a, a) matching profile and feasibility region J(r) -------------
    j_nonempty_up_to, j_empty_from = None, None
    rows = []
    for r in np.arange(1.02, 1.99, 0.01):
        lo = max(2 - r, r - 1); hi = min(1 / r, (2 - r) / (r - 1))
        rows.append((round(float(r), 2), lo <= hi + 1e-12))
    nonempty = [r for r, ok in rows if ok]
    out["prop5"]["J_nonempty_r_range"] = [min(nonempty), max(nonempty)]
    out["prop5"]["golden_ratio"] = (1 + 5 ** 0.5) / 2
    # direct numeric check that, inside J(r), M is an MPE of (a,a) and E1 an MPE of (a,s)
    inside = bad = 0
    for r in np.arange(1.02, 1.62, 0.02):
        H = L * r
        fAA, fBB = flows([L, H], c, D, D, D)
        fAs, fBs = flows([L, H], c, 0.5 * D, D, D)
        lo = max(2 - r, r - 1); hi = min(1 / r, (2 - r) / (r - 1))
        for beta in np.linspace(lo + 1e-4, hi - 1e-4, 5) if lo < hi else []:
            inside += 1
            okM, _ = is_mpe((0, 1), (0, 1), fAA, fBB, beta)
            okE, _ = is_mpe((0, 0), (1, 0), fAs, fBs, beta)
            if not (okM and okE):
                bad += 1
    out["prop5"]["inside_J_points"] = inside
    out["prop5"]["inside_J_failures"] = bad
    # static (a, s) stage game: mixed equilibrium payoffs (A scarce: l, B ample: h)
    r = 1.5; H = L * r; l, h = 0.5 * L * D, 0.5 * H * D
    y = l / h; x = r - 1                                # P(B plays H) , P(A plays H)
    uA_L, uA_H = l, y * h
    uB_L, uB_H = (1 - x) * l + x * 2 * l, h
    out["prop5"]["static_mixed_check"] = {"A_indiff": abs(uA_L - uA_H) < 1e-12, "B_indiff": abs(uB_L - uB_H) < 1e-12,
                                          "payoffs_A_B": [uA_L, uB_H], "l_h": [l, h]}
    json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "theory_checks.json"), "w"), indent=1, default=float)
    if verbose:
        print("Prop 4 grid points:", out["prop4"]["points"], "mismatches:", len(out["prop4"]["mismatches"]), out["prop4"]["mismatches"][:3])
        print("Prop 5:", out["prop5"])
    return out


if __name__ == "__main__" and len(__import__("sys").argv) > 1 and __import__("sys").argv[1] == "verify":
    verify_propositions()
