"""Figures for the results draft. Run from this folder: python make_figures.py"""
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
MODELS = [("openai/gpt-4o-mini", "GPT-4o-mini", "#2a78d6", "o"),
          ("meta-llama/llama-3.3-70b-instruct", "Llama-3.3-70B", "#eb6834", "s"),
          ("anthropic/claude-haiku-5.5", "Haiku 5.5", "#1baf7a", "^")]
plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK2, "xtick.color": INK2,
                     "ytick.color": INK2, "text.color": INK, "axes.spines.top": False, "axes.spines.right": False})


def fig_dispersion():
    sets = [("a  Retail II setting (mean about 0.5)", "retail_ci.csv", 2.49, 2.10, (-0.15, 4.1)),
            ("b  Grocery setting (mean about 4.8)", "grocery_ci.csv", 7.85, 6.61, (-0.5, 13.8))]
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.6))
    for ax, (title, fn, ref, ceil, xl) in zip(axes, sets):
        df = pd.read_csv(fn)
        rows = [(c, an) for c in "ABCD" for an in (False, True)]
        for ri, (c, an) in enumerate(rows):
            y0 = len(rows) - 1 - ri
            for mi, (mid, name, col, mk) in enumerate(MODELS):
                r = df[(df.model == mid) & (df.cond == c) & (df.anchor == an)].iloc[0]
                y = y0 + (1 - mi) * 0.22
                ax.plot([r.var_mean_lo, r.var_mean_hi], [y, y], color=col, lw=1.4, solid_capstyle="round", zorder=2)
                ax.plot(r.var_mean, y, mk, ms=5.5, mfc=col if not an else "white", mec=col, mew=1.4, zorder=3)
        ax.axvline(ref, color=INK, lw=1.2, ls="--", zorder=1)
        ax.axvline(ceil, color=INK2, lw=0.9, ls=":", zorder=1)
        ax.text(ref, len(rows) - 0.35, f" real {ref}", ha="left", va="bottom", fontsize=8, color=INK)
        ax.text(ceil, len(rows) - 0.35, f"C ceiling {ceil} ", ha="right", va="bottom", fontsize=7.5, color=INK2)
        ax.set_yticks([len(rows) - 1 - i for i in range(len(rows))])
        ax.set_yticklabels([f"{c} {'anchored' if an else 'plain'}" for c, an in rows], fontsize=8)
        ax.set_xlim(*xl); ax.set_ylim(-0.7, len(rows) + 0.35)
        ax.set_xlabel("variance / mean (95% CI)"); ax.set_title(title, loc="left", fontsize=10, color=INK)
        ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True)
    handles = [plt.Line2D([], [], marker=mk, color=col, ls="", ms=6, label=name) for _, name, col, mk in MODELS]
    handles += [plt.Line2D([], [], marker="o", color=INK2, mfc=INK2, ls="", ms=6, label="plain prompt"),
                plt.Line2D([], [], marker="o", color=INK2, mfc="white", ls="", ms=6, label="anchored prompt")]
    fig.legend(handles=handles, loc="lower center", ncol=5, frameon=False, fontsize=8.5)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig("fig1_dispersion.png", dpi=200); plt.close(fig)


def fig_lift():
    df = pd.read_csv("hillstrom_table.csv")
    df = df[df.method == "C_prob"]
    real = {"visit": (0.0766, 0.0766 - 0.0066, 0.0766 + 0.0066), "purchase": (0.0068, 0.0068 - 0.0018, 0.0068 + 0.0018)}
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.5))
    for ax, outcome, title in zip(axes, ("visit", "purchase"), ("a  Website visit (2 weeks)", "b  Purchase (2 weeks), log scale")):
        rows = [(m, an) for m in range(3) for an in (False, True)]
        for ri, (mi, an) in enumerate(rows):
            mid, name, col, mk = MODELS[mi]
            r = df[(df.model == mid) & (df.anchor == an) & (df.outcome == outcome)].iloc[0]
            y = len(rows) - 1 - ri
            x = max(r.RD_men, 1e-4)
            ax.plot(x, y, mk, ms=7, mfc=col if not an else "white", mec=col, mew=1.5, zorder=3)
            ax.text(x * (1.10 if outcome == "purchase" else 1.0) + (0 if outcome == "purchase" else 0.006), y, f"{r.RD_men:+.3f}", va="center", fontsize=7.5, color=INK2)
        v, lo, hi = real[outcome]
        ax.axvspan(lo, hi, color="#cfcdc6", alpha=0.6, lw=0, zorder=0)
        ax.axvline(v, color=INK, lw=1.2, ls="--", zorder=1)
        ax.text(v, len(rows) - 0.25, f" real {v:+.4f}", ha="left", va="bottom", fontsize=8, color=INK)
        ax.set_yticks(range(len(rows))[::-1]); ax.set_yticklabels([f"{MODELS[m][1]}, {'anchored' if an else 'plain'}" for m, an in rows], fontsize=8)
        if outcome == "purchase":
            ax.set_xscale("log"); ax.set_xlim(0.003, 0.4)
        else:
            ax.set_xlim(-0.012, 0.26)
        ax.set_ylim(-0.7, len(rows) + 0.3)
        ax.set_xlabel("men's email minus no email (probability)"); ax.set_title(title, loc="left", fontsize=10, color=INK)
        ax.grid(axis="x", color=GRID, lw=0.6); ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig("fig2_lift.png", dpi=200); plt.close(fig)


if __name__ == "__main__":
    fig_dispersion(); fig_lift(); print("ok")
