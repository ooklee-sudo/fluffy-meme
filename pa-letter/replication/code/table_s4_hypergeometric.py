"""SI Table S4: number of human-labelled events in a random validated subset.

Each simulation draw validates a fixed number of posts, sampled without
replacement from the 191-post frame. The number of the 10 human escalation
events (and 32 de-escalation events) it contains is hypergeometric, so the
distribution is computed exactly rather than by simulation.
"""
import csv
import os
from math import comb

N_POSTS = 191
N_ESC = 10
N_DEESC = 32
SHARES = [(0.10, 19), (0.20, 38), (0.30, 57), (0.40, 76), (0.50, 96)]

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")


def pmf(n_draw, n_success, n_total=N_POSTS):
    return [comb(n_success, k) * comb(n_total - n_success, n_draw - k) / comb(n_total, n_draw)
            for k in range(n_success + 1)]


def quantile(cdf, p):
    return next(k for k, c in enumerate(cdf) if c >= p - 1e-12)


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for share, n in SHARES:
        f = pmf(n, N_ESC)
        cdf = [sum(f[:k + 1]) for k in range(len(f))]
        rows.append({
            "share": f"{share:.0%}",
            "posts": n,
            "esc_mean": round(N_ESC * n / N_POSTS, 2),
            "esc_median": quantile(cdf, 0.5),
            "esc_iqr": f"{quantile(cdf, 0.25)}-{quantile(cdf, 0.75)}",
            "esc_90pct_range": f"{quantile(cdf, 0.05)}-{quantile(cdf, 0.95)}",
            "p_zero": round(f[0], 3),
            "p_le_2": round(cdf[2], 2),
            "deesc_mean": round(N_DEESC * n / N_POSTS, 1),
        })
    path = os.path.join(OUT, "table_s4.csv")
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(r)
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
