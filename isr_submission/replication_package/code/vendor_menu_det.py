"""Deterministic menus in the testing-service model (companion to vendor_menu.py).

vendor_menu.py solved the screening LP with random allocations (an UPPER BOUND). Here each type receives ONE item
(budget T_j, payment t) -> mixed-integer program (one-hot assignment x_ij, transfers t_i). Compared on the same grid:
  linear price p        (firm picks T freely)
  two-part tariff F + p (firm picks T given p; adopt iff surplus - F >= human outside option)
  deterministic menu    (MILP, time limit; reports the solver's lower and upper bounds)
  random-allocation LP  (upper bound on any menu)

Run: python3 vendor_menu_det.py [nI nJ time_limit_seconds]
"""
import sys
import numpy as np
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix
import vendor_model as VM
import vendor_menu as VMN

a, b, Bs, c0, kv = VM.a, VM.b, VM.B, VM.c0, VM.kv
h = VM.h


def build(A, nI, nJ):
    f, w, T, SH, Bf = VMN.setup(A, nI=nI, nJ=nJ)
    return f, w, T, SH, Bf


def milp_menu(f, w, T, SH, Bf, time_limit):
    I, J = Bf.shape
    nv = I * (J + 1) + I
    ix = lambda i, j: i * (J + 1) + j
    it = lambda i: I * (J + 1) + i
    c = np.zeros(nv)
    for i in range(I):
        for j in range(1, J + 1):
            c[ix(i, j)] = w[i] * kv * T[j - 1]
        c[it(i)] = -w[i]
    n_rows = I * (I - 1) + I
    M = lil_matrix((n_rows, nv)); ub = np.zeros(n_rows); r = 0
    for i in range(I):
        for m in range(I):
            if m == i: continue
            for (mm, sg) in ((m, 1.0), (i, -1.0)):
                M[r, ix(mm, 0)] += sg * SH[i]
                for j in range(1, J + 1):
                    M[r, ix(mm, j)] += sg * Bf[i, j - 1]
                M[r, it(mm)] += -sg
            r += 1
    for i in range(I):
        M[r, ix(i, 0)] += -SH[i]
        for j in range(1, J + 1):
            M[r, ix(i, j)] += -Bf[i, j - 1]
        M[r, it(i)] += 1.0; ub[r] = -SH[i]; r += 1
    E = lil_matrix((I, nv))
    for i in range(I):
        for j in range(J + 1):
            E[i, ix(i, j)] = 1.0
    cons = [LinearConstraint(M.tocsr(), -np.inf, ub), LinearConstraint(E.tocsr(), 1.0, 1.0)]
    integ = np.zeros(nv); integ[: I * (J + 1)] = 1
    lb = np.concatenate([np.zeros(I * (J + 1)), np.full(I, -1e3)])
    ubv = np.concatenate([np.ones(I * (J + 1)), np.full(I, 1e3)])
    res = milp(c, constraints=cons, integrality=integ, bounds=Bounds(lb, ubv),
               options={"time_limit": time_limit, "mip_rel_gap": 1e-4, "disp": False})
    return res, ix, it


def two_part(A, f, w, SH):
    best = (0.0, None, None)
    for p in np.linspace(0.0, 2.0, 81):
        cL = c0 + p
        Tstar = VM.Tstar(A * a, Bs * b, cL, f)
        gross = f * A * a * (1 - np.exp(-Bs * b * Tstar)) - c0 * Tstar - p * Tstar      # firm surplus at price p, before fee
        slack = gross - SH
        for F in np.unique(np.concatenate([np.maximum(slack, 0), [0]])):
            ad = slack >= F - 1e-12
            ad &= Tstar > 0
            prof = float(((F + (p - kv) * Tstar) * ad * w).sum())
            if prof > best[0]:
                best = (prof, p, F)
    return best


if __name__ == "__main__":
    nI = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    nJ = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    tl = float(sys.argv[3]) if len(sys.argv) > 3 else 600
    print(f"grid: {nI} types x {nJ} budget levels; k={kv}, c0={c0}, B={Bs}; MILP time limit {tl:.0f}s")
    print(" A  | linear | two-part(F,p) | det. menu (MILP) | gap | LP bound (random) | det/linear | adopters (menu) | top-decile adopters")
    for A in (0.8, 0.9, 1.0):
        f, w, T, SH, Bf = build(A, nI, nJ)
        lin, p_star, adopt_lin = VMN.linear_best(A, f, w, SH)
        tp, p_tp, F_tp = two_part(A, f, w, SH)
        lp = VMN.menu_lp(A, f, w, T, SH, Bf)[0]
        res, ix, it = milp_menu(f, w, T, SH, Bf, tl)
        if res.x is None:
            print(f" {A:.1f} | {lin:.3f} | {tp:.3f} | MILP found no solution ({res.message}) | LP {lp:.3f}"); continue
        prof = -res.fun
        I, J = Bf.shape
        x = res.x
        assign = np.array([int(np.argmax([x[ix(i, j)] for j in range(J + 1)])) for i in range(I)])
        adopt = assign > 0
        top = np.cumsum(w) > 0.9
        gap = res.mip_gap if res.mip_gap is not None else float("nan")
        print(f" {A:.1f} | {lin:.3f} | {tp:.3f} (F={F_tp:.2f},p={p_tp:.2f}) | {prof:.3f} | {gap:.1%} | {lp:.3f} | {prof/lin-1:+.0%} | "
              f"{float((adopt*w).sum()):.2f} (linear {float((adopt_lin*w).sum()):.2f}) | {float((adopt[top]*w[top]).sum()/w[top].sum()):.2f}")
        if A == 0.9:
            ad = np.where(adopt)[0]
            print(f"      menu at A=0.9: {len(set(assign[ad]))} distinct items for {len(ad)} adopting types; "
                  f"T range {T[assign[ad]-1].min():.1f}-{T[assign[ad]-1].max():.1f}; f range {f[ad].min():.2f}-{f[ad].max():.2f}; "
                  f"monotone T(f): {bool((np.diff(assign[ad]) >= 0).all())}")
