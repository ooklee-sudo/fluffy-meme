"""Figures for the IEEE Intelligent Systems version (balanced action order).

    python figures.py            # writes figures/fig2_goal.{png,pdf}, figures/fig3_order.{png,pdf}

Figure 1 (prompt anatomy) is a diagram and is described in
isr_revision/ieee_is_structure.md rather than drawn here.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from analyze import load

HERE = Path(__file__).parent
R, OUT = HERE / "results", HERE / "figures"

# Reference palette (dataviz skill): slot 1 blue for "target stated in the
# headline"; a muted neutral for headlines that do not state it.
TARGET = "#2a78d6"
NOTARGET = "#a3a29c"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8.5, "axes.edgecolor": INK2,
    "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6,
})

LABEL = {"neutral": "Neutral", "loss": "Loss", "gain": "Gain-to-goal",
         "neutral_goal": "Neutral\n+ target", "loss_goal": "Loss\n+ target"}
FRAMES = ["neutral", "loss", "gain", "neutral_goal", "loss_goal"]
HAS_TARGET = {"gain", "neutral_goal", "loss_goal"}


def frame_ci(d, frame, rng, n_boot=4000):
    """Mean over wordings of the cell skip rate, with a bootstrap over wordings."""
    rates = d[d.frame == frame].groupby("headline_id")["skip"].mean().to_numpy()
    idx = rng.integers(0, len(rates), size=(n_boot, len(rates)))
    m = rates[idx].mean(axis=1)
    return rates.mean(), np.percentile(m, 2.5), np.percentile(m, 97.5)


def style(ax, ymax):
    ax.set_ylim(0, ymax)
    ax.yaxis.grid(True, color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))


def fig2_goal():
    rng = np.random.default_rng(0)
    d = load([R / "study4_bal__haiku45__s4_bal.jsonl"])
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.7), sharey=True)
    for ax, hide, title in zip(axes, (False, True),
                               ("Target also in the facts line", "Target only in the headline")):
        dd = d[d.hide_target == hide]
        for i, f in enumerate(FRAMES):
            m, lo, hi = frame_ci(dd, f, rng)
            ax.bar(i, m, width=0.62, color=TARGET if f in HAS_TARGET else NOTARGET,
                   edgecolor="white", linewidth=1.0)
            ax.errorbar(i, m, yerr=[[m - lo], [hi - m]], color=INK, lw=0.8, capsize=2.5, capthick=0.8)
            ax.text(i, hi + 0.012, f"{100 * m:.0f}%", ha="center", va="bottom", fontsize=7.5, color=INK)
        ax.set_xticks(range(5), [LABEL[f] for f in FRAMES], fontsize=7.5)
        ax.set_title(title, fontsize=8.5, color=INK, loc="left")
        style(ax, 0.42)
    axes[0].set_ylabel("First choices that skip verification")
    handles = [plt.Rectangle((0, 0), 1, 1, color=TARGET), plt.Rectangle((0, 0), 1, 1, color=NOTARGET)]
    fig.legend(handles, ["Headline states the target", "Headline does not state the target"],
               loc="upper center", ncol=2, frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, 1.03))
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    return fig


def fig3_order():
    rng = np.random.default_rng(1)
    d = load([R / "study4_bal__haiku45__s4_bal.jsonl"])
    d = d[d.hide_target == False]  # noqa: E712
    d = d.assign(target=d.frame.isin(HAS_TARGET))
    order = ["hold", "rollback", "wide_skip", "narrow_skip", "wide_patch", "narrow_patch"]
    nice = {"hold": "hold", "rollback": "rollback", "wide_skip": "wide fix,\nno tests",
            "narrow_skip": "small fix,\nno tests", "wide_patch": "wide fix,\ntested",
            "narrow_patch": "small fix,\ntested"}
    fig, ax = plt.subplots(figsize=(7.0, 2.7))
    w = 0.36
    for j, (tgt, color, lab) in enumerate([(False, NOTARGET, "Headline does not state the target"),
                                           (True, TARGET, "Headline states the target")]):
        for i, a in enumerate(order):
            sub = d[(d.first_listed == a) & (d.target == tgt)]
            rates = sub.groupby(["headline_id", "frame"])["skip"].mean().groupby("headline_id").mean().to_numpy()
            idx = rng.integers(0, len(rates), size=(4000, len(rates)))
            bm = rates[idx].mean(axis=1)
            m, lo, hi = rates.mean(), np.percentile(bm, 2.5), np.percentile(bm, 97.5)
            x = i + (j - 0.5) * (w + 0.03)
            ax.bar(x, m, width=w, color=color, edgecolor="white", linewidth=1.0, label=lab if i == 0 else None)
            ax.errorbar(x, m, yerr=[[m - lo], [hi - m]], color=INK, lw=0.8, capsize=2, capthick=0.8)
    ax.set_xticks(range(len(order)), [nice[a] for a in order], fontsize=7.5)
    ax.set_xlabel("Option listed first in the prompt", color=INK)
    ax.set_ylabel("First choices that skip verification")
    style(ax, 0.85)
    ax.legend(frameon=False, fontsize=7.5, loc="upper right")
    fig.tight_layout()
    return fig


def main():
    OUT.mkdir(exist_ok=True)
    for name, fn in [("fig2_goal", fig2_goal), ("fig3_order", fig3_order)]:
        fig = fn()
        for ext in ("png", "pdf"):
            fig.savefig(OUT / f"{name}.{ext}", dpi=300, bbox_inches="tight")
        plt.close(fig)
        print("wrote", OUT / f"{name}.png")


if __name__ == "__main__":
    main()
