"""Estimate the serving-cost parameter c0 implied by an observed peak/off-peak price ratio (DeepSeek: 2x).

Identification: list prices are in dollars, the model's delay cost and choke value P are in units of user time, and the value of user
time is not observed, so the PRICE LEVEL cannot identify c0.  What the price RATIO identifies (given the demand profile) is
c0/P: the share of the marginal user's value that is serving cost.  For each parameter set we find the c0 at which the best free two-level
schedule (hours split into peak / off-peak, prices chosen to maximise welfare) has full-price ratio (c0 + toll_peak)/(c0 + toll_off) equal to
the target, quasi-static model, Azure 2024 hour-of-day profile (results/longtrace_azure.md).
Usage: python c0_estimate.py"""
import sys

import numpy as np

import theory_check as th
from schedule_test import profile_from
from trace_calibration import table


def ratio(c0, P, over, c, prof, ngrid=81):
    th.P = P - c0
    try:
        K = len(prof)
        Lams = over * c * prof / prof.mean()
        grid = np.linspace(0, th.P, ngrid)
        Wt = np.array([[th.w_phase(th.eq_rate(p, L, c), L, c) for p in grid] for L in Lams])
        order = np.argsort(-Lams)
        best = (-1e18, None)
        for m in range(1, K):
            wh, wo = Wt[order[:m]].sum(0), Wt[order[m:]].sum(0)
            v = wh.max() + wo.max()
            if v > best[0]:
                best = (v, (m, grid[wo.argmax()], grid[wh.argmax()]))
        m, po, ph = best[1]
        return (c0 + ph) / (c0 + po), m, po, ph
    finally:
        th.P = th.P if False else th.P


def solve(P, over, c, prof, targets):
    fr = np.linspace(0.0, 0.7, 15)
    res = []
    for f in fr:
        th_P_backup = th.P
        th.P = P
        r, m, po, ph = ratio(f * P, P, over, c, prof)
        th.P = th_P_backup
        res.append((f, r, m))
    out = {}
    for tg in targets:
        hit = next(((a, b) for a, b in zip(res, res[1:]) if a[1] >= tg > b[1]), None)
        if hit:
            (f0, r0, m0), (f1, r1, m1) = hit
            w = (r0 - tg) / (r0 - r1)
            out[tg] = (f0 + w * (f1 - f0), m0)
        else:
            out[tg] = (None, None)
    return out, res


def main():
    prof = profile_from("results/longtrace_azure.md")
    P_ORIG = th.P
    rows = []
    cases = [(20, 1.4, 77), (10, 1.4, 77), (40, 1.4, 77), (20, 1.2, 77), (20, 2.0, 77), (20, 1.4, 108), (20, 1.4, 64)]
    for P, over, c in cases:
        th.P = P
        out, res = solve(P, over, c, prof, [2.0, 1.5, 4.0])
        th.P = P_ORIG
        fmt = lambda t: "-" if out[t][0] is None else f"{out[t][0]:.2f} ({out[t][1]}h)"
        rows.append([P, over, c, f"{res[0][1]:.1f}x ({res[0][2]}h)", fmt(2.0), fmt(1.5), fmt(4.0)])
        print(rows[-1], flush=True)
    md = ["# Implied serving-cost share c0/P from observed peak/off-peak ratios\n",
          "Azure 2024 hour-of-day profile, quasi-static model. Entry = c0/P at which the model's best two-level schedule has the stated price ratio "
          "(number of peak hours in parentheses). First ratio column = ratio at c0 = 0.\n",
          table(rows, ["P (choke value)", "unpriced demand / capacity", "c", "ratio at c0=0", "c0/P for 2x (DeepSeek)", "c0/P for 1.5x", "c0/P for 4x"]), ""]
    open("results/c0_estimate.md", "w").write("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()
