"""How much of the gain from time-varying prices can schedules with the price ratios seen in real list prices capture?

Real structures (verified on the providers' pages, accessed 2026-10-09):
  DeepSeek: peak = 2x off-peak, peak windows 01-04 and 06-10 UTC Mon-Fri (= 09-12 and 14-18 China time), i.e. 7 weekday hours.
  OpenAI: Fast 2x, Batch/Flex 0.5x, Ultrafast 6x (relative to Standard).
Test: 24 hour-of-day phases from the Azure 2024 code trace (results/longtrace_azure.md), quasi-static model, serving cost c0 per request
(prices paid = c0 + toll).  Policies: no price, best flat, best two-level schedule with free prices, best schedule with the full
price ratio fixed at r (peak = r x off-peak) with the best number of peak hours, and the DeepSeek-like 7-peak-hour schedule at r = 2.
Loss is % of welfare below the hour-by-hour first best.  Usage: python schedule_test.py [results/longtrace_azure.md]"""
import re
import sys

import numpy as np

import theory_check as th
from trace_calibration import table

P0 = th.P


def profile_from(md_path):
    txt = open(md_path).read()
    line = re.search(r"profile \(x mean\): ([0-9., ]+)", txt).group(1)
    return np.array([float(x) for x in line.split(",")])


def run(prof, c, c0, md):
    th.P = P0 - c0
    try:
        K = len(prof)
        Lams = 1.4 * c * prof / prof.mean()
        grid = np.linspace(0, th.P, 161)
        Wt = np.array([[th.w_phase(th.eq_rate(p, L, c), L, c) for p in grid] for L in Lams]) / K
        wfb = sum(th.w_phase(th.first_best(L, c), L, c) for L in Lams) / K
        order = np.argsort(-Lams)  # peak hours first
        Wf = lambda k, p: np.interp(p, grid, Wt[k])
        wnone = Wt[:, 0].sum()
        wflat = Wt.sum(0).max()
        best_free = max(Wt[order[m:]].sum(0).max() + Wt[order[:m]].sum(0).max() for m in range(1, K))

        def constrained(r, ms):
            best = (-1e18, None)
            for m in ms:
                pk, of = order[:m], order[m:]
                for po in grid:
                    ph = r * (c0 + po) - c0
                    if ph > grid[-1] or ph < 0:
                        continue
                    v = sum(Wf(k, po) for k in of) + sum(Wf(k, ph) for k in pk)
                    if v > best[0]:
                        best = (v, (m, po, ph))
            return best
        loss = lambda w: 100 * (wfb - w) / abs(wfb)
        row = [c0, f"{loss(wnone):.1f}%", f"{loss(wflat):.1f}%", f"{loss(best_free):.1f}%"]
        for r in (1.5, 2.0, 4.0, 6.0):
            v, par = constrained(r, range(2, 20))
            row.append(f"{loss(v):.1f}% ({par[0]}h)" if par else "-")
        v7, par7 = constrained(2.0, [7])
        row.append(f"{loss(v7):.1f}%" if par7 else "-")
        return row
    finally:
        th.P = P0


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "results/longtrace_azure.md"
    prof = profile_from(path)
    c = 77
    rows = [run(prof, c, c0, None) for c0 in (0.0, 4.0, 8.0)]
    md = ["# Schedules with real list-price ratios (Azure 2024 hour-of-day profile, c=77, quasi-static)\n",
          "Loss (% of welfare) relative to hour-by-hour first-best prices; 'h' = number of peak hours chosen.\n",
          table(rows, ["c0", "no price", "best flat", "free 2-level", "ratio 1.5x", "ratio 2x", "ratio 4x", "ratio 6x",
                       "2x with 7 peak h (DeepSeek-like)"]), ""]
    open("results/schedule_test.md", "w").write("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()
