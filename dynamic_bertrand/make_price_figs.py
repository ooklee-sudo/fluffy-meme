"""Figure for the dynamic-pricing section: Edgeworth cycle at fixed capacities."""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(HERE, "results")
d = json.load(open(os.path.join(R, "price_game.json")))
prices = np.array(d["prices"])
case = [c for c in d["cases"] if (c["mA"], c["mB"]) == (3, 3) and c["rho_target"] == 0.1][0]
cases_11 = [c for c in d["cases"] if (c["mA"], c["mB"]) == (1, 1) and c["rho_target"] == 0.1][0]
cases_13 = [c for c in d["cases"] if (c["mA"], c["mB"]) == (1, 3) and c["rho_target"] == 0.1][0]

fig, axs = plt.subplots(1, 3, figsize=(11, 3.3), sharey=True)
for ax, (c, l, title) in zip(axs, [(cases_11, 1, "(1,1) nodes, medium demand\n(scarce capacity)"),
                                    (case, 1, "(3,3) nodes, medium demand\n(ample capacity)"),
                                    (case, 2, "(3,3) nodes, high demand\n(ample capacity)")]):
    path = c["paths"][str(l)][:18]
    t = np.arange(len(path))
    pa = [p for (m, p) in path if m == 0]; ta = [i for i, (m, p) in enumerate(path) if m == 0]
    pb = [p for (m, p) in path if m == 1]; tb = [i for i, (m, p) in enumerate(path) if m == 1]
    # prices stay in force until the firm moves again: step plots
    ax.step(ta + [len(path)], pa + [pa[-1]], where="post", color="#3b6ea8", lw=2, label="Firm A")
    ax.step(tb + [len(path)], pb + [pb[-1]], where="post", color="#c9733a", lw=2, ls="--", label="Firm B")
    ax.set_title(title, fontsize=9)
    ax.set_xlabel("period")
    ax.spines[["top", "right"]].set_visible(False)
axs[0].set_ylabel("posted price")
axs[0].legend(frameon=False, fontsize=8, loc="center right")
fig.tight_layout()
fig.savefig(os.path.join(R, "edgeworth_cycle.png"), dpi=200, bbox_inches="tight")

print("ok")
