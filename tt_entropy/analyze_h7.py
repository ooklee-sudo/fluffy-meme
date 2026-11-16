"""H7 analysis (PREREGISTRATION_H5_H7.md): does a stale adapter lose relative gain faster than RAG-8 whose index
is refreshed weekly?

Primary test: for each brand, the OLS slope of relative gain on week (weeks 2-8) for the stale LoRA r=1 adapter
and for fresh-index RAG-8; Wilcoxon signed-rank test of the per-brand difference (adapter slope minus RAG
slope), two-sided, alpha 0.05.

Usage: python analyze_h7.py results/h7_drift
"""
import glob
import json
import os
import sys

import numpy as np
from scipy.stats import wilcoxon


def slope(r, key):
    pts = [(int(w), v[key]) for w, v in r["weeks"].items() if w.isdigit() and key in v]
    w, y = np.array(pts, float).T
    return float(np.polyfit(w, y, 1)[0])


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else "results/h7_drift"
    rows = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(d, "*.json")))]
    if len(rows) < 6:
        raise SystemExit(f"only {len(rows)} brands in {d}")
    sa = np.array([slope(r, "lora_stale_rel") for r in rows])
    sr = np.array([slope(r, "rag_fresh_rel") for r in rows])
    diff = sa - sr
    p = wilcoxon(diff).pvalue
    print(f"{len(rows)} brands")
    print(f"mean slope per week: stale adapter {sa.mean():+.4f}, fresh-index RAG {sr.mean():+.4f}")
    print(f"PRIMARY H7 (Wilcoxon, two-sided): adapter minus RAG slope, median {np.median(diff):+.4f}, "
          f"adapter declines faster for {(diff < 0).sum()}/{len(diff)} brands, p = {p:.4f} -> "
          f"{'significant' if p < 0.05 else 'not significant'} at 0.05")
    last = max(int(w) for w in rows[0]["weeks"] if w.isdigit())
    st = np.array([r["weeks"][str(last)]["lora_stale_rel"] for r in rows])
    fr = np.array([r["weeks"][str(last)]["lora_fresh_rel"] for r in rows])
    rg = np.array([r["weeks"][str(last)]["rag_fresh_rel"] for r in rows])
    ip = np.array([r["weeks"]["in-period"]["lora_stale_rel"] for r in rows])
    print(f"\nSecondary: week {last}: stale adapter keeps {st.mean() / ip.mean():.1%} of its in-period gain; "
          f"recovery R = {st.mean() / fr.mean():.3f}; stale adapter ahead of fresh-index RAG for "
          f"{(st > rg).sum()}/{len(rows)} brands")
    w2 = np.array([r["weeks"]["2"]["lora_stale_rel"] - r["weeks"]["2"]["rag_fresh_rel"] for r in rows]).mean()
    if sa.mean() < sr.mean() and w2 > 0:
        print(f"horizon over which the stale adapter stays ahead (from week 2, linear): "
              f"{2 + w2 / (sr.mean() - sa.mean()):.1f} weeks")


if __name__ == "__main__":
    main()
