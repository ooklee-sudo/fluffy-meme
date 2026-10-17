"""Figures for the manuscript. Run from this folder after parse_data.py: python make_figures.py"""
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, INK2, GRID, MARK = "#0b0b0b", "#52514e", "#e4e3df", "#2a78d6"
ORDER = ["openai/gpt-4o-mini", "meta-llama/llama-3.3-70b-instruct", "anthropic/claude-haiku-5.5", "anthropic/claude-sonnet-5",
         "openai/gpt-5.6-terra", "deepseek/deepseek-v4-pro-0813", "google/gemini-3.1-flash-lite", "mistralai/mistral-large-4-0"]
NAME = {"openai/gpt-4o-mini": "GPT-4o-mini", "meta-llama/llama-3.3-70b-instruct": "Llama-3.3-70B", "anthropic/claude-haiku-5.5": "Haiku 5.5",
        "anthropic/claude-sonnet-5": "Sonnet 5", "openai/gpt-5.6-terra": "GPT-5.6-terra", "deepseek/deepseek-v4-pro-0813": "DeepSeek-V4-Pro",
        "google/gemini-3.1-flash-lite": "Gemini 3.1 Flash-Lite", "mistralai/mistral-large-4-0": "Mistral Large 4"}
plt.rcParams.update({"font.size": 8, "axes.edgecolor": INK2, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.spines.top": False, "axes.spines.right": False, "text.color": INK})


def fig_dispersion():
    """Rows = settings, columns = designs A-D, y = model; filled = plain prompt, hollow = anchored prompt (one hue)."""
    sets = [("a  Low-mean setting (reference 2.49; C ceiling 2.10)", "retail_ci.csv", 2.49, 2.10),
            ("b  High-mean setting (reference 7.85; C ceiling 6.61)", "grocery_ci.csv", 7.85, 6.61),
            ("c  Real household demographics (reference 6.52; C ceiling 5.01)", "demo_ci.csv", 6.52, 5.01)]
    sizes = [len([m for m in ORDER if m in set(pd.read_csv(fn).model)]) for _, fn, _, _ in sets]
    fig = plt.figure(figsize=(9.2, 10.4)); row_axes = []
    gs = fig.add_gridspec(3, 4, height_ratios=[s + 1.6 for s in sizes], hspace=0.55, wspace=0.12)
    for ri, (title, fn, ref, ceil) in enumerate(sets):
        df = pd.read_csv(fn)
        models = [m for m in ORDER if m in set(df.model)]
        xmax = max(df.var_mean_hi.max(), ref) * 1.05
        axes = []
        for ci, c in enumerate("ABCD"):
            ax = fig.add_subplot(gs[ri, ci], sharex=axes[0] if axes else None); axes.append(ax)
            for yi, m in enumerate(models):
                y = len(models) - 1 - yi
                for an, dy in ((False, 0.14), (True, -0.14)):
                    r = df[(df.model == m) & (df.anchor == an) & (df.cond == c)]
                    if r.empty:
                        continue
                    r = r.iloc[0]
                    ax.plot([r.var_mean_lo, r.var_mean_hi], [y + dy] * 2, color=MARK, lw=1.2, solid_capstyle="round", zorder=2)
                    ax.plot(r.var_mean, y + dy, "o", ms=4.2, mfc=MARK if not an else "white", mec=MARK, mew=1.2, zorder=3)
            ax.axvline(ref, color=INK, lw=1.0, ls="--", zorder=1)
            if c == "C":
                ax.axvline(ceil, color=INK2, lw=0.8, ls=":", zorder=1)
            ax.set_ylim(-0.7, len(models) - 0.3)
            ax.set_xlim(-0.05 * xmax, xmax)
            ax.set_yticks(range(len(models))[::-1] if ci == 0 else [])
            if ci == 0:
                ax.set_yticklabels([NAME[m] for m in models], fontsize=7.5)
            ax.set_title(f"design {c}", loc="left", fontsize=8.5, color=INK2)
            ax.grid(axis="x", color=GRID, lw=0.5); ax.set_axisbelow(True)
        row_axes.append((axes, title))
    handles = [plt.Line2D([], [], marker="o", color=MARK, mfc=MARK, ls="", ms=5, label="plain prompt"),
               plt.Line2D([], [], marker="o", color=MARK, mfc="white", ls="", ms=5, label="anchored prompt"),
               plt.Line2D([], [], color=INK, ls="--", label="real value"), plt.Line2D([], [], color=INK2, ls=":", label="ceiling of design C")]
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=8, bbox_to_anchor=(0.58, 0.0))
    fig.subplots_adjust(left=0.17, right=0.985, top=0.94, bottom=0.075)
    for axes, title in row_axes:  # row titles above each row (placed after the layout is fixed)
        fig.text(0.17, axes[0].get_position().y1 + 0.032, title, fontsize=9.5, fontweight="bold", color=INK, ha="left")
    fig.text(0.58, 0.043, "variance / mean (95% CI)", fontsize=8, color=INK2, ha="center")
    fig.savefig("fig1_dispersion.png", dpi=200); plt.close(fig)


def fig_lift():
    df = pd.read_csv("hillstrom_rd_parsed.csv"); df = df[df.method == "C_prob"]
    real = {"visit": (0.0766, 0.0766 - 0.0066, 0.0766 + 0.0066), "purchase": (0.0068, 0.0068 - 0.0018, 0.0068 + 0.0018)}
    rows = [(m, an) for m in ORDER for an in (False, True)]
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 6.4), sharey=True)
    for ax, outcome, title in zip(axes, ("visit", "purchase"), ("a  Website visit (2 weeks)", "b  Purchase (2 weeks), log scale")):
        for ri, (m, an) in enumerate(rows):
            r = df[(df.model == m) & (df.anchor == an) & (df.outcome == outcome)].iloc[0]
            y = len(rows) - 1 - ri
            lo = max(r.RD_men_lo, 1e-4)
            ax.plot([lo, r.RD_men_hi], [y, y], color=MARK, lw=1.2, solid_capstyle="round", zorder=2)
            ax.plot(max(r.RD_men, 1e-4), y, "o", ms=5, mfc=MARK if not an else "white", mec=MARK, mew=1.3, zorder=3)
        v, lo, hi = real[outcome]
        ax.axvspan(lo, hi, color="#cfcdc6", alpha=0.6, lw=0, zorder=0)
        ax.axvline(v, color=INK, lw=1.0, ls="--", zorder=1)
        ax.text(v, len(rows) - 0.1, f" real {v:+.4f}", ha="left", va="bottom", fontsize=7.5, color=INK)
        if outcome == "purchase":
            ax.set_xscale("log"); ax.set_xlim(0.0015, 0.4)
        else:
            ax.set_xlim(-0.01, 0.25)
        ax.set_yticks(range(len(rows))[::-1])
        ax.set_yticklabels([f"{NAME[m]}, {'anchored' if an else 'plain'}" for m, an in rows], fontsize=7)
        ax.set_ylim(-0.7, len(rows) + 0.4)
        ax.set_xlabel("men's email minus no email (probability), 95% CI"); ax.set_title(title, loc="left", fontsize=9.5, color=INK)
        ax.grid(axis="x", color=GRID, lw=0.5); ax.set_axisbelow(True)
    handles = [plt.Line2D([], [], marker="o", color=MARK, mfc=MARK, ls="", ms=5, label="plain prompt"),
               plt.Line2D([], [], marker="o", color=MARK, mfc="white", ls="", ms=5, label="anchored prompt")]
    fig.legend(handles=handles, loc="lower center", ncol=2, frameon=False, fontsize=8)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig("fig2_lift.png", dpi=200); plt.close(fig)


if __name__ == "__main__":
    fig_dispersion(); fig_lift(); print("ok")
