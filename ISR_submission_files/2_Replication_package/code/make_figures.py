"""Recreate Figures 1, 3 and 4 from the model (Figure 2 needs the release dates; Figure 5 is made by vendor_sensitivity.py).

  python code/make_figures.py        # writes figures/fig1_model.png, fig3_model.png, fig4_model.png
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import monopoly_duopoly as M

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "figures")
os.makedirs(OUT, exist_ok=True)


def fig1():
    v = np.linspace(0, 40, 801)
    mu05, mu07 = M.optimum(0.5, M.THETA, M.Em_static), M.optimum(0.7, M.THETA, M.Em_static)
    def s(mu, R):
        vh = M.CN * (M.RHO + mu) / (1 - R)
        return M.B * mu - np.where(v >= vh, mu * M.CN / M.RHO, (1 - R) * v * mu / (M.RHO * (M.RHO + mu)))
    d = s(mu07, 0.7) - s(mu05, 0.5)
    fig, ax = plt.subplots(figsize=(7, 3.8))
    ax.plot(v, d, color="#1f4e79", lw=2)
    ax.fill_between(v, 0, d, where=d >= 0, color="#9fc29f", alpha=0.4, label="Net gain")
    ax.fill_between(v, 0, d, where=d < 0, color="#e69999", alpha=0.4, label="Net loss")
    ax.axhline(0, color="grey", lw=0.8)
    ax.set_xlabel("Adapter value v (multiple of retraining cost)"); ax.set_ylabel("Change in firm surplus when R rises 0.5 to 0.7")
    ax.legend(); fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig1_model.png"), dpi=200); plt.close(fig)
    return d.max(), v[d.argmax()], d[-1]


def fig3():
    R = np.linspace(0.3, 0.8, 26)
    mono = [M.optimum(r, M.THETA, M.Em_static) for r in R]
    duo = [M.mu_duopoly_symmetric(r) for r in R]
    fig, ax = plt.subplots(figsize=(7, 3.8))
    ax.plot(R, mono, label="Monopoly $\\mu_V$", color="#1f4e79", lw=2); ax.plot(R, duo, label="Symmetric duopoly $\\mu^*$ (H = 10)", color="#c55a11", lw=2)
    ax.set_xlabel("Recovery rate R"); ax.set_ylabel("Equilibrium release intensity"); ax.legend(); fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig3_model.png"), dpi=200); plt.close(fig)


def fig4():
    a = M.asymmetric_check()
    fig, ax = plt.subplots(figsize=(7, 3.8))
    ax.plot(M.V, a["phi"], color="#1f4e79", lw=2); ax.axhline(0.5, color="grey", ls="--", lw=0.8)
    ax.set_ylim(0, 1); ax.set_xlabel("Adapter value v"); ax.set_ylabel("Probability of choosing the frontier owner"); fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig4_model.png"), dpi=200); plt.close(fig)
    return a["phi"]


if __name__ == "__main__":
    pk, vk, plateau = fig1(); fig3(); phi = fig4()
    print(f"Figure 1: peak {pk:.1f} at v = {vk:.1f}; retraining plateau {plateau:.2f}")
    print(f"Figure 4: P(frontier) at v = 0, 1.6, 40: {phi[0]:.2f}, {phi[int(1.6 / 40 * 2000)]:.2f}, {phi[-1]:.2f}")
    print("saved figures to", os.path.abspath(OUT))
