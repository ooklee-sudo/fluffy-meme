"""Figures 1 and 2 for the IJRM manuscript, drawn from the values printed in Tables 2 and 6 of the manuscript."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"font.family": "serif", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

# Figure 1: Table 2 (beta = 0, equal-link budget, 30 paired replications)
hours = [0, 1, 2, 3, 6, 12, 48]
conc = [0, 56, 108, 156, 248, 287, 299]
dist = [0, 50, 84, 106, 135, 141, 144]
fig, ax = plt.subplots(figsize=(5.5, 3.6))
ax.plot(hours, conc, "k-o", ms=4, label="Concentrated (3 influencers)")
ax.plot(hours, dist, "k--s", ms=4, mfc="white", label="Distributed (about 428 ordinary users)")
ax.set_xscale("symlog", linthresh=3, linscale=1.0)
ax.set_xticks([0, 1, 2, 3, 6, 12, 24, 48]); ax.set_xticklabels([0, 1, 2, 3, 6, 12, 24, 48])
ax.set_xlabel("Hours after injection (axis compressed beyond 3 h)")
ax.set_ylabel("Mean cumulative adopters")
ax.legend(frameon=False, loc="lower right")
fig.tight_layout()
for ext, kw in (("pdf", {}), ("png", {"dpi": 400})):
    fig.savefig(f"Figure_1.{ext}", **kw)

# Figure 2: Table 6
beta = [0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.50]
d = [157, 140, 117, 49, 2, 33, -52, -116]
lo = [100, 84, 39, -10, -26, -26, -82, -135]
hi = [218, 198, 218, 131, 37, 100, -16, -91]
dv = [7.8, 6.6, -2.5, -15.4, -19.1, -22.6, -29.7, -42.1]
vlo = [2.2, -1.6, -7.8, -21.1, -23.1, -26.9, -33.4, -45.7]
vhi = [14.1, 15.2, 3.7, -10.8, -14.7, -18.7, -25.4, -38.6]
fig, ax = plt.subplots(figsize=(5.5, 3.8))
ax.errorbar(beta, d, yerr=[[a - b for a, b in zip(d, lo)], [b - a for a, b in zip(d, hi)]], fmt="k-o", ms=4, capsize=3, label="Final adopters (48 h)")
off = [b + 0.006 for b in beta]
ax.errorbar(off, dv, yerr=[[a - b for a, b in zip(dv, vlo)], [b - a for a, b in zip(dv, vhi)]], fmt="--s", color="0.45", ms=4, capsize=3, label=r"Discounted reach $V(\delta=1/\mathrm{h})$")
ax.axhline(0, color="k", lw=0.8)
ax.set_xlabel(r"Engagement elasticity $\beta$")
ax.set_ylabel("Concentrated minus distributed")
ax.legend(frameon=False, loc="upper right")
fig.tight_layout()
for ext, kw in (("pdf", {}), ("png", {"dpi": 400})):
    fig.savefig(f"Figure_2.{ext}", **kw)
