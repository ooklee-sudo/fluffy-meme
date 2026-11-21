"""Numerical checks of the propositions in Section 2.6 of the manuscript, and the illustrative calibration.

  python quant_cost/paper/model_check.py

Model. A buyer perceives the expected exposure loss as w(lam) * L with
    w(lam) = lam0 * m * (lam / lam0) ** gamma ,   0 < gamma <= 1, m > 0,
where lam0 = D / L is the break-even probability of a risk-neutral buyer (D = E - B, the local model's net cost
disadvantage). The benchmark is m = 1 and gamma = 1.
  Proposition 1: the buyer chooses the local model iff w(lam) L > D, so the behavioral break-even is
                 lam_tilde = lam0 * m ** (-1 / gamma); lam_tilde < lam0 iff m > 1.
  Proposition 2: a vendor that sets the highest price the buyer accepts bears w(lam(s)) L, so its marginal reward for
                 reducing the true probability is scaled by w'(lam) = gamma * m * (lam/lam0) ** (gamma - 1);
                 w' < 1 iff lam > lam_bar = lam0 * (gamma * m) ** (1 / (1 - gamma)).
  Vendor example: lam(s) = lam_b * exp(-theta * s), cost C(s) = c * s**2 / 2.
"""
import math
import random

import numpy as np
from scipy import optimize
from scipy.special import lambertw


def w(lam, lam0, m, g):
    return lam0 * m * (lam / lam0) ** g


def breakeven_numeric(lam0, m, g):
    # solve w(lam) = lam0 (the buyer is indifferent when perceived expected loss equals D, and D/L = lam0)
    return optimize.brentq(lambda x: w(x, lam0, m, g) - lam0, 1e-12, 1.0)


def breakeven_closed(lam0, m, g):
    return lam0 * m ** (-1.0 / g)


def lam_bar(lam0, m, g):
    return lam0 * (g * m) ** (1.0 / (1.0 - g))


def vendor_opt(lam_b, theta, c, L, lam0, m, g, behavioral=True):
    """Minimise  w(lam(s)) L + C(s)  (behavioral)  or  lam(s) L + C(s)  (rational)  over s >= 0."""
    if behavioral:
        f = lambda s: w(lam_b * math.exp(-theta * s), lam0, m, g) * L + c * s * s / 2
    else:
        f = lambda s: lam_b * math.exp(-theta * s) * L + c * s * s / 2
    return optimize.minimize_scalar(f, bounds=(0, 200), method="bounded", options={"xatol": 1e-10}).x


def main():
    random.seed(1)
    # ---- Proposition 1: closed form equals the numerical root; the sign condition
    worst = 0.0; n_ok = 0
    for _ in range(2000):
        lam0 = random.uniform(0.005, 0.2); g = random.uniform(0.1, 1.0); m = random.uniform(0.5, 3.0)
        b = breakeven_closed(lam0, m, g)
        if b >= 1.0:   # with m < 1 the break-even can exceed 1: the buyer then never chooses the local model
            continue
        a = breakeven_numeric(lam0, m, g)
        worst = max(worst, abs(a - b) / b)
        assert (b < lam0) == (m > 1) or abs(m - 1) < 1e-9
        n_ok += 1
    print(f"Proposition 1: closed form matches the root in {n_ok} random cases with a break-even below 1 (max relative error {worst:.1e}); "
          "lam_tilde < lam0 exactly when m > 1")
    # monotonicity: for m > 1 a lower gamma lowers the break-even further
    lam0 = 0.04
    for m in (1.1, 1.3, 2.0):
        vals = [breakeven_closed(lam0, m, g) for g in (1.0, 0.8, 0.6, 0.4)]
        assert all(x > y for x, y in zip(vals, vals[1:]))
    print("  for m > 1 the break-even falls as gamma falls (checked at m = 1.1, 1.3, 2.0)")

    # ---- Proposition 2: derivative and threshold
    bad = 0
    for _ in range(2000):
        lam0 = random.uniform(0.005, 0.2); g = random.uniform(0.1, 0.95); m = random.uniform(0.5, 3.0)
        lb = lam_bar(lam0, m, g)
        lam = random.uniform(1e-4, 0.9)
        wp = g * m * (lam / lam0) ** (g - 1)
        num = (w(lam * (1 + 1e-6), lam0, m, g) - w(lam, lam0, m, g)) / (lam * 1e-6)
        assert abs(num - wp) / wp < 1e-4
        if (wp < 1) != (lam > lb):
            bad += 1
    print(f"Proposition 2: w' formula and the threshold lam_bar verified in 2000 random cases (mismatches: {bad})")
    # lower gamma lowers the marginal incentive for lam >= lam0 * exp(-1/gamma)
    cnt = 0
    for _ in range(2000):
        lam0 = random.uniform(0.01, 0.1); m = random.uniform(0.5, 3.0)
        g1 = random.uniform(0.3, 0.9); g2 = g1 - random.uniform(0.01, 0.25)
        if g2 <= 0.05: continue
        lam = random.uniform(lam0 * math.exp(-1 / g1), 0.9)
        w1 = g1 * m * (lam / lam0) ** (g1 - 1); w2 = g2 * m * (lam / lam0) ** (g2 - 1)
        if lam >= lam0 * math.exp(-1 / g2) and lam >= lam0 * math.exp(-1 / g1):
            assert w2 < w1 + 1e-12; cnt += 1
    print(f"  lower gamma lowers the marginal incentive for lam >= lam0 exp(-1/gamma) ({cnt} random cases)")

    # ---- vendor example: under-investment when the efficient residual risk is above lam_bar
    L, theta, c = 2000.0, 1.0, 400.0
    print("\nVendor example (L = 2000, theta = 1, c = 400, lam0 = 4%):")
    for name, g, m in (("neutral", 0.674, 1.006), ("incident", 0.455, 1.30)):
        for lam_b in (0.02, 0.06, 0.12):
            se = vendor_opt(lam_b, theta, c, L, 0.04, m, g, behavioral=False)
            sb = vendor_opt(lam_b, theta, c, L, 0.04, m, g, behavioral=True)
            lam_e = lam_b * math.exp(-theta * se)
            print(f"  {name:8s} base risk {lam_b:.2f}: efficient effort {se:6.3f}, behavioral effort {sb:6.3f} "
                  f"(ratio {sb / se:4.2f}); residual risk at the efficient level {lam_e:.4f}, threshold lam_bar {lam_bar(0.04, m, g):.4f}")

    # ---- calibration from the group means in Table 2 (ln WTP/L at 2% and 6%)
    print("\nIllustrative calibration from the group means (no heterogeneity, no response cap):")
    lam0 = 0.04
    for name, a2, a6 in (("neutral", -3.68, -2.94), ("incident", -3.27, -2.77)):
        g = (a6 - a2) / math.log(3)
        ln_w0 = a2 + g * math.log(lam0 / 0.02)        # ln w at lam0 by interpolation in ln(lam)
        m = math.exp(ln_w0 - math.log(lam0))
        be = lam0 * m ** (-1 / g)
        print(f"  {name:8s} gamma = {g:.3f}, m = {m:.3f}, behavioral break-even = {be * 100:.2f}% (benchmark 4.00%), "
              f"lam_bar = {lam_bar(lam0, m, g) * 100:.2f}%, "
              f"w'(2%) = {g * m * (0.02 / lam0) ** (g - 1):.2f}, w'(6%) = {g * m * (0.06 / lam0) ** (g - 1):.2f}")


if __name__ == "__main__":
    main()
