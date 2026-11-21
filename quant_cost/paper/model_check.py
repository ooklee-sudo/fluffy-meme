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


    # ---- Corollary 1: loss from over-adoption of the local model
    cnt = 0
    for _ in range(2000):
        lam0 = random.uniform(0.005, 0.2); g = random.uniform(0.1, 1.0); m = random.uniform(1.01, 3.0)
        be = breakeven_closed(lam0, m, g)
        if be >= lam0:
            continue
        L = 1000.0; D = lam0 * L
        # buyer chooses local for every lam > be; the cloud is optimal for lam < lam0
        for lam in np.linspace(be * 1.0001, lam0 * 0.9999, 7):
            assert w(lam, lam0, m, g) * L > D                      # the behavioral buyer goes local
            loss = D - lam * L                                      # extra cost of local relative to cloud
            assert loss >= -1e-9 and loss <= D * (1 - m ** (-1 / g)) + 1e-6
        assert abs(L * (lam0 - be) - D * (1 - m ** (-1 / g))) < 1e-6
        cnt += 1
    print(f"Corollary 1: loss L(lam0 - lam) is largest at lam_tilde and equals D (1 - m^(-1/gamma)) ({cnt} random cases)")
    for name, g_, m_ in (("neutral", 0.674, 1.006), ("incident", 0.455, 1.303)):
        print(f"  {name:8s} largest over-adoption loss as a share of D: {1 - m_ ** (-1 / g_):.3f}")

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
    print("\nVendor example (L = 2000, theta = 1, k = 400, lam0 = 4%):")
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


# ======================================================================================================
# Extensions: competition among vendors (Proposition 3) and a mixture of calculators and non-calculators
# (Proposition 4)
# ======================================================================================================
def extensions():
    L, theta, k = 2000.0, 1.0, 400.0        # loss, effectiveness of effort, effort-cost coefficient
    lam0 = 0.04

    # ---- Proposition 3: symmetric equilibrium effort under Bertrand competition equals the take-it-or-leave-it effort
    # A deviator with effort s facing rivals with effort s_c wins the buyer by undercutting the perceived cost; its
    # payoff is  g(s) - g(s_c)  with  g(s) = -w(lam(s)) L - C(s).
    print("\nProposition 3 (competition):")
    for name, g_, m_ in (("neutral", 0.674, 1.006), ("incident", 0.455, 1.30)):
        lam_b = 0.06
        g = lambda s: -w(lam_b * math.exp(-theta * s), lam0, m_, g_) * L - k * s * s / 2
        s_b = vendor_opt(lam_b, theta, k, L, lam0, m_, g_, behavioral=True)
        # best deviation against rivals at s_c, for several s_c
        rows = []
        for s_c in (0.5 * s_b, 0.9 * s_b, s_b, 1.1 * s_b, 2.0 * s_b):
            best = optimize.minimize_scalar(lambda s: -(g(s) - g(s_c)), bounds=(0, 200), method="bounded",
                                            options={"xatol": 1e-10})
            rows.append((s_c, best.x, -best.fun))
        ok = all((abs(r[0] - s_b) < 1e-6 and abs(r[2]) < 1e-9) or (abs(r[0] - s_b) > 1e-6 and r[2] > 1e-9) for r in rows)
        print(f"  {name:8s} s_b = {s_b:.4f}; best deviation always goes to s_b: "
              f"{all(abs(r[1] - s_b) < 1e-4 for r in rows)}; profitable deviation exists iff s_c != s_b: {ok}")

    # ---- Proposition 4: mixture of calculators (w = lam) and non-calculators (w_b)
    print("\nProposition 4 (mixture of calculators and non-calculators), linear demand, common price:")
    Dbar, c_m = 400.0, 0.0
    gb, mb = 0.40, 1.0
    def what(lam, pi):
        return pi * lam + (1 - pi) * w(lam, lam0, mb, gb)
    def profit(s, pi, lam_b=0.06):
        lam = lam_b * math.exp(-theta * s)
        x = Dbar - L * what(lam, pi) - c_m
        return x * x / (4 * Dbar) - k * s * s / 2
    # marginal-reward formula: d profit / d s (without cost) = Q* L what'(lam) |lam'(s)|
    lam_b = 0.06
    for pi in (0.0, 0.5, 1.0):
        s = 0.1
        lam = lam_b * math.exp(-theta * s)
        h = 1e-6
        num = ((Dbar - L * what(lam_b * math.exp(-theta * (s + h)), pi) - c_m) ** 2 -
               (Dbar - L * what(lam_b * math.exp(-theta * s), pi) - c_m) ** 2) / (4 * Dbar) / h
        q_star = (Dbar - L * what(lam, pi) - c_m) / (2 * Dbar)
        wp_b = gb * mb * (lam / lam0) ** (gb - 1)
        what_p = pi + (1 - pi) * wp_b
        formula = q_star * L * what_p * theta * lam
        assert abs(num - formula) / formula < 1e-4, (pi, num, formula)
    print("  marginal reward = Q* L (pi + (1 - pi) w_b'(lam)) |lam'(s)| verified at pi = 0, 0.5, 1")
    effs = []
    for pi in (0.0, 0.25, 0.5, 0.75, 1.0):
        s_opt = optimize.minimize_scalar(lambda s: -profit(s, pi), bounds=(0, 50), method="bounded",
                                         options={"xatol": 1e-10}).x
        effs.append((pi, s_opt))
    print("  optimal effort by share of calculators:", ", ".join(f"pi={p:.2f}: {e:.3f}" for p, e in effs))

    # ---- accounting decomposition of the difference in mean S (Table 2 values)
    print("\nDecomposition of the difference in mean S between the conditions (accounting identity):")
    ln3 = math.log(3)
    S_N, S_I, pi_N, pi_I = 0.74, 0.50, 0.45, 0.35
    nc_N = (S_N - pi_N * ln3) / (1 - pi_N)
    nc_I = (S_I - pi_I * ln3) / (1 - pi_I)
    comp = (pi_I - pi_N) * (ln3 - nc_N)
    within = (1 - pi_I) * (nc_I - nc_N)
    print(f"  mean S among the others: neutral {nc_N:.3f}, incident {nc_I:.3f}")
    print(f"  total difference {S_I - S_N:.3f} = composition {comp:.3f} + within the others {within:.3f} "
          f"(check {comp + within:.3f}); composition share {comp / (S_I - S_N):.0%}")


if __name__ == "__main__":
    main()
    extensions()
