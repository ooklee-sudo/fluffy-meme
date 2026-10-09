"""Robustness of the main claim (flat price loses welfare against time-varying prices; a two-level schedule recovers most of the gap)
to the assumed choke value P, the unpriced-demand ratio and the serving-cost share c0/P.  Azure 2024 hour-of-day profile (24 phases),
quasi-static model, c = 77.  Loss = % of the welfare of hour-by-hour first-best prices.  Usage: python robustness.py"""
import numpy as np

import theory_check as th
from schedule_test import profile_from
from trace_calibration import table


def losses(prof, c, P, over, c0):
    th.P = P - c0
    try:
        K = len(prof)
        Lams = over * c * prof / prof.mean()
        grid = np.linspace(0, th.P, 81)
        Wt = np.array([[th.w_phase(th.eq_rate(p, L, c), L, c) for p in grid] for L in Lams]) / K
        wfb = sum(th.w_phase(th.first_best(L, c), L, c) for L in Lams) / K
        order = np.argsort(-Lams)
        w2 = max(Wt[order[:m]].sum(0).max() + Wt[order[m:]].sum(0).max() for m in range(1, K))
        L = lambda w: 100 * (wfb - w) / abs(wfb)
        flat, none = L(Wt.sum(0).max()), L(Wt[:, 0].sum())
        return none, flat, L(w2), 100 * (flat - L(w2)) / flat if flat > 0.05 else float("nan")
    finally:
        th.P = P_ORIG


P_ORIG = th.P


def main():
    prof = profile_from("results/longtrace_azure.md")
    rows = []
    for P in (10, 20, 40):
        for over in (1.2, 1.4, 2.0):
            for share in (0.0, 0.15):
                n, f, t, rec = losses(prof, 77, P, over, share * P)
                rows.append([P, over, share, f"{n:.1f}%", f"{f:.1f}%", f"{t:.1f}%", f"{rec:.0f}%"])
                print(rows[-1], flush=True)
    md = ["# Robustness (Azure 2024 hour-of-day profile, c=77, quasi-static)\n",
          "Loss relative to hour-by-hour first-best prices; 'recovered' = share of the flat-price loss removed by the best two-level schedule.\n",
          table(rows, ["P", "unpriced demand / capacity", "c0/P", "no price", "best flat", "best two-level", "gap recovered by two-level"]), ""]
    open("results/robustness.md", "w").write("\n".join(md))


if __name__ == "__main__":
    main()
