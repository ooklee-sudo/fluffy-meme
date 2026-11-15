"""H4 analysis (PREREGISTRATION_H4.md): knowledge injection, TT r=31 vs LoRA r=16 at about 11.5M parameters.

  python analyze_h4.py tune results/h4_tune   learning rate per method = highest dev exact-match accuracy on
                                               the tuning fact set; edge choices are flagged
  python analyze_h4.py test results/h4        primary test: paired t-test, two-sided, alpha 0.05, on the
                                               per-fact-set difference in eval exact-match accuracy (TT - LoRA)
"""
import glob
import json
import os
import sys

import numpy as np
from scipy.stats import t as tdist, ttest_rel, wilcoxon

A, B = "tt:31", "lora:16"


def load(d):
    return [json.load(open(p)) for p in sorted(glob.glob(os.path.join(d, "*.json")))]


def tune(d):
    rows = load(d)
    if not rows:
        raise SystemExit(f"no results in {d}")
    best, grid = {}, {}
    print(f"{'config':<10}{'lr':>9}{'dev acc':>9}{'eval acc':>10}{'best step':>11}")
    for r in rows:
        for x in r["runs"]:
            print(f"{x['config']:<10}{x['lr']:>9.0e}{x['dev_acc']:>9.3f}{x['acc']:>10.3f}{x['best_step']:>11}")
            grid.setdefault(x["method"], []).append(x["lr"])
            if x["method"] not in best or x["dev_acc"] > best[x["method"]][1]:
                best[x["method"]] = (x["lr"], x["dev_acc"])
    print()
    edge = [m for m, (lr, _) in best.items() if lr in (min(grid[m]), max(grid[m]))]
    for m, (lr, a) in sorted(best.items()):
        print(f"{m}: lr {lr:.0e} (dev acc {a:.3f}){'  <- at the grid edge' if m in edge else ''}")
    print(f"\n--lrs " + ",".join(f"{m}={best[m][0]:g}" for m in sorted(best)))
    if edge:
        print(f"Edge choices for {', '.join(edge)}: extend that grid one step and tune again (section 5).")


def test(d):
    rows = load(d)
    pairs = []
    for r in rows:
        g = {x["config"]: x for x in r["runs"]}
        if A in g and B in g:
            pairs.append((r["name"], g[A], g[B]))
    print(f"{len(pairs)} fact sets in {d}\n")
    print(f"{'fact set':<22}{'TT acc':>8}{'LoRA acc':>10}{'diff':>8}{'TT nll':>8}{'LoRA nll':>10}{'TT min':>8}{'LoRA min':>10}")
    for n, a, b in pairs:
        print(f"{n:<22}{a['acc']:>8.3f}{b['acc']:>10.3f}{a['acc'] - b['acc']:>+8.3f}{a['nll']:>8.3f}{b['nll']:>10.3f}"
              f"{a['seconds'] / 60:>8.1f}{b['seconds'] / 60:>10.1f}")
    if len(pairs) < 3:
        print("\nfewer than 3 fact sets; no test")
        return
    d_acc = np.array([a["acc"] - b["acc"] for _, a, b in pairs])
    d_nll = np.array([a["nll"] - b["nll"] for _, a, b in pairs])
    n = len(d_acc)
    m, se = d_acc.mean(), d_acc.std(ddof=1) / np.sqrt(n)
    lo, hi = m + np.array([-1, 1]) * tdist.ppf(0.975, n - 1) * se
    p = ttest_rel([a["acc"] for _, a, _ in pairs], [b["acc"] for _, _, b in pairs]).pvalue
    print(f"\nPRIMARY H4 (paired t-test, two-sided): mean accuracy difference TT - LoRA = {m:+.4f} "
          f"[95% CI {lo:+.4f}, {hi:+.4f}], TT better in {(d_acc > 0).sum()}/{n}, p = {p:.4f} -> "
          f"{'significant' if p < 0.05 else 'not significant'} at 0.05")
    print("\nSecondary (do not decide H4):")
    if not np.allclose(d_acc, 0):
        print(f"  Wilcoxon signed-rank on accuracy difference: p = {wilcoxon(d_acc).pvalue:.4f}")
    print(f"  mean eval NLL difference TT - LoRA = {d_nll.mean():+.4f} (negative favors TT)")
    print(f"  mean training minutes: TT {np.mean([a['seconds'] for _, a, _ in pairs]) / 60:.1f}, "
          f"LoRA {np.mean([b['seconds'] for _, _, b in pairs]) / 60:.1f}")
    if all(a.get("rank") and b.get("rank") for _, a, b in pairs):
        print("  mean effective rank of the learned update (TT / LoRA):")
        for k in pairs[0][1]["rank"]:
            ta = np.mean([a["rank"][k]["eff_rank"] for _, a, _ in pairs])
            lb = np.mean([b["rank"][k]["eff_rank"] for _, _, b in pairs])
            print(f"    {k:<10}{ta:>8.1f} / {lb:.1f}")
    with open(d.rstrip("/") + "_h4.json", "w") as f:
        json.dump(dict(primary=dict(mean_diff=m, ci=[lo, hi], p=p, n=n, wins=int((d_acc > 0).sum())),
                       per_set=[dict(name=nm, tt_acc=a["acc"], lora_acc=b["acc"]) for nm, a, b in pairs]), f, indent=1)


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in ("tune", "test"):
        raise SystemExit(__doc__)
    (tune if sys.argv[1] == "tune" else test)(sys.argv[2])
