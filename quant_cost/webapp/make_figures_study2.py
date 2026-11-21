"""Descriptive tables and figures for Study 2 (visualisation of values the preregistered analysis uses; no new tests).

  python quant_cost/webapp/make_figures_study2.py --csv ~/study2_main_data/main_wide.csv --outdir ~/study2_main_data/figures

Uses the same exclusions as analysis_study2.py. Writes fig1_S_by_group, fig2_wtp_by_lambda, fig3_choice_by_format
(.png and .pdf) and descriptives_study2.csv / .md. Intervals are 95% t-intervals over participants.
Colours: two categorical slots (neutral = blue, incident = orange), checked with the palette validator.
"""
import argparse
import math
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

import analysis_study2 as A

NEUTRAL, INCIDENT = "#2a78d6", "#eb6834"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#d9d8d3"
NORM = {2: math.log(0.02), 6: math.log(0.06)}


def style():
    plt.rcParams.update({"font.size": 10, "axes.edgecolor": GRID, "axes.labelcolor": MUTED, "xtick.color": MUTED,
                         "ytick.color": MUTED, "text.color": INK, "axes.spines.top": False, "axes.spines.right": False,
                         "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
                         "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "savefig.facecolor": "#fcfcfb"})


def mean_ci(x):
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    n = len(x)
    m = x.mean()
    h = stats.t.ppf(0.975, n - 1) * x.std(ddof=1) / math.sqrt(n) if n > 1 else float("nan")
    return m, m - h, m + h, n


def save(fig, outdir, name):
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(outdir, f"{name}.{ext}"), dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig1(df, outdir):
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    rng = np.random.default_rng(1)
    for x0, (lab, g, col) in enumerate([("Neutral news", df[df.incident == 0], NEUTRAL), ("Incident report", df[df.incident == 1], INCIDENT)]):
        v = g["S"].dropna().values
        ax.scatter(x0 + rng.uniform(-0.18, 0.18, len(v)), v, s=14, color=col, alpha=0.35, linewidths=0, zorder=2)
        m, lo, hi, n = mean_ci(v)
        ax.plot([x0, x0], [lo, hi], color=col, lw=2.5, zorder=4, solid_capstyle="round")
        ax.scatter([x0], [m], s=60, color=col, edgecolor="#fcfcfb", linewidths=2, zorder=5)
        ax.text(x0 + 0.24, m, f"mean {m:.2f}", va="center", color=INK, fontsize=9.5,
                bbox=dict(boxstyle="round,pad=0.2", fc="#fcfcfb", ec="none"), zorder=6)
    ax.axhline(math.log(3), color=MUTED, lw=1, ls="--", zorder=1)
    ax.text(1.68, math.log(3) + 0.04, "Normative\nln 3 = 1.10", va="bottom", ha="right", color=MUTED, fontsize=9)
    ax.set_xticks([0, 1])
    n0, n1 = int((df.incident == 0).sum()), int((df.incident == 1).sum())
    ax.set_xticklabels([f"Neutral news\n(n = {n0})", f"Incident report\n(n = {n1})"])
    ax.set_xlim(-0.5, 1.7)
    ax.set_ylabel("S = mean ln(WTP/L) at 6% minus at 2%")
    ax.set_title("Sensitivity of willingness to pay to the stated probability", loc="left", fontsize=11, color=INK)
    save(fig, outdir, "fig1_S_by_group")


def fig2(df, L, outdir):
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    xs = {2: 0, 6: 1}
    ends = []
    for lab, inc, col, dx in [("Neutral news", 0, NEUTRAL, -0.03), ("Incident report", 1, INCIDENT, 0.03)]:
        pts = []
        for lam in (2, 6):
            g = L[(L.incident == inc) & (L.lam6 == int(lam == 6))].groupby("pid")["lnw"].mean()
            pts.append(mean_ci(g.values))
        x = [xs[2] + dx, xs[6] + dx]
        ax.plot(x, [p[0] for p in pts], color=col, lw=2, zorder=3)
        for xi, p in zip(x, pts):
            ax.plot([xi, xi], [p[1], p[2]], color=col, lw=2.5, solid_capstyle="round", zorder=4)
            ax.scatter([xi], [p[0]], s=55, color=col, edgecolor="#fcfcfb", linewidths=2, zorder=5)
        ends.append((pts[1][0], x[1] + 0.07, lab))
    ends.sort()
    if ends[1][0] - ends[0][0] < 0.14:
        mid = (ends[0][0] + ends[1][0]) / 2
        ends[0] = (mid - 0.07, ends[0][1], ends[0][2]); ends[1] = (mid + 0.07, ends[1][1], ends[1][2])
    for yy, xx, lab in ends:
        ax.text(xx, yy, lab, color=INK, va="center", fontsize=9.5)
    for lam in (2, 6):
        ax.scatter([xs[lam]], [NORM[lam]], marker="_", s=900, color=MUTED, linewidths=1.5, zorder=2)
    ax.text(-0.13, NORM[2], "Normative", color=MUTED, fontsize=8.5, va="center", ha="right")
    ax.text(0.87, NORM[6], "Normative", color=MUTED, fontsize=8.5, va="center", ha="right")
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Stated probability 2%", "Stated probability 6%"])
    ax.set_xlim(-0.5, 1.75)
    ax.set_ylabel("Mean ln(WTP/L)")
    ax.set_title("Willingness to pay by stated probability and news", loc="left", fontsize=11, color=INK)
    save(fig, outdir, "fig2_wtp_by_lambda")


def fig3(df, L, outdir):
    fig, ax = plt.subplots(figsize=(5.2, 4.2))
    xs = {"Accuracy only": 0, "Accuracy + cost per\ncorrect answer": 1}
    for lam, col, lab in [(0, "#6250d6", "Stated probability 2%"), (1, "#008300", "Stated probability 6%")]:
        pts = []
        for fmt in (0, 1):
            g = L[(L.lam6 == lam) & (L.cost_shown == fmt)].groupby("pid")["local"].mean()
            pts.append(mean_ci(g.values))
        x = [0 + (-0.03 if lam == 0 else 0.03), 1 + (-0.03 if lam == 0 else 0.03)]
        ax.plot(x, [p[0] for p in pts], color=col, lw=2, zorder=3)
        for xi, p in zip(x, pts):
            ax.plot([xi, xi], [max(0, p[1]), min(1, p[2])], color=col, lw=2.5, solid_capstyle="round", zorder=4)
            ax.scatter([xi], [p[0]], s=55, color=col, edgecolor="#fcfcfb", linewidths=2, zorder=5)
        ax.text(x[1] + 0.06, pts[1][0], lab, color=INK, va="center", fontsize=9.5)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(list(xs.keys()))
    ax.set_xlim(-0.4, 1.9)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Share choosing the local model")
    ax.set_title("Choice of the local model by performance format", loc="left", fontsize=11, color=INK)
    save(fig, outdir, "fig3_choice_by_format")


def table(df, L, outdir):
    rows = []

    def add(label, series_by_group, fmt="{:.2f}"):
        row = {"measure": label}
        for name, g in series_by_group.items():
            m, lo, hi, n = mean_ci(g)
            sd = np.nanstd(np.asarray(g, float), ddof=1)
            row[name] = f"{fmt.format(m)} (SD {fmt.format(sd)}; 95% CI {fmt.format(lo)} to {fmt.format(hi)}; n = {n})"
        rows.append(row)

    grp = {"Neutral news": df[df.incident == 0], "Incident report": df[df.incident == 1]}
    add("S (ln WTP/L at 6% minus at 2%)", {k: v["S"].values for k, v in grp.items()})
    add("Mean ln(WTP/L), all four scenarios", {k: v["meanLnWTPL"].values for k, v in grp.items()})
    for lam in (2, 6):
        add(f"Mean ln(WTP/L), stated probability {lam}%", {k: L[(L.incident == (k == "Incident report")) & (L.lam6 == int(lam == 6))].groupby("pid")["lnw"].mean().values for k in grp})
    add("Share choosing local (all scenarios)", {k: (v["n_local"] / 4).values for k, v in grp.items()})
    add("General 12-month exposure estimate, % (GP)", {k: v["GP"].values for k, v in grp.items()}, "{:.1f}")
    t = pd.DataFrame(rows)
    t.to_csv(os.path.join(outdir, "descriptives_study2.csv"), index=False)
    with open(os.path.join(outdir, "descriptives_study2.md"), "w", encoding="utf-8") as f:
        f.write("| Measure | Neutral news | Incident report |\n| --- | --- | --- |\n")
        for _, r in t.iterrows():
            f.write(f"| {r['measure']} | {r['Neutral news']} | {r['Incident report']} |\n")
    print(open(os.path.join(outdir, "descriptives_study2.md"), encoding="utf-8").read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--outdir", required=True)
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    style()
    df = A.load(a.csv)
    L = A.long_format(df)
    fig1(df, a.outdir)
    fig2(df, L, a.outdir)
    fig3(df, L, a.outdir)
    table(df, L, a.outdir)
    print("written to", a.outdir)


if __name__ == "__main__":
    main()
