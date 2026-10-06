"""Figures for the paper from runs/summary.json."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from stats_model import fit_negbin

S = json.load(open("runs/summary.json"))
NAMES = {"qwen05": "Qwen2.5-0.5B", "smol360": "SmolLM2-360M", "qwen15": "Qwen2.5-1.5B"}
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})

# Fig 1: daily counts without guardrails, steady vs bursty traffic (Qwen 0.5B)
fig, ax = plt.subplots(1, 2, figsize=(9, 3.3), sharey=True)
for a, key, title in ((ax[0], "sla500", "NHPP traffic (no burstiness)"), (ax[1], "burst", "Cox traffic (daily rate CV = 0.3)")):
    res = S["qwen05"][key]["poisson_checks"]["none"]
    dc = np.array(res["daily_counts"]); lam = res["lambda_per_day"]
    ks = np.arange(int(dc.min()) - 10, int(dc.max()) + 11)
    a.hist(dc, bins=np.arange(ks.min() - .5, ks.max() + 1.5, 3), density=True, color="#9ecae1", label="observed daily counts")
    a.plot(ks, stats.poisson.pmf(ks, lam), color="#d62728", lw=1.8, label="Poisson fit")
    m, r = fit_negbin(dc)
    if np.isfinite(r) and r < 500:
        a.plot(ks, stats.nbinom.pmf(ks, r, r / (r + m)), color="#2ca02c", lw=1.8, ls="--", label="negative-binomial fit")
    kp = res["k_star_poisson"]; a.axvline(kp, color="k", ls=":", lw=1)
    a.set_title(f"{title}\nPoisson k* = {kp} exceeded on {100 * res['p_exceed_k_star_observed']:.0f}% of days", fontsize=9)
    a.set_xlabel("critical hallucinations per day")
ax[0].set_ylabel("density"); ax[0].legend(fontsize=7, frameon=False)
fig.tight_layout(); fig.savefig("runs/fig_burst.png", dpi=200)

# Fig 2: independence formula vs observed residual share (L2+L3), and k* with CIs
fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
x = np.arange(3); w = 0.26
for i, (lab, key, col) in enumerate((("independence formula", "independent", "#bdbdbd"), ("observed, no routing", "observed_no_routing", "#6baed6"), ("observed, with routing", "observed_with_routing", "#2171b5"))):
    ax[0].bar(x + (i - 1) * w, [100 * S[r]["residual_share"]["L2+L3"][key] for r in NAMES], w, label=lab, color=col)
ax[0].set_xticks(x); ax[0].set_xticklabels(NAMES.values()); ax[0].set_ylabel("hallucinations passing L2+L3 (%)")
ax[0].set_title("Independence formula understates residual risk", fontsize=9); ax[0].legend(fontsize=7, frameon=False)
cfgs = ["none", "L2", "L2+L3", "L1+L2+L3"]
for j, r in enumerate(NAMES):
    ci = S[r]["sla500"]["bootstrap_ci"]; rows = {c["config"]: c for c in S[r]["sla500"]["configs"]}
    for i, c in enumerate(cfgs):
        k = rows[c]["k_star"]; lo, hi = ci[c]["k"]
        ax[1].errorbar(i + (j - 1) * 0.2, k, yerr=[[k - lo], [hi - k]], fmt="o", color=f"C{j}", capsize=2, label=list(NAMES.values())[j] if i == 0 else None)
ax[1].set_xticks(range(len(cfgs))); ax[1].set_xticklabels(cfgs); ax[1].set_yscale("log"); ax[1].set_ylabel("capacity k* (log scale)")
ax[1].set_title("Required capacity by cascade (95% bootstrap CI)", fontsize=9); ax[1].legend(fontsize=7, frameon=False)
fig.tight_layout(); fig.savefig("runs/fig_cascade.png", dpi=200)
print("ok")
