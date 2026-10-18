"""Conceptual model figures. Figure 1: propositions. Figure 2: same model with empirical support."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

BOX = {  # name: (x, y, w, h, label)
    "AB": (0.02, 0.78, 0.20, 0.14, "Authority binding\n(binding vs. advisory)"),
    "RT": (0.02, 0.52, 0.20, 0.14, "Office rents"),
    "ER": (0.02, 0.26, 0.20, 0.14, "Election rule\n(plurality vs. ranked)"),
    "MC": (0.02, 0.00, 0.20, 0.14, "Agent capability /\nmodel family"),
    "CC": (0.40, 0.52, 0.20, 0.14, "Candidacy and\nelectoral competition"),
    "DA": (0.76, 0.78, 0.22, 0.14, "Inequality of access\nto tasks"),
    "PC": (0.76, 0.36, 0.22, 0.14, "Persistence of\ncontrol over office"),
    "WN": (0.40, 0.00, 0.20, 0.14, "Who holds office"),
}

def centre(k, side):
    x, y, w, h, _ = BOX[k]
    return {"r": (x + w, y + h / 2), "l": (x, y + h / 2), "t": (x + w / 2, y + h), "b": (x + w / 2, y)}[side]

def arrow(ax, a, sa, b, sb, style, color, label=None, lpos=(0, 0), rad=0.0, ha="center"):
    p = FancyArrowPatch(centre(a, sa), centre(b, sb), arrowstyle="-|>", mutation_scale=14, lw=1.6,
                        linestyle=style, color=color, connectionstyle=f"arc3,rad={rad}")
    ax.add_patch(p)
    if label:
        (x1, y1), (x2, y2) = centre(a, sa), centre(b, sb)
        ax.text((x1 + x2) / 2 + lpos[0], (y1 + y2) / 2 + lpos[1], label, fontsize=8.5, ha=ha, va="center",
                bbox=dict(fc="white", ec="none", pad=1.2))

def moderation(ax, label, color):
    ax.add_patch(FancyArrowPatch((0.22, 0.63), (0.49, 0.85), arrowstyle="-|>", mutation_scale=14, lw=1.6,
                                 linestyle=":", color=color))
    ax.text(0.54, 0.715, label, fontsize=8.5, ha="center", va="center", bbox=dict(fc="white", ec="none", pad=1.2))


def draw(annotated, path):
    fig, ax = plt.subplots(figsize=(11, 6.2))
    ax.set_xlim(-0.02, 1.02); ax.set_ylim(-0.14, 1.0); ax.axis("off")
    for k, (x, y, w, h, t) in BOX.items():
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.01", fc="#f3f4f6", ec="#374151", lw=1.4))
        ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=10)
    S, D, T = "-", "--", ":"
    g, r, o = "#1f2937", "#9ca3af", "#b45309"
    if not annotated:
        arrow(ax, "RT", "r", "CC", "l", S, g, "P1 (+)", (0, 0.035))
        arrow(ax, "MC", "r", "WN", "l", S, g, "P5", (0, 0.035))
        arrow(ax, "CC", "r", "PC", "t", S, g, "(+)", (0.0, 0.04))
        arrow(ax, "AB", "r", "DA", "l", S, g, "P2 (+ inequality)", (0, 0.035))
        arrow(ax, "ER", "r", "PC", "l", S, g, "P4 (reduces)", (0.0, 0.035), rad=-0.12)
        moderation(ax, "P3 (moderation)", o)
        ax.set_title("Figure 1. Conceptual model and propositions", fontsize=12, loc="left")
        ax.text(0.0, -0.1, "Solid arrows: main-effect propositions. Dotted arrow: moderation of the authority effect by office rents (P3). Signs show predicted direction.",
                fontsize=8.5, color="#4b5563")
    else:
        arrow(ax, "RT", "r", "CC", "l", S, g, "supported", (0, 0.035))
        arrow(ax, "MC", "r", "WN", "l", S, g, "supported for standing;\nweak for winning", (0, 0.05))
        arrow(ax, "CC", "r", "PC", "t", S, g, "rents lengthen spells", (-0.02, 0.05))
        arrow(ax, "AB", "r", "DA", "l", S, g, "reduces Gini (opposite to P2); no effect on exclusion spells", (0, 0.035))
        arrow(ax, "ER", "r", "PC", "l", D, r, "no effect", (0.0, 0.035), rad=-0.12)
        moderation(ax, "weak: rents remove the\nexclusion benefit (p = 0.055)", o)
        ax.set_title("Figure 2. Empirical support for the model (168 worlds)", fontsize=12, loc="left")
        ax.text(0.0, -0.1, "Solid: supported. Dashed grey: no detectable effect. Dotted: weak or suggestive. Authority binding had no detectable effect on persistence of control.\nMediation by candidacy was not tested.",
                fontsize=8.5, color="#4b5563")
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)

draw(False, "figure1.png")
draw(True, "figure2.png")
