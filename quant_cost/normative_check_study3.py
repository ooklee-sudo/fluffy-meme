"""Normative structure of Study 3 (cost x confidentiality). Amounts in thousands of dollars per year.

Local model's net operating disadvantage D (extra cost vs. the cloud API after running cost and errors);
API exposure: probability lam per year, loss L if it happens.  Net advantage of LOCAL = lam*L - D  (risk neutral).
Dominance ratio rho = lam*L / D: choose local iff rho > 1.
Design: L in {low, high}; D scales with L so that rho takes the SAME values at both L levels:
    rho in {2.5, 0.625, 0.156}  ->  normative choice local, API, API  at BOTH L levels.
Any difference between the L levels at equal rho is therefore a departure from the normative model.

  python -m quant_cost.normative_check_study3
"""
LAM = 0.04
L_BASE = {"low": 2500.0, "high": 10000.0}
RHO = (2.5, 0.625, 0.15625)
CASES = {"A": 0.8, "B": 0.6, "C": 1.0, "D": 1.2, "E": 0.9, "F": 1.1}   # scale of all amounts


def cells(m=1.0):
    out = []
    for lname, L in L_BASE.items():
        for rho in RHO:
            D = LAM * L * m / rho
            out.append((lname, rho, L * m, D, LAM * L * m, LAM * L * m - D, "LOCAL" if LAM * L * m > D else "API"))
    return out


def main():
    print(f"lambda = {LAM:.0%}; scale m = 1 (case C). Cells (thousand $/yr):")
    print("L-level  rho     L      D (net cost of local)  lam*L   net advantage  normative choice")
    for lname, rho, L, D, lamL, net, ch in cells(1.0):
        print(f"{lname:6s} {rho:6.3f} {L:7.0f} {D:14.0f} {lamL:14.0f} {net:12.0f}   {ch}")
    print("\nCase scales (all amounts multiply by m):", CASES)


if __name__ == "__main__":
    main()
