"""Table 3: upgrade intensity per family, exact Poisson 95% intervals, pooled rate, likelihood-ratio test of a common rate.

Input: data/release_counts.csv (counts and window lengths as printed in Table 3, so T is rounded to 0.01 year).
The underlying release dates (release_history.csv) are not part of this package; see README.

  python code/release_intensity.py
"""
import csv
import os

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))


def load():
    rows = list(csv.DictReader(open(os.path.join(HERE, "..", "data", "release_counts.csv"))))
    return [(r["family"], int(r["n_releases"]), float(r["window_years"])) for r in rows]


def main():
    fams = load()
    N, T = sum(n for _, n, _ in fams), sum(t for _, _, t in fams)
    mu = N / T
    lr = 0.0
    print(f"{'family':<10}{'n':>3}{'T':>7}{'mu_hat':>8}   95% CI")
    out = {}
    for f, n, t in fams:
        lo = stats.chi2.ppf(0.025, 2 * n) / 2 / t
        hi = stats.chi2.ppf(0.975, 2 * n + 2) / 2 / t
        lr += 2 * n * np.log((n / t) / mu)
        out[f] = (n / t, lo, hi)
        print(f"{f:<10}{n:>3}{t:>7.2f}{n / t:>8.2f}   [{lo:.2f}, {hi:.2f}]")
    p = 1 - stats.chi2.cdf(lr, len(fams) - 1)
    print(f"{'Pooled':<10}{N:>3}{T:>7.2f}{mu:>8.2f}\nLR test of a common rate: chi2({len(fams) - 1}) = {lr:.2f}, p = {p:.2f}")
    return out, mu, lr, p


if __name__ == "__main__":
    main()
