import numpy as np, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from formal_model import R, FG, costs, summarize
SURF, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e1"
BLUE, ORANGE = "#2a78d6", "#eb6834"
cJ0, cR, L = 0.0174, 20.0, 100.0
r = R["mixture"]
fig, ax = plt.subplots(1, 2, figsize=(10.4, 4.3), dpi=200, facecolor=SURF)
for a in ax:
    a.set_facecolor(SURF)
    for s in ("top", "right"): a.spines[s].set_visible(False)
    for s in ("left", "bottom"): a.spines[s].set_color(INK2); a.spines[s].set_linewidth(0.8)
    a.tick_params(colors=INK2, labelsize=9); a.grid(axis="y", color=GRID, lw=0.8); a.set_axisbelow(True)
# Panel A: cost vs share judged, pi = 10%
pi = 0.10
for mult, col, lab in ((1, BLUE, "judge price ×1 (US$0.017/doc)"), (100, ORANGE, "judge price ×100 (US$1.74/doc)")):
    casc, _, jall, none = costs(r, pi, cJ0 * mult, cR, L)
    q = pi * r[:, 0] + (1 - pi) * FG; o = np.argsort(q)
    ax[0].plot(q[o] * 100, casc[o] * 1000, color=col, lw=2, label=lab)
    k = int(np.argmin(casc)); ax[0].plot(q[k] * 100, casc[k] * 1000, "o", ms=8, color=col, mec=SURF, mew=2)
    ax[0].plot(100, jall * 1000, "s", ms=8, color=col, mec=SURF, mew=2)
ax[0].set_xlabel("Share of all documents sent to the judge, q (%)", color=INK2, fontsize=9.5)
ax[0].set_ylabel("Expected cost per 1,000 documents (US$)", color=INK2, fontsize=9.5)
ax[0].set_title("A. Cost against depth (10% machine papers)", color=INK, fontsize=10.5, loc="left")
ax[0].text(52, 8000, "circle: cascade optimum\nsquare: judge on all documents", color=INK2, fontsize=8.5, va="top")
ax[0].legend(frameon=False, fontsize=8.5, labelcolor=INK2, loc="upper left")
# Panel B: optimal q* against base rate
pis = np.array([0.005, 0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.50])
for mult, col, lab in ((1, BLUE, "judge price ×1"), (100, ORANGE, "judge price ×100")):
    qs = [summarize(r, p, cJ0 * mult, cR, L)["q"] * 100 for p in pis]
    ax[1].plot(pis * 100, qs, color=col, lw=2, marker="o", ms=8, mec=SURF, mew=2, label=lab)
ax[1].set_xscale("log"); ax[1].set_xticks([0.5, 1, 2, 5, 10, 20, 50]); ax[1].set_xticklabels(["0.5", "1", "2", "5", "10", "20", "50"])
ax[1].set_xlabel("Share of machine papers in the stream, π (%)", color=INK2, fontsize=9.5)
ax[1].set_ylabel("Cost-minimizing share judged, q* (%)", color=INK2, fontsize=9.5)
ax[1].set_title("B. Optimal depth rises with the base rate", color=INK, fontsize=10.5, loc="left")
ax[1].legend(frameon=False, fontsize=8.5, labelcolor=INK2, loc="upper left")
fig.text(0.01, 0.01, r"Equal-weight mixture of GPT-4o, Claude, and Llama papers. Review cost (US\$20 per flagged paper) and loss (US\$100 per missed paper) are assumptions.", color=INK2, fontsize=7.8)
plt.tight_layout(rect=(0, 0.04, 1, 1)); plt.savefig("fig_formal_model.png", facecolor=SURF)
print("ok")
