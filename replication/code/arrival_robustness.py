"""Table 6: loss multiplier E[ int_0^tau exp(-(rho-g) t) dt ] under gamma and deterministic epoch lengths, relative to Poisson.

  python code/arrival_robustness.py
"""
import csv
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RHO, G = 0.10, 0.20


def multipliers(mean_gap_years, cv, a=RHO - G):
    L = lambda laplace: (1 - laplace) / a                     # E[(1 - e^{-a tau}) / a]
    mu = 1 / mean_gap_years
    poisson = L(mu / (mu + a))                                # tau ~ Exp(mu)
    shape, scale = 1 / cv ** 2, mean_gap_years * cv ** 2      # gamma matched to mean and CV
    gamma = L((1 + a * scale) ** (-shape))
    det = L(np.exp(-a * mean_gap_years))
    return gamma / poisson, det / poisson


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, "..", "data", "release_counts.csv"))))
    rows.append(dict(family="Pooled", mean_gap_months="6.1", cv_gaps="0.46"))
    print(f"{'family':<10}{'CV':>6}{'gamma/Poisson':>15}{'determ./Poisson':>17}")
    for r in rows:
        g, d = multipliers(float(r["mean_gap_months"]) / 12, float(r["cv_gaps"]))
        print(f"{r['family']:<10}{float(r['cv_gaps']):>6.2f}{g:>15.3f}{d:>17.3f}")


if __name__ == "__main__":
    main()
