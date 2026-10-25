"""Menu pricing baseline (cf. Bergemann, Bonatti & Smolin) in the testing-service model.

Firms differ in the cost f of a residual fault (private information). A firm of stakes f using the AI tool with
testing budget T gets benefit  B(T; f) = f*A*a*(1-exp(-B*b*T)) - c0*T  (c0 = its own cost per unit), and has the
outside option of the human technology, worth S_H(f). The vendor's cost per unit T is k.

Screening problem (direct mechanism, random allocations allowed => the LP value is an UPPER BOUND on any menu):
  max  sum_i w_i * (t_i - k * sum_j pi_ij T_j)
  s.t. IC:  u_i(i) >= u_i(m) for all types i,m  (u_i(m) = sum_j pi_mj B(T_j;f_i) + pi_m0 S_H(f_i) - t_m)
       IR:  u_i(i) >= S_H(f_i)
Compared with the best linear usage price p (firm picks T freely).

Run: python3 vendor_menu.py
"""
import numpy as np
from scipy.optimize import linprog
from scipy.sparse import lil_matrix
import vendor_model as VM

a, b, Bs, c0, kv = VM.a, VM.b, VM.B, VM.c0, VM.kv
h = VM.h


def setup(A, nI=60, nJ=41, Tmax=40.0):
    f = np.exp(np.linspace(np.log(0.1), np.log(60.0), nI))
    dens = np.exp(-0.5 * ((np.log(f) - VM.MU) / VM.SIG) ** 2) / (f * VM.SIG * np.sqrt(2 * np.pi))
    w = dens * np.gradient(f); w = w / w.sum()
    T = np.linspace(0.0, Tmax, nJ)[1:]                           # purchasable budgets (T>0)
    SH = f * a * h(a * b * f / 1.0)                              # human net saving
    Bf = f[:, None] * A * a * (1 - np.exp(-Bs * b * T[None, :])) - c0 * T[None, :]     # I x J benefit
    return f, w, T, SH, Bf


def linear_best(A, f, w, SH, ps=np.linspace(0.12, 3.0, 300)):
    best = (0, None, None)
    for p in ps:
        cL = c0 + p
        SL = f * (A * a) * h(A * a * Bs * b * f / cL)
        adopt = SL > SH + 1e-9
        Ts = VM.Tstar(A * a, Bs * b, cL, f)
        prof = float((adopt * (p - kv) * Ts * w).sum())
        if prof > best[0]:
            best = (prof, p, adopt)
    return best


def menu_lp(A, f, w, T, SH, Bf):
    I, J = Bf.shape
    nv = I * (J + 1) + I                                         # pi_i0..pi_iJ , t_i
    idx_pi = lambda i, j: i * (J + 1) + j                        # j=0 is the "keep human" option
    idx_t = lambda i: I * (J + 1) + i
    c = np.zeros(nv)
    for i in range(I):
        for j in range(1, J + 1):
            c[idx_pi(i, j)] = w[i] * kv * T[j - 1]               # minimise -profit
        c[idx_t(i)] = -w[i]
    def util_row(i, m, row):                                     # coefficients of u_i(m) in the variables
        row[idx_pi(m, 0)] += SH[i]
        for j in range(1, J + 1):
            row[idx_pi(m, j)] += Bf[i, j - 1]
        row[idx_t(m)] += -1.0
    rows = []
    A_ub = lil_matrix((I * (I - 1) + I, nv)); b_ub = np.zeros(I * (I - 1) + I); r = 0
    for i in range(I):
        for m in range(I):
            if m == i: continue
            tmp = {}
            # constraint: u_i(m) - u_i(i) <= 0
            for (mm, sgn) in ((m, 1.0), (i, -1.0)):
                A_ub[r, idx_pi(mm, 0)] += sgn * SH[i]
                for j in range(1, J + 1):
                    A_ub[r, idx_pi(mm, j)] += sgn * Bf[i, j - 1]
                A_ub[r, idx_t(mm)] += -sgn
            r += 1
    for i in range(I):                                           # IR: SH_i - u_i(i) <= 0
        A_ub[r, idx_pi(i, 0)] += -SH[i]
        for j in range(1, J + 1):
            A_ub[r, idx_pi(i, j)] += -Bf[i, j - 1]
        A_ub[r, idx_t(i)] += 1.0
        b_ub[r] = -SH[i]; r += 1
    A_eq = lil_matrix((I, nv)); b_eq = np.ones(I)
    for i in range(I):
        for j in range(0, J + 1):
            A_eq[i, idx_pi(i, j)] = 1.0
    bounds = [(0, None)] * (I * (J + 1)) + [(None, None)] * I
    res = linprog(c, A_ub=A_ub.tocsr(), b_ub=b_ub, A_eq=A_eq.tocsr(), b_eq=b_eq, bounds=bounds, method="highs")
    if not res.success:
        return None
    x = res.x
    pi = np.array([[x[idx_pi(i, j)] for j in range(J + 1)] for i in range(I)])
    t = np.array([x[idx_t(i)] for i in range(I)])
    return -res.fun, pi, t


if __name__ == "__main__":
    print(f"vendor compute cost k={kv}, firm own cost c0={c0}, B={Bs}; stakes f ~ lognormal(median 2, sigma 0.9)")
    print(" A   | linear: p*   profit  adopter share | menu (LP upper bound): profit  adopter share | gain | top-decile adopters (linear / menu)")
    for A in (0.8, 0.9, 1.0):
        f, w, T, SH, Bf = setup(A)
        lin_profit, p_star, adopt_lin = linear_best(A, f, w, SH)
        out = menu_lp(A, f, w, T, SH, Bf)
        if out is None:
            print(f" {A}: LP failed"); continue
        prof, pi, t = out
        adopt_menu = pi[:, 0] < 0.5
        cum = np.cumsum(w); top = cum > 0.9
        topw = w[top] / w[top].sum()
        print(f" {A:.1f} |  {p_star:.2f}  {lin_profit:7.3f}   {float((adopt_lin * w).sum()):.2f}        |   {prof:7.3f}    {float((adopt_menu * w).sum()):.2f}      "
              f"| {prof / lin_profit - 1:+.0%} | {float((adopt_lin[top] * topw).sum()):.2f} / {float((adopt_menu[top] * topw).sum()):.2f}")
        if A == 0.9:
            ad = np.where(adopt_menu)[0]
            tot = [(pi[i, 1:] * T).sum() for i in ad]
            print(f"      menu at A=0.9: adopters f in [{f[ad].min():.2f}, {f[ad].max():.2f}], "
                  f"expected T from {min(tot):.1f} to {max(tot):.1f}; types with randomised allocation: "
                  f"{int(((pi[ad][:, 1:] > 1e-6).sum(1) > 1).sum())} of {len(ad)}")
