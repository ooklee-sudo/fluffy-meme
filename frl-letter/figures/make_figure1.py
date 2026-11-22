"""Figure 1: directional 30-minute WTI return by class under each label set.

All values are taken from the Letter's SI Table S2 (same 95 events under every
label set). Confidence intervals for the class means are available only for the
human labels; the third panel shows the human-minus-model escalation difference
with its day-clustered bootstrap 95% CI.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

HUMAN = "#2a78d6"   # categorical slot 1 (reference palette, light mode)
MODEL = "#6b6a64"   # neutral gray: model label sets are the comparison, not a series
INK = "#2b2a27"
MUTED = "#8a8983"
GRID = "#e4e3df"

labels = ["Human (final)", "Model 1", "v2 majority", "v2 sonnet", "v2 haiku", "v2 sonnet repeat"]
deesc = {"mean": [0.94, 0.90, 0.95, 1.04, 1.04, 0.99], "n": [32, 34, 33, 28, 28, 28]}
esc = {"mean": [0.45, 0.17, 0.32, 0.24, 0.35, 0.22], "n": [10, 24, 30, 38, 29, 31]}
human_ci = {"deesc": (0.38, 1.73), "esc": (0.02, 0.89)}
# Human minus label set, escalation: point, (lo, hi); index 0 (human) has none.
diff = [None, (0.28, -0.07, 0.69), (0.13, -0.26, 0.54), (0.21, -0.17, 0.62),
        (0.10, -0.28, 0.50), (0.23, -0.17, 0.68)]

y = list(range(len(labels)))[::-1]  # human on top

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": MUTED,
    "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK,
    "axes.linewidth": 0.8,
})
fig, axes = plt.subplots(1, 3, figsize=(7.5, 3.0), sharey=True,
                         gridspec_kw={"width_ratios": [1, 1, 1]})


def style(ax, title, xlabel, xlim):
    ax.set_title(title, loc="left", fontsize=9.5, color=INK, fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.set_xlim(*xlim)
    ax.axvline(0, color=MUTED, lw=0.8, zorder=1)
    ax.grid(axis="x", color=GRID, lw=0.6, zorder=0)
    ax.tick_params(length=0)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)


def class_panel(ax, data, ci, title, xlim):
    style(ax, title, "Directional return (%)", xlim)
    hm = data["mean"][0]
    ax.axvline(hm, color=HUMAN, lw=1, ls=(0, (3, 2)), zorder=1)
    ax.plot(ci, [y[0], y[0]], color=HUMAN, lw=2, solid_capstyle="round", zorder=2)
    for i, (m, n) in enumerate(zip(data["mean"], data["n"])):
        if i == 0:
            ax.plot(m, y[i], "o", ms=8, color=HUMAN, mec="white", mew=1.5, zorder=3)
        else:
            ax.plot(m, y[i], "o", ms=8, mfc="white", mec=MODEL, mew=1.8, zorder=3)
        ax.annotate(f"n={n}", (xlim[1], y[i]), xytext=(-2, 0), textcoords="offset points",
                    ha="right", va="center", fontsize=7.5, color=MUTED)


class_panel(axes[0], deesc, human_ci["deesc"], "A. De-escalation", (-0.2, 2.4))
class_panel(axes[1], esc, human_ci["esc"], "B. Escalation", (-0.2, 1.25))

ax = axes[2]
style(ax, "C. Escalation: human − label set", "Difference (pp)", (-0.45, 0.85))
for i, d in enumerate(diff):
    if d is None:
        ax.annotate("reference", (0.02, y[i]), ha="left", va="center", fontsize=7.5, color=MUTED)
        continue
    pt, lo, hi = d
    ax.plot([lo, hi], [y[i], y[i]], color=MODEL, lw=2, solid_capstyle="round", zorder=2)
    ax.plot(pt, y[i], "o", ms=8, mfc="white", mec=MODEL, mew=1.8, zorder=3)

axes[0].set_yticks(y)
axes[0].set_yticklabels(labels)
axes[0].get_yticklabels()[0].set_color(HUMAN)
axes[0].get_yticklabels()[0].set_fontweight("bold")
axes[0].set_ylim(-0.6, len(labels) - 0.4)

fig.tight_layout(w_pad=1.2)
for ext in ("pdf", "png"):
    fig.savefig(f"../Figure_1.{ext}", dpi=300, bbox_inches="tight", facecolor="white")
print("saved")
