"""Figure 2: drift hazard and optimal retraining threshold vs. days since the last drift event.

Reads results_hazard.json from hazard_mdp.py; writes fig_hazard.png (same monochrome style as Figure 1).
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

r = json.load(open("results_hazard.json"))
U_SHOW = 60
STYLE = {  # line style + marker carry identity (print and colorblind safe), ink stays black/gray
    "0.5": dict(ls="-", marker="o", color="black", label="IMRL (Weibull shape 0.5)"),
    "1.0": dict(ls=":", marker=None, color="0.45", label="Memoryless (Poisson)"),
    "2.0": dict(ls="--", marker="s", color="black", label="DMRL (Weibull shape 2)"),
}
plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.linewidth": 0.8})
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 3.1), dpi=300)
for k, s in r["shapes"].items():
    st = STYLE[k]
    u = list(range(U_SHOW + 1))
    kw = dict(ls=st["ls"], color=st["color"], lw=1.2, marker=st["marker"], ms=3.5, markevery=5,
              mfc="white", label=st["label"])
    ax1.plot(u, s["hazard"][:U_SHOW + 1], **kw)
    th = [t if t is not None else float("nan") for t in s["thresholds"][:U_SHOW + 1]]
    ax2.plot(u, th, drawstyle="steps-post", **kw)
ax1.set_xlabel("Days since last drift event, $u$")
ax1.set_ylabel("Daily drift hazard $h(u)$")
ax1.set_ylim(0, None)
ax2.set_xlabel("Days since last drift event, $u$")
ax2.set_ylabel("Optimal retraining threshold $X^\\star(u)$")
for ax, tag in ((ax1, "(a)"), (ax2, "(b)")):
    ax.set_xlim(0, U_SHOW)
    ax.grid(True, lw=0.3, color="0.85")
    ax.text(0.02, 0.97, tag, transform=ax.transAxes, va="top", fontweight="bold")
ax2.set_ylim(0, 14)  # above this the shape-2 policy never retrains (states almost never reached)
handles, labels = ax2.get_legend_handles_labels()
fig.legend(handles, labels, loc="lower center", ncol=3, frameon=False, fontsize=8)
fig.tight_layout(rect=(0, 0.08, 1, 1))
fig.savefig("fig_hazard.png")
print("wrote fig_hazard.png")
