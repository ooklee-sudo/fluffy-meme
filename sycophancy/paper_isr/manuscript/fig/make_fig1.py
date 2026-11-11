"""Figure 1: expected loss under P3 (evidence required) and P4 (evidence + tool) as the cost of
fabricating evidence F rises; authors and challengers dispute. Values from policy_sim.py."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

F = [0, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0]
D = {  # model: (P0, P3 by F, P4 by F)
    "Qwen3-4B": (49.6, [77.4] * 5 + [22.7, 8.4], [49.2] * 3 + [25.3] * 3 + [9.5]),
    "Qwen3-8B": (43.1, [140.4] * 6 + [0.0], [46.4] * 3 + [28.2] * 2 + [8.8] * 2),
    "Claude Haiku 5.5": (24.8, [21.6] * 3 + [11.9] * 4, [22.3, 19.0, 19.0] + [8.9] * 4),
    "GPT-6 Luna": (23.6, [38.6] + [34.8] * 4 + [16.1] * 2, [34.8] * 5 + [18.3] * 2),
    "DeepSeek V4.1": (17.5, [30.7] + [25.7] * 4 + [4.4] * 2, [18.3] * 3 + [7.3] * 4),
}
BLUE, ORANGE, INK, MUTED, GRID = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5, "axes.edgecolor": MUTED,
                     "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})
fig, axes = plt.subplots(1, 5, figsize=(10.5, 2.7), constrained_layout=True)
x = list(range(len(F)))
for ax, (name, (p0, p3, p4)) in zip(axes, D.items()):
    ax.axhline(p0, color=MUTED, lw=1, ls=":", zorder=1)
    ax.step(x, p3, where="post", color=BLUE, lw=2, zorder=3)
    ax.plot(x, p3, "o", color=BLUE, ms=4.5, mec="white", mew=1, zorder=4)
    ax.step(x, p4, where="post", color=ORANGE, lw=2, ls="--", zorder=3)
    ax.plot(x, p4, "s", color=ORANGE, ms=4.5, mec="white", mew=1, zorder=4)
    ax.set_title(name, fontsize=9, color=INK)
    ax.set_xticks(x, [f"{f:g}" for f in F], fontsize=7)
    ax.set_xlabel("Fabrication cost F", fontsize=8)
    ax.set_ylim(bottom=0, top=max(max(p3), max(p4), p0) * 1.12)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
axes[0].set_ylabel("Loss per 100 submissions")
from matplotlib.lines import Line2D
fig.legend(handles=[Line2D([], [], color=BLUE, lw=2, marker="o", label="P3 evidence required"),
                    Line2D([], [], color=ORANGE, lw=2, ls="--", marker="s", label="P4 evidence + execution tool"),
                    Line2D([], [], color=MUTED, lw=1, ls=":", label="P0 no pushback")],
           loc="outside upper center", ncol=3, frameon=False, fontsize=8)
fig.savefig("fig/figure1_evidence_window.png", dpi=300)
print("saved")
