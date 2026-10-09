"""Theory vs numerics for G-level price schedules (paper_notes/theory.md, Section 6).

Quadratic regime: W_k(p) ~ W_k(p_k*) - omega_k (p - p_k*)^2 / 2, omega_k = kappa_k (1 + kappa_k t'(lam_k*)).  A schedule with G price levels groups the
phases; the loss is half the weighted within-group sum of squares of the first-best prices p_k*, with weights pi_k omega_k.  Predicted share of the flat-price loss
recovered by the best G-level schedule:  R_G = between-group / total weighted variance (1-D optimal clustering, groups contiguous in p*).
Bounds: R_2 >= (E|X - mean| / sd)^2 (weighted) and R_G >= 1 - (b - a)^2 / (4 G^2 sd^2).
Compared with the exact quasi-static recovery computed from the full welfare curves (dynamic programme over contiguous groups, price grid).
Usage: python two_level_theory.py"""
import numpy as np

import theory_check as th
import theory_props as tpr
from schedule_test import profile_from
from trace_calibration import table

P_ORIG = th.P


def quad_inputs(Lams, pis, c):
    lfb = np.array([th.first_best(L, c) for L in Lams])
    h = 1e-4
    dp = np.array([(th.sojourn(l + h, c) - th.sojourn(l - h, c)) / (2 * h) for l in lfb])
    kap = 1.0 / (th.P / Lams + dp)
    tpr_ = np.array([(tpr.toll_at(l + 1e-3, c) - tpr.toll_at(l - 1e-3, c)) / 2e-3 for l in lfb])
    om = kap * (1 + kap * tpr_)
    ps = np.array([tpr.toll_at(l, c) for l in lfb])
    return ps, om


def best_partition_sse(x, w, G):
    """Optimal contiguous G-partition of sorted points x with weights w (1-D k-means by DP); returns within-SSE."""
    n = len(x)
    cw, cwx, cwx2 = np.cumsum(w), np.cumsum(w * x), np.cumsum(w * x * x)
    def sse(i, j):  # points i..j-1
        W = cw[j - 1] - (cw[i - 1] if i else 0.0)
        S = cwx[j - 1] - (cwx[i - 1] if i else 0.0)
        S2 = cwx2[j - 1] - (cwx2[i - 1] if i else 0.0)
        return S2 - S * S / W
    INF = 1e300
    dp = np.full((G + 1, n + 1), INF)
    dp[0, 0] = 0.0
    for g in range(1, G + 1):
        for j in range(g, n + 1):
            dp[g, j] = min(dp[g - 1, i] + sse(i, j) for i in range(g - 1, j))
    return dp[G, n]


def exact_recovery(Lams, pis, c, Gs):
    K = len(Lams)
    grid = np.linspace(0, th.P, 81)
    Wt = np.array([[th.w_phase(th.eq_rate(p, L, c), L, c) for p in grid] for L in Lams]) * pis[:, None]
    order = np.argsort(Lams)
    Ws = Wt[order]
    wfb = sum(pis[k] * th.w_phase(th.first_best(Lams[k], c), Lams[k], c) for k in range(K))
    cost = np.zeros((K + 1, K + 1))
    for i in range(K):
        for j in range(i + 1, K + 1):
            cost[i, j] = Ws[i:j].sum(0).max()
    out = {}
    INF = -1e300
    dp = np.full((max(Gs) + 1, K + 1), INF)
    dp[0, 0] = 0.0
    for g in range(1, max(Gs) + 1):
        for j in range(g, K + 1):
            dp[g, j] = max(dp[g - 1, i] + cost[i, j] for i in range(g - 1, j))
    loss = lambda G: wfb - dp[G, K]
    return {G: loss(G) for G in Gs}


def main():
    prof = profile_from("results/longtrace_azure.md")
    K, c = len(prof), 77
    pis = np.full(K, 1.0 / K)
    rows, gro = [], []
    for P, over, share in ((20, 1.4, 0.0), (20, 1.4, 0.15), (10, 1.2, 0.0), (40, 2.0, 0.0)):
        th.P = P - share * P
        try:
            Lams = over * c * prof / prof.mean()
            ps, om = quad_inputs(Lams, pis, c)
            order = np.argsort(ps)
            x, w = ps[order], (pis * om)[order]
            tot = best_partition_sse(x, w, 1)
            R = {G: 1 - best_partition_sse(x, w, G) / tot for G in (2, 3, 4, 6)}
            mu = (w * x).sum() / w.sum()
            q = w / w.sum()
            mad, sd = (q * np.abs(x - mu)).sum(), np.sqrt((q * (x - mu) ** 2).sum())
            lb2 = (mad / sd) ** 2
            lbG = {G: 1 - (x.max() - x.min()) ** 2 / (4 * G * G * sd ** 2) for G in (2, 3, 4, 6)}
            ex = exact_recovery(Lams, pis, c, (1, 2, 3, 4, 6))
            Rex = {G: 1 - ex[G] / ex[1] for G in (2, 3, 4, 6)}
            rows.append([P, over, share, f"{om.min():.3f}-{om.max():.3f}", f"{lb2:.2f}", f"{R[2]:.2f}", f"{Rex[2]:.2f}",
                         f"{R[3]:.2f} / {Rex[3]:.2f}", f"{R[4]:.2f} / {Rex[4]:.2f}", f"{R[6]:.2f} / {Rex[6]:.2f}"])
            print(rows[-1], flush=True)
        finally:
            th.P = P_ORIG
    md = ["# Theory vs numerics: share of the flat-price loss recovered by a G-level schedule\n",
          "Azure 2024 hour-of-day profile (24 equally likely phases), c = 77, quasi-static. 'quad' = prediction from the quadratic (local) theory with weights pi_k omega_k; "
          "'exact' = dynamic programme over contiguous groups on the full welfare curves.\n",
          table(rows, ["P", "unpriced / capacity", "c0/P", "omega range", "lower bound (MAD/sd)^2", "G=2 quad", "G=2 exact",
                       "G=3 quad / exact", "G=4 quad / exact", "G=6 quad / exact"]), ""]
    open("results/two_level_theory.md", "w").write("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()
