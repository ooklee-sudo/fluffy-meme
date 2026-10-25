"""Generate the figures of the manuscript (and cache the continuous-model profit function).

Run from this directory:  python3 make_figures.py      (about 3-6 minutes; writes ../figures/*.png and fig_cache.npz)
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import norm
import kink_asymptotics as K
import vendor_model as VM

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "figures")
DATA = os.path.join(HERE, "..", "data")
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({"font.family": "serif", "font.size": 9, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.dpi": 130, "savefig.dpi": 300, "legend.frameon": False})
hv = np.vectorize(K.h)
A0 = K.A0

# ------------------------------------------------------------------ Figure 1: adoption set
kap = np.logspace(-0.4, 3.2, 1500)
rho = 1.15
fig, ax = plt.subplots(figsize=(5.6, 3.2))
for A, st in ((0.8, ":"), (0.9, "--"), (1.0, "-"), (1.1, "-.")):
    phi = A * hv(rho * kap) - hv(kap)
    ax.plot(kap, phi, st, color="black", lw=1.2, label=f"$A={A}$")
ax.axhline(0, color="grey", lw=0.6)
ax.set_xscale("log")
ax.set_xlabel(r"Human-technology index $\kappa = a\,b\,f$ (log scale; increases with the cost $f$)")
ax.set_ylabel(r"Adoption gain per unit of $f\,a$:  $\Phi(\kappa)$")
ax.set_ylim(-0.12, 0.12)
ax.legend(loc="lower left", ncol=2, fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig1_adoption_set.png")); plt.close(fig)

# ------------------------------------------------------------------ continuous profit function and cache
cache = os.path.join(OUT, "fig_cache.npz")
As = np.unique(np.round(np.concatenate([np.linspace(0.58, 0.96, 20), np.linspace(0.97, 0.999, 15), [1.0],
                                         np.linspace(1.001, 1.04, 8), np.linspace(1.06, 1.30, 13)]), 4))
if os.path.exists(cache):
    z = np.load(cache); As, Pi, Rho = z["As"], z["Pi"], z["Rho"]
else:
    res = [K.Pi_star(A) for A in As]
    Pi = np.array([r[0] for r in res]); Rho = np.array([r[1] if r[1] is not None else np.nan for r in res])
    np.savez(cache, As=As, Pi=Pi, Rho=Rho)

e1, s1 = K.EY(0.0, np.inf)
M = e1 / (K.B * K.b); P = K.B - K.c0 - K.k
Pi1 = P * M; Dplus = K.B * M


def consumer_surplus(A, rho):
    if not np.isfinite(rho):
        return 0.0
    y = np.linspace(K.m - 8 * K.s, K.m + 12 * K.s, 40001)
    kp = np.exp(y)
    phi = A * hv(rho * kp) - hv(kp)
    w = norm.pdf(y, K.m, K.s) * (y[1] - y[0])
    return float((kp / K.b * np.maximum(phi, 0.0) * w).sum())


CS = np.array([consumer_surplus(A, r) for A, r in zip(As, Rho)])
cost = 0.5 * (As - A0) ** 2
mask = As > A0 + 1e-9
psi = np.where(mask, Pi / cost, 0.0)
psiW = np.where(mask, (Pi + CS) / cost, 0.0)
theta_hat, theta_s = psi.max(), psiW.max()

# ------------------------------------------------------------------ Figure 2: profit function and its kink
deltas = np.logspace(-5, -1, 9)
loss_q = [(Pi1 - K.Pi_star(1 - d)[0]) / d for d in deltas]
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.1))
ax = axs[0]
ax.plot(As, Pi, color="black", lw=1.3)
ax.axvline(1.0, color="grey", ls="--", lw=0.7)
ax.axvline((K.c0 + K.k) / K.B, color="grey", ls=":", lw=0.7)
ax.text((K.c0 + K.k) / K.B + 0.01, 8.5, r"$A_e$", fontsize=8)
ax.text(1.01, 1.0, "parity", fontsize=8)
ax.set_xlabel(r"Vendor reach $A$"); ax.set_ylabel(r"Stage-2 profit $\Pi^*(A)$")
ax = axs[1]
ax.loglog(deltas, loss_q, "o-", color="black", ms=3, lw=1.0, label=r"$[\Pi^*(1)-\Pi^*(1-\delta)]/\delta$")
ax.axhline(Dplus, color="grey", ls="--", lw=0.8)
ax.text(2e-5, Dplus * 1.12, r"right derivative $D^+=E[\ln\kappa;\kappa>1]/b$", fontsize=8)
ax.set_xlabel(r"Shortfall $\delta = 1-A$"); ax.set_ylabel("Left difference quotient")
ax.legend(loc="upper right", fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig2_profit_kink.png")); plt.close(fig)

# ------------------------------------------------------------------ Figure 3: cost efficiency and reach choice
thetas = np.linspace(10, 80, 281)
def choose(profile, th):
    J = profile - th * cost
    i = J.argmax()
    return As[i] if J[i] > 1e-9 else A0
priv = np.array([choose(Pi, t) for t in thetas]); soc = np.array([choose(Pi + CS, t) for t in thetas])
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.1))
ax = axs[0]
ax.plot(As[mask], psi[mask], color="black", lw=1.3, label=r"vendor: $\Pi^*(A)/c(A)$")
ax.plot(As[mask], psiW[mask], color="black", lw=1.0, ls="--", label=r"society: $(\Pi^*+CS)/c(A)$")
ax.axhline(theta_hat, color="grey", lw=0.5); ax.axhline(theta_s, color="grey", lw=0.5)
ax.set_xlabel(r"Reach $A$"); ax.set_ylabel(r"Cost efficiency ($c(A)=(A-A_0)^2/2$)")
ax.legend(loc="lower right", fontsize=7.5)
ax = axs[1]
ax.step(thetas, priv, where="post", color="black", lw=1.3, label="vendor")
ax.step(thetas, soc, where="post", color="black", lw=1.0, ls="--", label="social planner")
ax.axvline(theta_hat, color="grey", ls=":", lw=0.7)
ax.set_xlabel(r"Cost of reach $\theta$"); ax.set_ylabel(r"Chosen reach $A^*(\theta)$")
ax.legend(loc="center right", fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig3_reach_choice.png")); plt.close(fig)

# ------------------------------------------------------------------ Figure 4: scaling of stakes
iv9 = VM.interval(0.33, A=0.9); flo, fhi = iv9[0], iv9[1]
mu, sg = VM.MU, VM.SIG
lam = np.logspace(-1.6, 1.6, 400)
share9 = norm.cdf((np.log(fhi / lam) - mu) / sg) - norm.cdf((np.log(flo / lam) - mu) / sg)
iv1 = VM.interval(0.79, A=1.0); flo1 = iv1[0]
share1 = 1 - norm.cdf((np.log(flo1 / lam) - mu) / sg)
lam_star = np.sqrt(flo * fhi) / np.exp(mu)
fig, ax = plt.subplots(figsize=(5.2, 3.0))
ax.semilogx(lam, share9, color="black", lw=1.3, label=r"$A=0.9$: bounded adoption window")
ax.semilogx(lam, share1, color="black", lw=1.0, ls="--", label=r"$A=1.0$: half-line")
ax.axvline(lam_star, color="grey", ls=":", lw=0.7); ax.text(lam_star * 1.05, 0.05, r"$\lambda^*$", fontsize=8)
ax.set_xlabel(r"Multiplier $\lambda$ on the cost of undetected faults"); ax.set_ylabel("Share of firms adopting (price fixed)")
ax.legend(loc="lower right", bbox_to_anchor=(1.0, 0.18), fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig4_stakes_scaling.png")); plt.close(fig)

# ------------------------------------------------------------------ Figure 5: public-data evidence
jira = pd.read_csv(os.path.join(DATA, "jira_nhpp_results.csv"))
half = np.log(2) / jira.b_GO_per30d
fig, axs = plt.subplots(1, 3, figsize=(7.4, 2.7))
ax = axs[0]
labs = ["<15 min", "15 min-1 h", "1-4 h", ">4 h"]; rate = [39.9, 25.2, 4.9, 0.0]; n = [193, 258, 41, 3]
ax.bar(range(4), rate, color="0.35")
for i, (r, c) in enumerate(zip(rate, n)):
    ax.text(i, r + 1, f"n={c}", ha="center", fontsize=7)
ax.set_xticks(range(4)); ax.set_xticklabels(labs, fontsize=7, rotation=20)
ax.set_ylabel("Share resolved by the agent (%)"); ax.set_xlabel("Human fix time (label)")
ax = axs[1]
kk = np.arange(1, 13); cov = [.125, .174, .202, .218, .231, .242, .250, .256, .261, .266, .271, .274]
ax.plot(kk, cov, "ko", ms=3)
ax.plot(kk, 0.263 * (1 - np.exp(-0.513 * kk)), "-", color="grey", lw=1.0, label="exponential (GO)")
ax.plot(kk, 0.061 * np.log1p(7.898 * kk), "--", color="black", lw=1.0, label="logarithmic (MO)")
ax.set_xlabel("Attempts $k$"); ax.set_ylabel("Share of instances solved"); ax.legend(fontsize=7)
ax = axs[2]
ax.hist(np.clip(half, 0, 6), bins=40, color="0.35")
ax.axvline(np.log(2) / jira.b_GO_per30d.median(), color="black", ls="--", lw=0.8)
ax.set_xlabel("Half-life (months; last bin: 6+)"); ax.set_ylabel("Releases")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig5_public_evidence.png")); plt.close(fig)

print(f"theta_hat (vendor)  = {theta_hat:.2f}   [closed form 2*P*M/(1-A0)^2 = {2 * Pi1 / (1 - A0) ** 2:.2f}]")
print(f"theta_s (planner)   = {theta_s:.2f}")
print(f"lambda* (A=0.9)     = {lam_star:.3f}")
print("figures written to", os.path.abspath(OUT))
