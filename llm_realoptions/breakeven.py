"""Break-even analysis for the flexibility premium, and paired comparison of switching rules.
Flex cost is linear in the premium, so the break-even premium (person-weeks) is the mean paired cost difference
rigid - flex(premium 0), divided by one person-week. Reported per scenario with a 95% interval over simulated lifecycles.
usage: python breakeven.py [--n 10000] [--out breakeven.md]
"""
import argparse, math
import numpy as np
from sim import run, WEEK


def ci(d):
    m = d.mean(); se = d.std(ddof=1) / math.sqrt(len(d)); return m, m - 1.96 * se, m + 1.96 * se


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=10000); ap.add_argument("--out", default="breakeven.md")
    a = ap.parse_args(); L = []
    L.append("## Break-even flexibility premium (person-weeks), by effort reduction, vendor-price correlation and volume\n")
    L.append("Premium below the value is worth paying: expected saving over 36 months from halving (phi) the migration effort and choosing the cheaper vendor at retirement, no early switching.\n")
    L.append("| Tokens/month | Alt. price correlation | phi=0.3 | phi=0.5 | phi=0.8 |\n|---|---|---|---|---|")
    for vol in (100, 1000, 10000):
        for corr in (0.0, 0.5, 1.0):
            cells = []
            for phi in (0.3, 0.5, 0.8):
                o = run(a.n, vol_m_tokens=vol, corr_alt=corr, phi=phi, premium_w=0.0)
                m, lo, hi = ci((o["rigid"] - o["flex"]) / WEEK); cells.append(f"{m:.1f} [{lo:.1f}, {hi:.1f}]")
            L.append(f"| {vol} M | {corr} | " + " | ".join(cells) + " |")
    L.append("\n## Break-even with no price shock at retirement (successor price unchanged), labor effect only\n")
    L.append("| Effort (triangular weeks) | phi=0.3 | phi=0.5 | phi=0.8 |\n|---|---|---|---|")
    for kw in ((2, 4, 10), (4, 8, 20)):
        cells = []
        for phi in (0.3, 0.5, 0.8):
            o = run(a.n, succ_ratio=1.0, phi=phi, kw=kw, premium_w=0.0)
            m, lo, hi = ci((o["rigid"] - o["flex"]) / WEEK); cells.append(f"{m:.1f} [{lo:.1f}, {hi:.1f}]")
        L.append(f"| {kw} | " + " | ".join(cells) + " |")
    o = run(a.n, premium_w=6.0)
    L.append(f"\nMean number of forced retirements in 36 months (base): {o['forced'].mean():.2f}.\n")
    L.append("## Switching rules: threshold (real-options) versus simple net-present-value rule, paired difference in cost (USD, positive = threshold cheaper)\n")
    L.append("| Scenario | NPV rule cost | Threshold cost | Difference [95% CI] | Early switches NPV | Early switches threshold |\n|---|---|---|---|---|---|")
    for lab, kw in (("price-gap volatility 0.05/month (theta 1.5)", dict(sig_m=0.05)), ("0.10 (theta 2.1)", dict(sig_m=0.10)),
                    ("0.20 (theta 4.2)", dict(sig_m=0.20)), ("0.36 (theta 9.7)", dict(sig_m=0.36)),
                    ("0.10, no price shock at retirement", dict(succ_ratio=1.0))):
        o = run(a.n, **kw); d = o["flex_npv"] - o["flex_ro"]; m, lo, hi = ci(d)
        L.append(f"| {lab} | {o['flex_npv'].mean():,.0f} | {o['flex_ro'].mean():,.0f} | {m:,.0f} [{lo:,.0f}, {hi:,.0f}] | {o['sw_flex_npv'].mean():.1f} | {o['sw_flex_ro'].mean():.1f} |")
    t = "\n".join(L) + "\n"; print(t); open(a.out, "w").write(t)


if __name__ == "__main__":
    main()
