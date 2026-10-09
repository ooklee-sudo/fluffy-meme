"""Figures for the manuscript (run from the repository root: python paper/make_figures.py)."""
import sys
sys.path.insert(0, ".")
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import theory_check as th
import theory_props as tpr
from schedule_test import profile_from

plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
prof = profile_from("results/longtrace_azure.md")
K, c = 24, 77
Lams = 1.4 * c * prof / prof.mean()
pstar = np.array([tpr.toll_at(th.first_best(L, c), c) for L in Lams])

# best two-level schedule
grid = np.linspace(0, th.P, 161)
Wt = np.array([[th.w_phase(th.eq_rate(p, L, c), L, c) for p in grid] for L in Lams])
order = np.argsort(-Lams)
best = (-1e18, None)
for m in range(1, K):
    wh, wo = Wt[order[:m]].sum(0), Wt[order[m:]].sum(0)
    v = wh.max() + wo.max()
    if v > best[0]:
        best = (v, (m, grid[wo.argmax()], grid[wh.argmax()]))
m, po, ph = best[1]
sched = np.full(K, po)
sched[order[:m]] = ph

fig, ax = plt.subplots(figsize=(6.2, 3.0))
h = np.arange(K)
ax.bar(h, prof, color="#c9d6e8", width=0.8)
ax.set_xlabel("Hour of day (UTC)"); ax.set_ylabel("Demand relative to mean")
ax2 = ax.twinx(); ax2.spines["right"].set_visible(True)
ax2.plot(h, pstar, color="#b2182b", marker="o", ms=3, lw=1.2, label="First-best toll")
ax2.step(np.arange(K + 1) - 0.5, np.r_[sched, sched[-1]], where="post", color="#1b7837", lw=1.6, label=f"Best two-level schedule ({m} peak hours)")
ax2.set_ylabel("Price (delay-cost units)")
ax2.legend(loc="upper left", frameon=False, fontsize=8)
fig.tight_layout(); fig.savefig("paper/figures/fig1.png", dpi=200); plt.close(fig)

# Figure 2: switching speed (values from results/switching_scaling.md)
burst = [0.02, 0.04, 0.08, 0.21, 0.41, 0.82, 2.06, 4.12, 8.23, 20.58]
loss = [0.28, 0.72, 1.32, 3.66, 7.05, 11.27, 17.03, 19.01, 16.91, 17.03]
fig, ax = plt.subplots(figsize=(4.8, 3.0))
ax.semilogx(burst, loss, marker="o", ms=4, color="#2166ac")
ax.set_xlabel("Mean burst length (mean service times)"); ax.set_ylabel("Welfare loss of best flat price (%)")
fig.tight_layout(); fig.savefig("paper/figures/fig2.png", dpi=200); plt.close(fig)

# Figure 3: G-level recovery (values from results/two_level_theory.md, first row)
G = [1, 2, 3, 4, 6]
quad = [0, 0.76, 0.89, 0.97, 0.99]
exact = [0, 0.69, 0.85, 0.94, 0.98]
fig, ax = plt.subplots(figsize=(4.8, 3.0))
ax.plot(G, quad, marker="s", ms=4, ls="--", color="#999999", label="Quadratic prediction")
ax.plot(G, exact, marker="o", ms=4, color="#2166ac", label="Exact")
ax.set_xlabel("Number of price levels G"); ax.set_ylabel("Share of flat-price loss recovered")
ax.set_ylim(0, 1.02); ax.legend(frameon=False)
fig.tight_layout(); fig.savefig("paper/figures/fig3.png", dpi=200); plt.close(fig)
print("two-level:", m, po, ph)
