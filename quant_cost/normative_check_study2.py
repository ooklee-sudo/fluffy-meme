"""Normative benchmark for Study 2 (privacy and performance presentation). Amounts in thousands of dollars per year.

Local model vs cloud API for the coming year:
  operating:  local saves B on running cost but its extra errors cost E   -> net operating advantage B - E
  privacy:    the API exposes customer data with probability lam per year, loss L if it happens -> lam * L
  net advantage of LOCAL = (B - E) + lam * L          choose local iff > 0   (risk neutral)
  willingness to pay to eliminate the API's exposure risk (normative) = lam * L
Break-even exposure probability lam* = (E - B) / L.

  python -m quant_cost.normative_check_study2
"""
import math

CASES = {"A": 0.8, "B": 0.6, "C": 1.0, "D": 1.2}      # scale relative to case C
B0, E0, L0 = 100.0, 180.0, 2000.0
LAM = {"low": 0.02, "high": 0.06}
SLIDER_SHARE = 0.25                                    # WTP slider range = 0 .. 0.25 L


def main():
    print("case   B     E     L   | lam: net_local  choice | WTP* (=lam*L) low high ratio  ln  | lam*   slider_max")
    for k, m in CASES.items():
        B, E, L = B0 * m, E0 * m, L0 * m
        out = []
        for name, lam in LAM.items():
            net = (B - E) + lam * L
            out.append((net, "LOCAL" if net > 0 else "API", lam * L))
        w_lo, w_hi = out[0][2], out[1][2]
        print(f"{k:4s} {B:5.0f} {E:5.0f} {L:6.0f} | low {out[0][0]:7.1f} {out[0][1]:5s} high {out[1][0]:7.1f} {out[1][1]:5s} "
              f"| {w_lo:6.1f} {w_hi:6.1f} {w_hi/w_lo:5.2f} {math.log(w_hi/w_lo):5.3f} | {(E-B)/L:5.3f} {SLIDER_SHARE*L:8.0f}")


if __name__ == "__main__":
    main()
