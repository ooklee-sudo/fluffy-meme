"""Flat-price loss as a function of the switching speed (exact CTMC, code-trace MMPP with dwell times scaled by f).

Theory (paper_notes/theory.md, Section 5): as f -> 0 (fast switching) the queue sees only the average rate, all phases face the
same externality, and a flat price is first best, so the loss -> 0; the rate of convergence is not proved; the measured log-log slope is about 1.
Output: loss of the best flat price (equilibrium demand) relative to the phase-dependent planner optimum, and the log-log slope.
Usage: python switching_scaling.py DATA_DIR [OUT.md]"""
import sys

import numpy as np

import theory_check as th
import trace_calibration as tc
import trace_equilibrium as te
import trace_pricing as tp

P = tp.PBAR


def loss_at(lam_s, G, c, f):
    pi = tp.stationary(G)
    Lams = lam_s * tp.OVER * c / (pi @ lam_s)
    Gf = G / f
    N = c + int(300 + 2200 * min(f, 1.0) ** 0.5)
    wflat, pflat, lam_prev = -1e18, 0.0, None
    for p in np.linspace(0, 16, 17):
        lam, q = te.equilibrium(p, Lams, Gf, c, N, lam_prev)
        lam_prev = lam
        w = te.welfare(lam, Lams, pi, q)
        if q.top_mass() < 1e-3 and w > wflat:
            wflat, pflat = w, p
    W = lambda tt: tp.welfare(Lams * np.clip(1 - np.asarray(tt) / P, 0, 1), Lams, Gf, c, N, pi)
    best = max((W([a, b]), a, b) for a in np.linspace(0, P, 11) for b in np.linspace(0, P, 11))
    _, a0, b0 = best
    best = max((W([a, b]), a, b) for a in np.linspace(max(a0 - 2, 0), a0 + 2, 9) for b in np.linspace(max(b0 - 2, 0), b0 + 2, 9))
    return wflat, pflat, best[0], 100 * (best[0] - wflat) / abs(best[0])


def main():
    data = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "results/switching_scaling.md"
    lam_s, G, c = th.scenario_code(data)
    rows, fs, ls = [], [], []
    for f in (0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0):
        wf, pf, wp, l = loss_at(lam_s, G, c, f)
        fs.append(f); ls.append(l)
        rows.append([f, f"{1 / (-G[0, 0] / f):.2f}", f"{wf:.2f} (p={pf:.0f})", f"{wp:.2f}", f"{l:.2f}%"])
        print(rows[-1], flush=True)
    sl = np.polyfit(np.log(fs[:4]), np.log(np.maximum(ls[:4], 1e-9)), 1)[0]
    md = ["# Flat-price loss vs. switching speed (code-trace MMPP, exact CTMC)\n",
          tc.table(rows, ["f (dwell multiplier)", "mean burst (service times)", "best flat welfare", "phase-dependent welfare", "flat loss"]),
          f"\nLog-log slope of the loss against f over f = {fs[0]}..{fs[3]}: {sl:.2f} (about 1 means roughly linear in f).\n"]
    open(out, "w").write("\n".join(md))
    print(md[-1])


if __name__ == "__main__":
    main()
