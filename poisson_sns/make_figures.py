"""Figures for the manuscript (print-safe: distinct line styles/markers, grayscale-readable)."""
import json, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from sim import Sim
from analysis import reference_hourly

OUT = "../dss_revision/figures/"
plt.rcParams.update({"font.size": 9, "font.family": "serif", "axes.spines.top": False,
                     "axes.spines.right": False, "axes.linewidth": 0.8})
BLUE, ORANGE, GRAY = "#1f5fa8", "#c4560b", "#555555"

# Fig 2: hourly distribution
ref = reference_hourly()
fig, ax = plt.subplots(figsize=(6.2, 3.0))
hrs = np.arange(24) + 0.5
ax.plot(hrs, ref * 100, color="black", lw=2, label="Reference (assumed)")
for sch, col, ls, lab in [("ipp", BLUE, "-", "IPP (proposed)"), ("hpp", ORANGE, "--", "Homogeneous Poisson"),
                          ("poll", GRAY, ":", "Fixed-period polling")]:
    reps = []
    for seed in (1, 2, 3):
        s = Sim(800, 5, seed, scheduler=sch).run(72)
        h = np.zeros(24)
        for t, a, act, i, d in s.events:
            if act < 3:
                h[int(t % 24)] += 1
        reps.append(h / h.sum())
    ax.plot(hrs, np.mean(reps, 0) * 100, color=col, ls=ls, lw=1.6, label=lab)
ax.set_xlabel("Hour of day"); ax.set_ylabel("Share of posting events (%)")
ax.set_xticks(range(0, 25, 3)); ax.set_xlim(0, 24); ax.set_ylim(0)
ax.legend(frameon=False, fontsize=8, loc="upper left")
fig.tight_layout(); fig.savefig(OUT + "fig2_hourly.png", dpi=300); plt.close(fig)

# Fig 3: adopters and t50 by strategy (40 paired replications, surrogate)
d = json.load(open("results_study2_surrogate.json"))["runs"]
fig, axs = plt.subplots(1, 2, figsize=(6.2, 3.0))
rng = np.random.default_rng(1)
for ax, key, yl in [(axs[0], "adopters", "Adopters within 48 h"), (axs[1], "t50", "Time to 50% of adopters (h)")]:
    for i, (cond, col, lab) in enumerate([("concentrated", BLUE, "Concentrated"), ("distributed", ORANGE, "Distributed")]):
        v = np.array([r[key] for r in d if r["cond"] == cond])
        ax.scatter(i + rng.uniform(-0.12, 0.12, len(v)), v, s=14, color=col, alpha=0.75, edgecolor="white", linewidth=0.4,
                   marker="o" if i == 0 else "s")
        ax.hlines(np.mean(v), i - 0.25, i + 0.25, color="black", lw=1.8)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["Concentrated\n(3 influencers)", "Distributed\n(ordinary users)"])
    ax.set_ylabel(yl); ax.set_xlim(-0.6, 1.6); ax.set_ylim(0)
axs[0].text(1.55, 0.02, "bar = mean", transform=axs[0].get_xaxis_transform(), ha="right", fontsize=7, color=GRAY)
fig.tight_layout(); fig.savefig(OUT + "fig3_seeding.png", dpi=300); plt.close(fig)

# Fig 1: architecture
fig, ax = plt.subplots(figsize=(6.2, 3.0)); ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 5)
def box(x, y, w, h, text, fc="#eef3fa"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.04,rounding_size=0.12", fc=fc, ec="#333333", lw=0.9))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=8)
def arrow(x0, y0, x1, y1, text=None):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="->", lw=0.9, color="#333333"))
    if text: ax.text((x0 + x1) / 2, (y0 + y1) / 2 + 0.16, text, ha="center", fontsize=7, color=GRAY)
box(0.1, 3.3, 2.4, 1.3, "Platform\nfollower graph, feeds,\nnotifications")
box(3.8, 3.3, 2.4, 1.3, "Intensity oracle\n(rule-based or LLM)\nrates urge 0-5", fc="#fdf0e6")
box(7.5, 3.3, 2.4, 1.3, "Intensity\nlambda(t) = baseline x\ncircadian + stimuli")
box(7.5, 0.4, 2.4, 1.3, "Thinning scheduler\ndraws next\naction time")
box(3.8, 0.4, 2.4, 1.3, "Persona agent\nchooses action type\n(post/comment/RT/like)")
box(0.1, 0.4, 2.4, 1.3, "Event log\nadopters, timing,\ncascade size", fc="#eef6ee")
arrow(2.5, 3.95, 3.8, 3.95, "exposure")
arrow(6.2, 3.95, 7.5, 3.95, "stimulus")
arrow(8.7, 3.3, 8.7, 1.7)
arrow(7.5, 1.05, 6.2, 1.05, "event time")
arrow(3.8, 1.05, 2.5, 1.05)
arrow(1.3, 1.7, 1.3, 3.3)
ax.text(1.0, 2.5, "new content", ha="right", fontsize=7, color=GRAY)
fig.tight_layout(); fig.savefig(OUT + "fig1_architecture.png", dpi=300); plt.close(fig)
print("ok")
