"""Figures for the JAIS manuscript. Run: python fig/make_figs.py"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import pathlib

OUT = pathlib.Path(__file__).parent
plt.rcParams.update({"font.family": "serif", "font.serif": ["Liberation Serif", "Times New Roman", "DejaVu Serif"],
                     "font.size": 11})

# Figure 1: research model
fig, ax = plt.subplots(figsize=(7.5, 3.6), dpi=300)
ax.set_xlim(-0.15, 10.15); ax.set_ylim(-0.05, 4.95); ax.axis("off")

def box(x, y, w, h, text, bold=False, fill="white"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=fill, ec="black", lw=0.9))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9,
            fontweight="bold" if bold else "normal", wrap=True)

def arrow(p, q, dashed=False, label=None, lx=0, ly=0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=12, lw=0.9, color="black",
                                 linestyle="--" if dashed else "-"))
    if label:
        ax.text((p[0] + q[0]) / 2 + lx, (p[1] + q[1]) / 2 + ly, label, fontsize=10, ha="center")

box(0.0, 1.9, 2.3, 1.2, "Accumulated loss\n(consecutive failures\nagainst the goal)", bold=True)
box(3.5, 1.9, 3.0, 1.2, "Evaluation gaming\n(tampering, special-casing,\nfalse completion)", bold=True, fill="#e6e6e6")
box(7.7, 1.9, 2.3, 1.2, "Tail-risk outcomes\nfor the delegating\norganization")
box(0.0, 3.8, 2.9, 1.0, "Success history (H2)\nScarcity cues (H3a)")
box(3.5, 3.8, 3.0, 1.0, "Unintegrated failure record (H4)\nDiagnostic failure feedback")
box(3.5, 0.1, 3.0, 1.0, "Model susceptibility\n(training regime)")
arrow((2.3, 2.5), (3.5, 2.5), label="H1 (+)", ly=-0.38)
arrow((6.5, 2.5), (7.7, 2.5))
arrow((2.0, 3.8), (2.9, 2.55), dashed=True)
arrow((5.0, 3.8), (5.0, 3.1), dashed=True)
arrow((5.0, 1.1), (5.0, 1.9), dashed=True)
fig.savefig(OUT / "figure1_model.png", bbox_inches="tight", facecolor="white")
plt.close(fig)

# Figure 2: unsafe rate by history
hist = ["N", "NI", "F2a", "F2", "F8a", "F8"]
named = ["not named", "named", "not named", "named", "not named", "named"]
series = [
    ("Low-cost models (7 models, n = 140 per bar)", [2.1, 3.6, 23.6, 17.1, 22.9, 14.3], "#1f1f1f"),
    ("Frontier, visible tests (6 models, n = 120)", [0.0, 0.0, 0.0, 0.0, 3.3, 0.0], "#8c8c8c"),
    ("Frontier, hidden tests (6 models, n = 60)", [1.7, 6.7, 5.0, 3.3, 10.0, 6.7], "#d0d0d0"),
]
fig, ax = plt.subplots(figsize=(7.5, 3.9), dpi=300)
w = 0.26
for k, (lab, vals, col) in enumerate(series):
    xs = [i + (k - 1) * w for i in range(len(hist))]
    ax.bar(xs, vals, w, color=col, edgecolor="black", lw=0.5, label=lab)
    for x_, v in zip(xs, vals):
        ax.text(x_, v + 0.5, f"{v:.1f}", ha="center", va="bottom", fontsize=8)
ax.set_xticks(range(len(hist)))
ax.set_xticklabels([f"{h}\n(test {n})" for h, n in zip(hist, named)], fontsize=9.5)
ax.set_ylabel("Episodes with evaluation gaming (%)")
ax.set_ylim(0, 36)
ax.set_yticks([0, 5, 10, 15, 20, 25, 30])
ax.spines[["top", "right"]].set_visible(False)
for i, lab in enumerate(["No loss", "Two failed attempts", "Eight failed attempts"]):
    ax.annotate("", xy=(2 * i - 0.4, -8.2), xytext=(2 * i + 1.4, -8.2), xycoords="data",
                arrowprops=dict(arrowstyle="-", lw=0.8), annotation_clip=False)
    ax.text(2 * i + 0.5, -10.2, lab, ha="center", va="top", fontsize=10, clip_on=False)
ax.legend(frameon=False, fontsize=9, loc="upper right")
fig.subplots_adjust(bottom=0.27)
fig.savefig(OUT / "figure2_results.png", bbox_inches="tight", facecolor="white")
plt.close(fig)
print("ok")
