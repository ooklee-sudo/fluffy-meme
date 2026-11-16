"""E4 summary (exploratory): weekly decay of a stale adapter's benefit vs RAG with a stale or fresh index.

Reports, by week since training, the mean relative gain of: stale LoRA r=1, RAG-8 with the training-period
index, RAG-8 with last week's index; a within-brand slope per week (brand fixed effects, so weeks with
harder traffic do not dominate); and the recovery of retraining in the last week (stale / fresh adapter).

Usage: python analyze_drift.py [results/econ_e4]
"""
import glob
import json
import os
import sys

import numpy as np

SERIES = ["lora_stale_rel", "rag_stale_rel", "rag_fresh_rel"]


def slope(rows, key):
    """Within-brand OLS slope of `key` on week (weeks >= 2), with a bootstrap 95% interval over brands."""
    def fit(rs):
        xs, ys = [], []
        for r in rs:
            pts = [(int(w), v[key]) for w, v in r["weeks"].items() if w.isdigit() and key in v]
            if len(pts) < 3:
                continue
            w, y = np.array(pts, float).T
            xs.append(w - w.mean())
            ys.append(y - y.mean())
        x, y = np.concatenate(xs), np.concatenate(ys)
        return float((x * y).sum() / (x * x).sum())
    est = fit(rows)
    rng = np.random.default_rng(0)
    boots = [fit([rows[i] for i in rng.integers(0, len(rows), len(rows))]) for _ in range(1000)]
    return est, np.percentile(boots, 2.5), np.percentile(boots, 97.5)


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else "results/econ_e4"
    rows = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(d, "*.json")))]
    if not rows:
        raise SystemExit(f"no results in {d}")
    weeks = ["in-period"] + sorted({w for r in rows for w in r["weeks"] if w.isdigit()}, key=int)
    print(f"{len(rows)} brands\n")
    print(f"{'week':<11}" + "".join(f"{s.replace('_rel', ''):>13}" for s in SERIES) + f"{'lora_fresh':>13}")
    for w in weeks:
        cells = []
        for s in SERIES + ["lora_fresh_rel"]:
            v = [r["weeks"][w][s] for r in rows if w in r["weeks"] and s in r["weeks"][w]]
            cells.append(f"{np.mean(v):>13.3f}" if v else f"{'':>13}")
        print(f"{w:<11}" + "".join(cells))
    print("\nWithin-brand change in relative gain per week (weeks 2 onward), bootstrap 95% CI over brands:")
    for s in SERIES:
        e, lo, hi = slope(rows, s)
        print(f"  {s.replace('_rel', ''):<12}{e:+.4f} per week  [{lo:+.4f}, {hi:+.4f}]")
    last = weeks[-1]
    rec = [r["weeks"][last]["lora_stale_rel"] / r["weeks"][last]["lora_fresh_rel"] for r in rows
           if r["weeks"][last].get("lora_fresh_rel", 0) > 0]
    ret = [r["weeks"][last]["lora_stale_rel"] / r["weeks"]["in-period"]["lora_stale_rel"] for r in rows
           if r["weeks"]["in-period"]["lora_stale_rel"] > 0]
    st = np.mean([r["weeks"][last]["lora_stale_rel"] for r in rows])
    fr = np.mean([r["weeks"][last].get("lora_fresh_rel", np.nan) for r in rows])
    ip = np.mean([r["weeks"]["in-period"]["lora_stale_rel"] for r in rows])
    print(f"\nWeek {last}: stale adapter keeps {st / ip:.1%} of its in-period gain (ratio of means; per-brand median "
          f"{np.median(ret):.1%})")
    print(f"recovery R = stale / fresh adapter gain = {st / fr:.3f} (ratio of means; per-brand median "
          f"{np.median(rec):.3f}, n = {len(rec)})")
    gap = [r["weeks"][last]["lora_stale_rel"] - r["weeks"][last]["rag_fresh_rel"] for r in rows]
    print(f"stale adapter minus fresh-index RAG in week {last}: mean {np.mean(gap):+.3f}, "
          f"adapter ahead for {sum(g > 0 for g in gap)}/{len(gap)} brands")


if __name__ == "__main__":
    main()
