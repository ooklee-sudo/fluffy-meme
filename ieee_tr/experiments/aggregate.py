#!/usr/bin/env python3
"""Aggregate per-seed JSON files from seed_study.py.

    python aggregate.py results_seeds --figdir ../figs_seeds

Prints the numbers that replace the single-seed values in Section VII-D
(mean, SD, 95% t-interval over seeds) and writes a LaTeX table plus two figures.
"""
import argparse
import glob
import json
import os

import numpy as np
from scipy import stats


def ols(x, y):
    x, y = np.asarray(x, float), np.asarray(y, float)
    slope, intercept, r, _, _ = stats.linregress(x, y)
    return slope, intercept, r ** 2


def ci(v, level=0.95):
    v = np.asarray(v, float)
    n = len(v)
    m = v.mean()
    if n < 2:
        return m, float("nan"), float("nan"), float("nan")
    sd = v.std(ddof=1)
    h = stats.t.ppf(0.5 + level / 2, n - 1) * sd / np.sqrt(n)
    return m, sd, m - h, m + h


def fmt(v, d=2):
    m, sd, lo, hi = ci(v)
    return f"{m:.{d}f} (SD {sd:.{d}f}; 95% CI {lo:.{d}f} to {hi:.{d}f})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--figdir", default="figs_seeds")
    ap.add_argument("--coverage", type=float, default=0.6)
    args = ap.parse_args()

    runs = [json.load(open(p)) for p in sorted(glob.glob(os.path.join(args.results, "seed_*.json")))]
    if not runs:
        raise SystemExit("no seed_*.json files found")
    n = len(runs)
    print(f"{n} seeds: {[r['seed'] for r in runs]}\n")

    # ---- deployed checkpoint ----------------------------------------------
    print("Deployed checkpoint")
    for key in ("acc_dynamic", "acc_static", "acc_note", "follow_conflicting_note"):
        print(f"  {key:26s} {fmt([r['deployed'][key] for r in runs], 3)}")
    print(f"  epochs to converge          {fmt([r['deployed']['epochs'] for r in runs], 1)}\n")

    # ---- staleness slopes ---------------------------------------------------
    sn, sr, r2n, r2r, absorbed = [], [], [], [], []
    for r in runs:
        d = [c["day"] for c in r["curve"]]
        a, _, ra = ols(d, [c["err_plain"] for c in r["curve"]])
        b, _, rb = ols(d, [c["err_retrieval"] for c in r["curve"]])
        sn.append(a); sr.append(b); r2n.append(ra); r2r.append(rb)
        absorbed.append(1 - b / a)
    absorbed = np.array(absorbed)
    print("Staleness growth over the horizon (pp per day)")
    print(f"  no retrieval   slope {fmt(sn, 3)}  mean R2 {np.mean(r2n):.3f}")
    print(f"  with retrieval slope {fmt(sr, 3)}  mean R2 {np.mean(r2r):.3f}")
    print(f"  absorbed share alpha/gamma = 1 - slope ratio: {fmt(absorbed, 3)}")
    if n > 1:
        t, p = stats.ttest_1samp(absorbed, args.coverage)
        print(f"  H0: share = coverage {args.coverage:.2f}:  t = {t:.2f}, p = {p:.3f} (n = {n})")
    fac = 1 / np.sqrt(np.clip(1 - absorbed, 1e-9, None))
    print(f"  predicted interval lengthening sqrt(gamma/(gamma-alpha)): {fmt(fac, 2)}")
    print(f"  predicted threshold factor sqrt(1-alpha/gamma):          {fmt(1 / fac, 2)}\n")

    # ---- mechanisms ---------------------------------------------------------
    names = {"edit": "Localized edit", "lora": "LoRA, rank 16, no replay", "full": "Full fine-tune"}
    rows = {}
    for mech in names:
        before, after, ret, cost, costf, dom = [], [], [], [], [], []
        for r in runs:
            per_seed = [r["maintenance"][d] for d in r["maintenance"]]
            before.append(np.mean([m["before_total"] for m in per_seed]))
            after.append(np.mean([m[mech]["after_total"] for m in per_seed]))
            ret.append(np.mean([m[mech]["retention_change_pp"] for m in per_seed]))
            cost.append(np.mean([m[mech]["cost_trainable_norm"] for m in per_seed]))
            costf.append(np.mean([m[mech]["cost_forward_inclusive_norm"] for m in per_seed]))
            dom.append(np.mean([m[mech]["after_total"] >= m["before_total"] for m in per_seed]))
        rows[mech] = dict(before=before, after=after, ret=ret, cost=cost, costf=costf, dom=dom)
    print("Parametric mechanisms (average of the interventions at the maintenance days, per seed)")
    for mech, v in rows.items():
        print(f"  {names[mech]}")
        print(f"    error before -> after (pp): {np.mean(v['before']):.1f} -> {np.mean(v['after']):.1f}  "
              f"(after: {fmt(v['after'], 1)})")
        print(f"    retention change (pp):      {fmt(v['ret'], 1)}")
        print(f"    cost, trainable accounting: {fmt(v['cost'], 1)}   forward-inclusive: {fmt(v['costf'], 1)}")
        print(f"    share of interventions that raise total error (dominated by no action): "
              f"{100 * np.mean(v['dom']):.0f}%")
    eff = {m: np.array(rows[m]["before"]) - np.array(rows[m]["after"]) for m in rows}
    cst = {m: np.array(rows[m]["cost"]) for m in rows}
    ok = np.mean((eff["full"] > eff["edit"]) & (cst["full"] > cst["edit"]))
    print(f"\n  seeds in which full fine-tune is both more effective and more expensive than the edit: "
          f"{100 * ok:.0f}%")

    # ---- LaTeX table --------------------------------------------------------
    os.makedirs(args.figdir, exist_ok=True)
    tex = [r"\begin{tabular}{lcccc}", r"\toprule",
           r"Mechanism & Cost & Error before $\to$ after (pp) & Retention change (pp) & Raises error (\%)\\",
           r"\midrule"]
    for mech, v in rows.items():
        tex.append(f"{names[mech]} & {np.mean(v['cost']):.1f} & ${np.mean(v['before']):.1f}\\to{np.mean(v['after']):.1f}$ & "
                   f"${np.mean(v['ret']):+.1f}\\ (\\pm{np.std(v['ret'], ddof=1) if n > 1 else float('nan'):.1f})$ & "
                   f"{100 * np.mean(v['dom']):.0f}\\\\")
    tex += [r"\bottomrule", r"\end{tabular}"]
    open(os.path.join(args.figdir, "table_mechanisms.tex"), "w").write("\n".join(tex) + "\n")

    # ---- figures ------------------------------------------------------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    days = [c["day"] for c in runs[0]["curve"]]
    P = np.array([[c["err_plain"] for c in r["curve"]] for r in runs])
    R = np.array([[c["err_retrieval"] for c in r["curve"]] for r in runs])
    fig, ax = plt.subplots(figsize=(5.2, 3.0))
    for M, lab, col in ((P, "No retrieval", "#c1502e"), (R, "Retrieval (60% coverage)", "#1f4e79")):
        mu = M.mean(0)
        se = M.std(0, ddof=1) / np.sqrt(n) if n > 1 else np.zeros_like(mu)
        ax.plot(days, mu, color=col, label=lab)
        ax.fill_between(days, mu - 1.96 * se, mu + 1.96 * se, color=col, alpha=0.2)
    ax.set_xlabel("Days since deployment")
    ax.set_ylabel("Dynamic-suite error (pp)")
    ax.legend(frameon=False)
    ax.set_title(f"Mean over {n} seeds, 95% band", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(args.figdir, "fig4_seeds.png"), dpi=200)

    fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.6))
    labels = ["edit", "LoRA", "full"]
    for ax, key, title in zip(axs, ("cost", "gain", "ret"), ("Cost (full = 1000)", "Error reduction (pp)", "Retention change (pp)")):
        for i, mech in enumerate(names):
            v = rows[mech]
            y = {"cost": v["cost"], "gain": np.array(v["before"]) - np.array(v["after"]), "ret": v["ret"]}[key]
            ax.bar(i, np.mean(y), yerr=(np.std(y, ddof=1) if n > 1 else 0), color="#1f4e79", capsize=3)
            ax.scatter([i] * n, y, color="k", s=6, zorder=3)
        ax.set_xticks(range(3)); ax.set_xticklabels(labels); ax.set_title(title, fontsize=9)
        if key == "cost":
            ax.set_yscale("symlog", linthresh=10)
        ax.axhline(0, color="gray", lw=0.5)
    fig.tight_layout()
    fig.savefig(os.path.join(args.figdir, "fig5_seeds.png"), dpi=200)
    print(f"\nwrote {args.figdir}/table_mechanisms.tex, fig4_seeds.png, fig5_seeds.png")


if __name__ == "__main__":
    main()
