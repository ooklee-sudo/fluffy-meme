"""Inter-coder reliability between two coding sheets (human-human or human-LLM).

Matches rows on (unit_id, claim_id) and reports Krippendorff's alpha per code:
nominal for presence, direction, A1 and Layer C cues; ordinal for intensity.
Codebook Section 8: target alpha >= 0.70 per HBM construct; an LLM is used for
scale only if its alpha against adjudicated labels is within 0.05 of human-human alpha.

    python reliability.py coder1.csv coder2.csv
"""
from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd

from codebook import CONSTRUCTS, CUES


def kripp_alpha(a, b, level: str = "nominal") -> float:
    """Krippendorff's alpha for two coders, no missing values within a pair."""
    pairs = [(x, y) for x, y in zip(a, b) if pd.notna(x) and pd.notna(y)]
    if len(pairs) < 2:
        return float("nan")
    vals = sorted({v for p in pairs for v in p})
    if len(vals) == 1:
        return 1.0
    ix = {v: i for i, v in enumerate(vals)}
    o = np.zeros((len(vals), len(vals)))
    for x, y in pairs:  # coincidence matrix: each pair counted in both orders
        o[ix[x], ix[y]] += 1
        o[ix[y], ix[x]] += 1
    n_c = o.sum(axis=1)
    n = n_c.sum()
    if level == "nominal":
        delta = 1 - np.eye(len(vals))
    else:  # ordinal metric
        delta = np.zeros_like(o)
        for c in range(len(vals)):
            for k in range(len(vals)):
                lo, hi = min(c, k), max(c, k)
                delta[c, k] = (n_c[lo:hi + 1].sum() - (n_c[lo] + n_c[hi]) / 2) ** 2
    d_o = (o * delta).sum() / n
    d_e = (np.outer(n_c, n_c) * delta).sum() / (n * (n - 1))
    return 1.0 - d_o / d_e if d_e else 1.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet_a")
    ap.add_argument("sheet_b")
    a = ap.parse_args()
    A, B = pd.read_csv(a.sheet_a), pd.read_csv(a.sheet_b)
    for d in (A, B):
        d["claim_id"] = d["claim_id"].fillna("none")
    m = A.merge(B, on=["unit_id", "claim_id"], suffixes=("_a", "_b"))
    if m.empty:
        sys.exit("no matching (unit_id, claim_id) rows")
    print(f"{len(m)} matched rows\n")
    print(f"{'code':<17}{'alpha':>8}{'agree%':>9}  level")
    codes = [("A1_health_claim", "nominal")]
    for b in CONSTRUCTS:
        codes += [(f"{b}_pres", "nominal"), (f"{b}_dir", "nominal"), (f"{b}_int", "ordinal")]
    codes += [(c, "nominal") for c in CUES]
    for col, level in codes:
        x, y = m[f"{col}_a"], m[f"{col}_b"]
        al = kripp_alpha(x, y, level)
        both = x.notna() & y.notna()
        agree = (x[both] == y[both]).mean() * 100 if both.any() else float("nan")
        flag = "" if np.isnan(al) or al >= 0.70 else "  < 0.70"
        print(f"{col:<17}{al:>8.3f}{agree:>8.1f}%  {level}{flag}")


if __name__ == "__main__":
    main()
