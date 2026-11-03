import json, statistics as st, collections, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
plt.rcParams.update({"font.size": 9, "font.family": "serif"})
# ---- Figure 1: retention strength vs share of superseded facts (70M, 3 seeds)
rows = [r for f in ("resA.json", "resB.json", "resC.json") for r in json.load(open("results/../" + f))] if False else []
import glob
rows = []
for f in ("resA.json", "resB.json", "resC.json"):
    try: rows += json.load(open(f))
    except Exception: pass
un = collections.defaultdict(list)
for r in rows:
    if r["q"] is None: un[(r["rho"], r["lam"])].append(r["currency"])
fig, ax = plt.subplots(figsize=(4.4, 3.2))
for lam, m, ls in ((0.0, "o", "-"), (1.0, "s", "--"), (10.0, "^", ":")):
    xs = [r for r in (0.1, 0.3, 0.5, 0.7, 0.9) if (r, lam) in un]
    ax.plot(xs, [st.mean(un[(r, lam)]) for r in xs], marker=m, ls=ls, color="black", label=f"KL weight {lam:g}")
ax.plot([0.1, 0.9], [0.9, 0.1], color="gray", lw=0.8, label="1 − ρ")
ax.set_xlabel("Share of superseded facts (ρ)"); ax.set_ylabel("Currency"); ax.legend(frameon=False, fontsize=8); ax.set_ylim(0, 1.02)
plt.tight_layout(); plt.savefig("paper/fig1_retention.png", dpi=300); plt.close()
# ---- Figure 2: stream-scoped retention vs matching accuracy (7B, 3 seeds)
A = json.load(open("results/autoscope_qwen7b.json"))
fig, axs = plt.subplots(1, 2, figsize=(6.6, 3.0), sharey=True)
for ax, rho in zip(axs, (0.3, 0.7)):
    ms = (0.6, 0.8, 1.0); mean, lo, hi = [], [], []
    for m in ms:
        v = [x["currency"] for x in A if x["rho"] == rho and x["method"] == "ss" and x.get("match", 1.0) == m]
        mean.append(st.mean(v)); lo.append(min(v)); hi.append(max(v))
    ax.errorbar(ms, mean, yerr=[[a - b for a, b in zip(mean, lo)], [b - a for a, b in zip(mean, hi)]], marker="o", color="black", capsize=3, label="Stream-scoped retention")
    ax.plot(ms, [(1 - rho) + rho * m for m in ms], ls="--", color="gray", label="(1 − ρ) + ρm")
    best = max(st.mean([x["currency"] for x in A if x["rho"] == rho and x["method"] == meth and x["lam"] == lam]) for meth, lam in (("none", 0.0), ("unscoped", 1.0), ("unscoped", 10.0)))
    ax.axhline(best, ls=":", color="black", lw=1, label="Best unscoped")
    ax.set_title(f"ρ = {rho}"); ax.set_xlabel("Matching accuracy (m)"); ax.set_ylim(0.5, 1.03)
axs[0].set_ylabel("Currency"); axs[0].legend(frameon=False, fontsize=7, loc="lower right")
plt.tight_layout(); plt.savefig("paper/fig2_matching.png", dpi=300); plt.close()
# ---- Figure 3: real amendments, share of listed provisions kA (7B, 3 seeds)
R = json.load(open("results/reallaw_v2.json"))
g = collections.defaultdict(list)
for r in R:
    if r["kdep"] == 0 and (r["method"], r["lam"]) in (("none", 0.0), ("dep", 10.0), ("ss", 10.0)): g[(r["method"], r["kA"])].append(r)
fig, axs = plt.subplots(1, 2, figsize=(6.6, 3.0))
sty = {"none": ("o", "-", "Fine-tuning on the listed amendments"), "dep": ("s", "--", "Dependency-scoped retention"), "ss": ("^", ":", "Stream-scoped retention")}
for m in ("none", "dep", "ss"):
    ks = [k for k in (0.1, 0.25, 0.5, 0.75) if (m, k) in g]
    for ax, key in zip(axs, ("unlisted_AB", "currency_all")):
        ax.plot(ks, [st.mean([x[key] for x in g[(m, k)]]) for k in ks], marker=sty[m][0], ls=sty[m][1], color="black", label=sty[m][2])
axs[0].set_title("Provisions not in the update", fontsize=9); axs[1].set_title("All amended provisions", fontsize=9)
axs[0].set_ylabel("Share answered with the new value")
for ax in axs: ax.set_xlabel("Share of provisions in the update (k)"); ax.set_ylim(-0.02, 1.02)
axs[0].legend(frameon=False, fontsize=7, loc="center right")
plt.tight_layout(); plt.savefig("paper/fig3_reallaw.png", dpi=300); plt.close()
print("figures done")
