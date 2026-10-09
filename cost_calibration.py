"""Add a marginal serving cost c0 per request (same units as P: service times of user delay cost) and ask what
c0 reproduces the peak/off-peak price ratios seen in the market (2x: DeepSeek time-of-day; up to 4x: priority vs flex),
and what the flat-price welfare loss is at that c0.

With cost c0 the planner's net marginal value is P_k(lam) - c0, i.e. the choke value becomes P - c0; users pay
c0 + p_k, where p_k is the congestion toll.  Quasi-static model of theory_check.py.  Usage: python cost_calibration.py DATA_DIR"""
import sys

import numpy as np

import theory_check as th
import theory_props as tpr

P0 = th.P


def at(c0, Lams, pis, c):
    th.P = P0 - c0
    try:
        r = th.analyse_qs(Lams, pis, c)
    finally:
        th.P = P0
    tol = r["tol"]
    return dict(ratio=(c0 + tol.max()) / (c0 + tol.min()), loss=100 * r["loss"] / abs(r["wfb"]),
                tmax=tol.max(), tmin=tol.min(), pflat=r["pflat"] + c0, wfb=r["wfb"])


def main():
    data = sys.argv[1]
    md = ["# Marginal-cost calibration of the peak/off-peak price ratio\n",
          "Prices include the serving cost c0 (units: service times of user delay cost; choke value P = 20).\n"]
    for name, sc in (("Code trace (c=7)", th.scenario_code), ("Conversation trace (c=45)", th.scenario_conv)):
        lam_s, G, c = sc(data)
        Lams, pis = th.lam_potential(lam_s, G, c, 1.0)
        rows = []
        res = []
        for c0 in (0, 2, 4, 6, 8, 10, 12, 14, 16, 18):
            r = at(c0, Lams, pis, c)
            res.append((c0, r))
            rows.append([c0, f"{r['tmin']:.2f} / {r['tmax']:.2f}", f"{r['ratio']:.1f}x", f"{r['pflat']:.1f}", f"{r['loss']:.1f}%"])
        md.append(f"## {name}\n")
        md.append(__import__("trace_calibration").table(rows, ["c0", "tolls off-peak / peak", "price ratio (peak/off-peak)",
                                                                  "best flat price (incl. c0)", "flat-price loss % of first best"]))
        # c0 at which ratio first drops to 4x and 2x
        for target in (4.0, 2.0):
            hit = next(((a, ra, b, rb) for (a, ra), (b, rb) in zip(res, res[1:]) if ra["ratio"] >= target > rb["ratio"]), None)
            if hit:
                a, ra, b, rb = hit
                w = (ra["ratio"] - target) / (ra["ratio"] - rb["ratio"])
                md.append(f"\nPrice ratio {target:.0f}x is reached at c0 ~ {a + w * (b - a):.1f} "
                          f"(flat loss there ~ {ra['loss'] + w * (rb['loss'] - ra['loss']):.1f}% of first best).")
            else:
                md.append(f"\nPrice ratio {target:.0f}x not bracketed on this grid.")
        md.append("")
        print("\n".join(md[-6:]), flush=True)
    open("results/cost_calibration.md", "w").write("\n".join(md))


if __name__ == "__main__":
    main()
