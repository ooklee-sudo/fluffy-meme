"""EXPLORATORY analysis (not preregistered): does gradient entropy predict how much a tenant gains from
personalization, beyond simple tenant traits?

Outcomes:  best gain (NLL without adapter minus best NLL over the sweep, seed-averaged), and relative gain
           (best gain / NLL without adapter), which removes the "more room to improve" effect.
Predictor: gradient-probe normalized bond entropy (equal token budget).
Controls:  response type-token ratio, distinct-response share, mean response length, NLL without adapter.

Reports partial Spearman correlations (rank residuals on one or more controls) for the confirmatory
sample, the exploratory sample, both pooled, and the confirmatory sample without TwitterSupport.
Any finding here is a hypothesis for a new preregistered test on unused tenants, not a result.

Usage: python explore.py [results/phase1_confirm] [results/phase1]
"""
import glob
import json
import math
import os
import sys

import numpy as np
from scipy.stats import pearsonr, rankdata, spearmanr, t as tdist


def load(d):
    rows = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(d, "*.json")))]
    out = []
    for r in rows:
        if "grad_probe" not in r or r["capacity_need"] is None:
            continue
        best = max(s["gain"] for s in r["sweep"])
        out.append(dict(
            tenant=r["tenant"], entropy=r["grad_probe"]["summary"]["mean_norm_entropy"],
            best_gain=best, rel_gain=best / r["nll_none"], log2_need=math.log2(r["capacity_need"]),
            ttr=r["features"]["response_type_token_ratio"], distinct=r["features"]["distinct_response_share"],
            resp_len=r["features"]["mean_response_tokens"], nll_none=r["nll_none"]))
    return out


def partial(rows, x, y, controls):
    """Partial Spearman of x and y given controls (ranks, least-squares residuals); two-sided p."""
    n, k = len(rows), len(controls)
    rx = rankdata([r[x] for r in rows])
    ry = rankdata([r[y] for r in rows])
    if k:
        z = np.column_stack([np.ones(n)] + [rankdata([r[c] for r in rows]) for c in controls])
        res = lambda v: v - z @ np.linalg.lstsq(z, v, rcond=None)[0]
        rx, ry = res(rx), res(ry)
    rho = float(pearsonr(rx, ry)[0])
    df = n - 2 - k
    if df < 1 or abs(rho) >= 1:
        return rho, float("nan")
    tt = rho * math.sqrt(df / (1 - rho * rho))
    return rho, float(2 * tdist.sf(abs(tt), df))


CONTROL_SETS = [
    ("none", []),
    ("type-token ratio", ["ttr"]),
    ("distinct share", ["distinct"]),
    ("response length", ["resp_len"]),
    ("NLL without adapter", ["nll_none"]),
    ("all four", ["ttr", "distinct", "resp_len", "nll_none"]),
]


def report(name, rows):
    print(f"\n=== {name} (n = {len(rows)}) ===")
    print(f"{'controlling for':<22}" + "".join(f"{y:>22}" for y in ("best gain", "relative gain", "log2 need")))
    for label, ctrl in CONTROL_SETS:
        cells = []
        for y in ("best_gain", "rel_gain", "log2_need"):
            rho, p = partial(rows, "entropy", y, ctrl)
            cells.append(f"{rho:>+8.3f} (p={p:.3f})")
        print(f"{label:<22}" + "".join(f"{c:>22}" for c in cells))


def main():
    conf = sys.argv[1] if len(sys.argv) > 1 else "results/phase1_confirm"
    expl = sys.argv[2] if len(sys.argv) > 2 else "results/phase1"
    a, b = load(conf), load(expl)
    print("EXPLORATORY: partial Spearman rho of gradient entropy with each outcome; none of this is preregistered.")
    report(f"confirmatory sample ({conf})", a)
    if b:
        report(f"exploratory sample ({expl})", b)
        report("both samples pooled", a + b)
    report("confirmatory sample without TwitterSupport", [r for r in a if r["tenant"] != "TwitterSupport"])

    print("\nHow the controls relate to entropy and best gain (confirmatory sample, zero-order Spearman):")
    for c in ("ttr", "distinct", "resp_len", "nll_none"):
        re_, pe = spearmanr([r["entropy"] for r in a], [r[c] for r in a])
        rg, pg = spearmanr([r["best_gain"] for r in a], [r[c] for r in a])
        print(f"  {c:<10} vs entropy {re_:+.3f} (p={pe:.3f})   vs best gain {rg:+.3f} (p={pg:.3f})")
    print("\nWith n = 30 and up to 4 controls, these p-values are descriptive. Many cells were looked at, so a single"
          "\np < 0.05 here is weak evidence; a pattern that holds across control sets and samples is a better guide.")


if __name__ == "__main__":
    main()
