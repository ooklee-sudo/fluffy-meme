"""Figures for Section 6 from calibration_results.json.

usage: python3 -I make_figures.py RESULTS_JSON OUT_DIR
"""
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({"font.family": "serif", "font.serif": ["DejaVu Serif"], "font.size": 10})
R = json.load(open(sys.argv[1]))
out = sys.argv[2]
os.makedirs(out, exist_ok=True)
NAMES = json.load(open(os.path.join(os.path.dirname(__file__), "model_names.json")))

# Figure 1: survival curve and fits ---------------------------------------------
b = R["baseline"]
u = np.array([float(x) for x in b["S_obs"]])
S = np.array(list(b["S_obs"].values()))
uu = np.logspace(-3, 0, 300)
fig, ax = plt.subplots(figsize=(6.2, 4.0))
ax.loglog(uu, np.exp(-b["theta_exp"] * uu), "--", color="#d9622b", lw=1.6,
          label=f"Exponential, θ = {b['theta_exp']:.1f}")
ax.loglog(uu, (1 + b["theta"] * uu / b["k"]) ** (-b["k"]), "-", color="#2a6fdb", lw=1.8,
          label=f"Gamma-mixed, k = {b['k']:.2f}")
ax.loglog(u, S, "o", mfc="white", mec="black", label="Observed")
ax.set_ylim(5e-3, 1.3)
ax.set_xlabel("Fraction of the test suite executed (random order)")
ax.set_ylabel("Share of defects not yet detected")
ax.grid(True, which="major", color="#dddddd", lw=0.6)
ax.spines[["top", "right"]].set_visible(False)
ax.legend(frameon=False, loc="lower left")
fig.tight_layout(); fig.savefig(os.path.join(out, "fig1.png"), dpi=300); plt.close(fig)

# Figure 2: sensitivity ---------------------------------------------------------------
sens = R["sensitivity"]
names = list(sens)
fig, ax = plt.subplots(figsize=(6.2, 3.6))
y = np.arange(len(names))[::-1]
for yi, n in zip(y, names):
    s = sens[n]
    ax.errorbar(s["eps"], yi, xerr=[[s["eps"] - s["eps_ci"][0]], [s["eps_ci"][1] - s["eps"]]],
                fmt="o", color="#2a6fdb", ecolor="#2a6fdb", capsize=3)
ax.axvline(sens[names[0]]["eps"], ls=":", color="gray")
ax.set_yticks(y); ax.set_yticklabels(names, fontsize=8.5)
ax.set_xlabel("Implied elasticity ε = 1/(1 + k)")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(out, "fig2.png"), dpi=300); plt.close(fig)

# Figure 3: detectability against defect intensity across models -----------------
pm = R["eta_main"]["per_model"]
core = set(R["core_models"])
fig, ax = plt.subplots(figsize=(6.2, 4.0))
xs, ys = [], []
for m, v in pm.items():
    if v["ln_theta_dm"] is None:
        continue
    x, yv = np.log(v["lam"]), v["ln_theta_dm"]
    xs.append(x); ys.append(yv)
    ax.plot(x, yv, "o", color="#2a6fdb" if m in core else "#9aa5b1", ms=6)
xs, ys = np.array(xs), np.array(ys)
eta = R["eta_main"]["eta"]
xx = np.linspace(xs.min() - 0.1, xs.max() + 0.1, 50)
ax.plot(xx, ys.mean() + eta * (xx - xs.mean()), "-", color="black", lw=1,
        label=f"Task fixed-effects slope, η̂ = {eta:.2f}")
ax.set_xlabel("ln defect intensity λ (defects per sample)")
ax.set_ylabel("ln detection rate (task-demeaned)")
ax.plot([], [], "o", color="#2a6fdb", label="Core panel (Table 1)")
ax.plot([], [], "o", color="#9aa5b1", label="Extended panel")
ax.legend(frameon=False, fontsize=8.5)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(out, "fig3.png"), dpi=300); plt.close(fig)

# Figure EC.2: nonparametric eps_hat(u) ----------------------------------------------
npr = R["nonparametric"]
fig, ax = plt.subplots(figsize=(6.2, 3.4))
uu = [d["u"] for d in npr]
ax.errorbar(uu, [d["eps"] for d in npr],
            yerr=[[d["eps"] - d["eps_ci"][0] for d in npr], [d["eps_ci"][1] - d["eps"] for d in npr]],
            fmt="o-", color="#2a6fdb", capsize=3, label="Nonparametric ε̂(u)")
ax.axhline(R["baseline"]["eps"], ls=":", color="gray", label="Gamma fit, 1/(1 + k)")
ax.set_xscale("log"); ax.set_xlabel("Fraction of the test suite executed, u"); ax.set_ylabel("Elasticity")
ax.legend(frameon=False, fontsize=8.5); ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(out, "figEC2.png"), dpi=300); plt.close(fig)
print("figures written to", out)
