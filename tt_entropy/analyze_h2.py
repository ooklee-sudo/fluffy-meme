"""H2 analysis (PREREGISTRATION_H2.md): tensor-train vs LoRA at matched per-tenant parameter budgets.

Primary test: per-tenant difference in relative gain, TT r=5 (127,120 params) minus LoRA r=1 (136,192),
averaged over the training seeds present; Wilcoxon signed-rank, two-sided, alpha = 0.05. Reported with the
median difference and the Hodges-Lehmann estimate with a bootstrap 95% interval.

Usage: python analyze_h2.py results/phase2_s0 [results/phase2_s1 ...]
"""
import glob
import json
import os
import sys
from collections import defaultdict

import numpy as np
from scipy.stats import wilcoxon

PRIMARY = ("tt:5", "lora:1")
SECONDARY = [("tt:10", "lora:4"), ("tt:15", "lora:8")]
SMALL = [("tt:2", "vera:256"), ("tt:2", "vera:1024"), ("tt:1", "vera:256")]


def hodges_lehmann(d):
    w = (d[:, None] + d[None, :]) / 2
    return float(np.median(w[np.triu_indices(len(d))]))


def pair(gains, a, b, rng):
    ts = [t for t in gains if a in gains[t] and b in gains[t]]
    d = np.array([gains[t][a] - gains[t][b] for t in ts])
    if len(d) < 6 or np.allclose(d, 0):
        return dict(n=len(d), p=float("nan"))
    p = float(wilcoxon(d, alternative="two-sided").pvalue)
    boots = [hodges_lehmann(rng.choice(d, len(d))) for _ in range(2000)]
    return dict(n=len(d), median=float(np.median(d)), hl=hodges_lehmann(d), lo=float(np.percentile(boots, 2.5)),
                hi=float(np.percentile(boots, 97.5)), p=p, wins=int((d > 0).sum()))


def fmt(a, b, s):
    if s["p"] != s["p"]:
        return f"{a + ' - ' + b:<22} n={s['n']}: not enough pairs"
    return (f"{a + ' - ' + b:<22} n={s['n']:<3} median {s['median']:+.4f}  HL {s['hl']:+.4f} [{s['lo']:+.4f}, {s['hi']:+.4f}]"
            f"  {a} better in {s['wins']}/{s['n']}  p = {s['p']:.4f}")


def main():
    dirs = sys.argv[1:] or ["results/phase2_s0"]
    empty = [d for d in dirs if not glob.glob(os.path.join(d, "*.json"))]
    if empty:
        print(f"WARNING: no results in {', '.join(empty)}; those seeds are NOT included below.")
    dirs = [d for d in dirs if d not in empty]
    if not dirs:
        raise SystemExit("no results to analyze")
    per = defaultdict(lambda: defaultdict(list))
    params = {}
    for d in dirs:
        for p in sorted(glob.glob(os.path.join(d, "*.json"))):
            r = json.load(open(p))
            for run in r["runs"]:
                per[r["tenant"]][run["config"]].append(run["rel_gain"])
                params[run["config"]] = run["params"]
    gains = {t: {c: float(np.mean(v)) for c, v in cs.items()} for t, cs in per.items()}
    print(f"{len(gains)} tenants from {', '.join(dirs)}")

    configs = sorted(params, key=lambda c: params[c])
    print(f"\n{'config':<11}{'params':>11}{'KB/tenant':>11}{'GB per 10k tenants':>20}{'mean rel gain':>15}{'n':>4}")
    for c in configs:
        v = [g[c] for g in gains.values() if c in g]
        print(f"{c:<11}{params[c]:>11,}{2 * params[c] / 1024:>11.0f}{2 * params[c] * 1e4 / 1e9:>20.2f}"
              f"{np.mean(v):>15.4f}{len(v):>4}")

    rng = np.random.default_rng(0)
    s = pair(gains, *PRIMARY, rng)
    print(f"\nPRIMARY H2 (two-sided Wilcoxon): {fmt(*PRIMARY, s)}")
    if s["p"] == s["p"]:
        print(f"  -> {'significant' if s['p'] < 0.05 else 'not significant'} at 0.05")

    sec = [pair(gains, a, b, rng) for a, b in SECONDARY]
    ps = [x["p"] if x["p"] == x["p"] else 1.0 for x in sec]
    order = np.argsort(ps)
    holm, run = [0.0] * len(ps), 0.0
    for k, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - k) * ps[i]))
        holm[i] = run
    print("\nSecondary, larger budgets (Holm over these two):")
    for (a, b), x, h in zip(SECONDARY, sec, holm):
        print(f"  {fmt(a, b, x)}  Holm p = {h:.4f}")
    print("\nSecondary, below LoRA's smallest size (TT has fewer params than VeRA in each pair):")
    for a, b in SMALL:
        print(f"  {fmt(a, b, pair(gains, a, b, rng))}")

    out = dirs[0].rstrip("/") + "_h2.json"
    with open(out, "w") as f:
        json.dump(dict(dirs=dirs, primary=dict(pair=PRIMARY, **s), secondary=[dict(pair=p_, holm=h, **x) for p_, x, h in
                                                                               zip(SECONDARY, sec, holm)],
                       mean_rel_gain={c: float(np.mean([g[c] for g in gains.values() if c in g])) for c in configs},
                       params=params), f, indent=1)
    print(f"\nsaved {out}")


if __name__ == "__main__":
    main()
