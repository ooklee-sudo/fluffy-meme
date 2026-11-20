"""Normative benchmark of the two-state vignette (all amounts in today's dollars, thousands).

Options:  (a) build now      : s + E[V] - F
          (b) wait 12 months : E[max(V - F, 0)]      (give up s; build next year only if V > F)
          (c) keep the API   : 0
(a) - (b) = s - E[max(F - V, 0)]: this year's savings vs. the value of avoiding the Bad state.
F*(spread) = highest building cost at which (a) is still optimal.

  python -m quant_cost.normative_check
"""
import math

CASES = {"A": 0.8, "B": 0.6, "C": 1.0, "D": 1.2}   # scale relative to F = 500
BASE_F, BASE_S, BASE_MEAN = 500.0, 60.0, 600.0
SPREADS = {"low": 0.10, "high": 0.50}               # +/- share of the mean, equal probability


def states(mean, spread):
    return [(0.5, mean * (1 - spread)), (0.5, mean * (1 + spread))]


def values(F, s, st):
    ev = sum(p * v for p, v in st)
    return s + ev - F, sum(p * max(v - F, 0.0) for p, v in st), 0.0


def best(F, s, st):
    a, b, c = values(F, s, st)
    return max((a, "build now"), (b, "wait"), (c, "keep API"))[1]


def f_star(s, st, hi=1e5):
    lo = 0.0
    for _ in range(200):
        mid = (lo + hi) / 2
        a, b, c = values(mid, s, st)
        lo, hi = (mid, hi) if a >= max(b, c) else (lo, mid)
    return lo


def main():
    print("case     F     s | low: (a)   (b)  best        | high: (a)   (b)  best       | F*low  F*high  ratio  ln")
    for k, m in CASES.items():
        F, s, mean = BASE_F * m, BASE_S * m, BASE_MEAN * m
        lo, hi = states(mean, SPREADS["low"]), states(mean, SPREADS["high"])
        (al, bl, _), (ah, bh, _) = values(F, s, lo), values(F, s, hi)
        fl, fh = f_star(s, lo), f_star(s, hi)
        print(f"{k:4s} {F:5.0f} {s:5.0f} | {al:9.1f} {bl:6.1f}  {best(F, s, lo):10s} | {ah:9.1f} {bh:6.1f}  "
              f"{best(F, s, hi):10s} | {fl:6.1f} {fh:6.1f} {fh/fl:6.3f} {math.log(fh/fl):6.3f}")


if __name__ == "__main__":
    main()
