"""H2b analysis (PREREGISTRATION_H2b.md): does a published tensor-network adapter (QuanTA) do better than LoRA
at a similar parameter budget, and does the TT layout (number of cores) explain the TT result of H2?

Primary: per brand, relative gain of quanta:4 minus lora:4 (both trained in the same run); Wilcoxon signed-rank
test, two-sided, alpha 0.05; Hodges-Lehmann estimate with a bootstrap 95% interval.
Secondary: quanta:5 vs lora:1; TT with 3 and 5 cores vs 4 cores at tt:2 and tt:10; the best of all TT layouts
and QuanTA sizes per brand vs lora:1.

Usage: python analyze_h2b.py results/h2b_main [results/h2b_tt_d3 results/h2b_tt_d5]
"""
import glob
import json
import os
import sys

import numpy as np
from scipy.stats import wilcoxon


def load(d, tag=""):
    out = {}
    for p in sorted(glob.glob(os.path.join(d, "*.json"))):
        r = json.load(open(p))
        out[r["tenant"]] = {run["config"] + tag: run for run in r["runs"]}
    return out


def hl(x, rng=np.random.default_rng(0), b=5000):
    def est(v):
        w = (v[:, None] + v[None, :]) / 2
        return float(np.median(w[np.triu_indices(len(v))]))
    boots = [est(rng.choice(x, len(x))) for _ in range(b)]
    return est(x), np.percentile(boots, [2.5, 97.5])


def compare(rows, a, b, label=""):
    names = [n for n in sorted(rows) if a in rows[n] and b in rows[n]]
    if len(names) < 6:
        print(f"{a} vs {b}: only {len(names)} brands, skipped")
        return
    x = np.array([rows[n][a]["rel_gain"] - rows[n][b]["rel_gain"] for n in names])
    pa = np.mean([rows[n][a]["params"] for n in names])
    pb = np.mean([rows[n][b]["params"] for n in names])
    est, ci = hl(x)
    p = wilcoxon(x).pvalue if not np.allclose(x, 0) else float("nan")
    print(f"{a} ({pa:,.0f} params) - {b} ({pb:,.0f}): n={len(names)}, {a} ahead for {(x > 0).sum()}, "
          f"median {np.median(x):+.4f}, HL {est:+.4f} [{ci[0]:+.4f}, {ci[1]:+.4f}], Wilcoxon p = {p:.4f}{label}")


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    rows = load(sys.argv[1])
    for extra in sys.argv[2:]:
        tag = "@" + os.path.basename(extra.rstrip("/")).split("_")[-1]  # e.g. tt:2@d3
        for n, runs in load(extra, tag).items():
            rows.setdefault(n, {}).update(runs)
    print(f"{len(rows)} brands\n\nmean relative gain by config:")
    configs = sorted({c for r in rows.values() for c in r})
    for c in configs:
        v = [r[c] for r in rows.values() if c in r]
        print(f"  {c:<14} {np.mean([x['rel_gain'] for x in v]):.4f}  params {np.mean([x['params'] for x in v]):>10,.0f}"
              f"  lr {v[0]['lr']:g}  sec/run {np.mean([x['seconds'] for x in v]):.0f}  n={len(v)}")
    print()
    compare(rows, "quanta:4", "lora:4", "  <- PRIMARY H2b")
    compare(rows, "quanta:5", "lora:1")
    for r in ("tt:2", "tt:10"):
        for d in ("d3", "d5"):
            compare(rows, f"{r}@{d}", r)
    tt_like = [c for c in configs if c.startswith(("tt:", "quanta:"))]
    names = [n for n in sorted(rows) if "lora:1" in rows[n]]
    best = np.array([max(rows[n][c]["rel_gain"] for c in tt_like if c in rows[n]) for n in names])
    lo = np.array([rows[n]["lora:1"]["rel_gain"] for n in names])
    print(f"\nbest of {len(tt_like)} TT/QuanTA configs per brand (chosen on eval, optimistic) minus lora:1: "
          f"median {np.median(best - lo):+.4f}, ahead for {(best > lo).sum()}/{len(names)} brands")


if __name__ == "__main__":
    main()
