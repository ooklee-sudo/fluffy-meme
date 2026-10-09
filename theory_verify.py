"""Numerical check of the local (second-order) loss formula in paper_notes/theory.md, Proposition 4.

  Loss(flat) ~= 1/2 * sum_k pi_k w_k (p_k* - pbar)^2,   w_k = kappa_k (1 + kappa_k t'(lam_k*)),
  pbar = sum pi_k w_k p_k* / sum pi_k w_k,   p_k* = t(lam_k*),   kappa_k = 1/(P/Lam_k + d'(lam_k*)).
Compared with the exact quasi-static loss for small demand spreads.  Usage: python theory_verify.py DATA_DIR"""
import sys

import numpy as np

import theory_check as th
import theory_props as tpr


def approx_and_exact(Lams, pis, c):
    K = len(Lams)
    lfb = np.array([th.first_best(L, c) for L in Lams])
    h = 1e-4
    dprime = np.array([(th.sojourn(l + h, c) - th.sojourn(l - h, c)) / (2 * h) for l in lfb])
    kap = 1.0 / (th.P / Lams + dprime)
    tprime = np.array([(tpr.toll_at(l + 1e-3, c) - tpr.toll_at(l - 1e-3, c)) / 2e-3 for l in lfb])
    w = kap * (1 + kap * tprime)
    pstar = np.array([tpr.toll_at(l, c) for l in lfb])
    pbar = float((pis * w) @ pstar / (pis * w).sum())
    approx = 0.5 * float(pis @ (w * (pstar - pbar) ** 2))
    r = th.analyse_qs(Lams, pis, c)
    return approx, r["loss"], r["harb"]


def main():
    data = sys.argv[1]
    out = ["# Check of Proposition 4 (local loss formula)\n",
           "| trace | spread | exact loss | corrected 2nd-order | old formula (kappa only) |", "|---|---|---|---|---|"]
    for name, sc in (("code", th.scenario_code), ("conversation", th.scenario_conv)):
        lam_s, G, c = sc(data)
        for spread in (0.02, 0.05, 0.1, 0.2, 0.3):
            Lams, pis = th.lam_potential(lam_s, G, c, spread)
            a, e, old = approx_and_exact(Lams, pis, c)
            out.append(f"| {name} | {spread} | {e:.4f} | {a:.4f} | {old:.4f} |")
            print(out[-1], flush=True)
    open("results/theory_verify.md", "w").write("\n".join(out))


if __name__ == "__main__":
    main()
