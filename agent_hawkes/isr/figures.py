"""Figures 2 and 3 of the ISR manuscript: effect of injected errors on task success and on later agent errors,
for both studies (customer service on tau2-bench; code repair on BugsInPy) and five agents."""
import json
from pathlib import Path
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent; ROOT = HERE.parent
R = {"Customer service (τ²-bench)": json.load(open(ROOT / "inject" / "inject_results.json")),
     "Code repair (BugsInPy)": json.load(open(ROOT / "inject_code" / "code_results.json"))}
LAB = {"llama8b": "Llama-8B", "llama70b": "Llama-70B", "deepseek": "DeepSeek-V3.1", "gpt61terra": "GPT-6.1-terra", "sonnet55": "Sonnet-5.5"}
MODELS = list(LAB); COL = {"single": "#2a6f97", "blame": "#e07a5f"}; NAME = {"single": "transient (503)", "blame": "misleading (not found)"}

fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
for ax, (dom, res) in zip(axes, R.items()):
    for mi, m in enumerate(MODELS):
        s = res[m]["success"]
        for k, off in (("single", -0.15), ("blame", 0.15)):
            d = s.get(k + "_minus_control")
            if not d: continue
            ax.errorbar(mi + off, d["diff"], yerr=[[d["diff"] - d["ci"][0]], [d["ci"][1] - d["diff"]]], fmt="o", ms=4,
                        color=COL[k], label=NAME[k] if mi == 0 else None)
    ax.axhline(0, color="k", lw=0.6); ax.set_xticks(range(len(MODELS))); ax.set_xticklabels([LAB[m] for m in MODELS], fontsize=7, rotation=20)
    ax.set_title(dom, fontsize=9, loc="left")
axes[0].set_ylabel("Change in task success vs control"); axes[0].legend(fontsize=7, frameon=False, loc="lower left")
fig.tight_layout(); fig.savefig(HERE / "fig2_success.png", dpi=200)

fig, axes = plt.subplots(1, 2, figsize=(10, 3.6), sharey=True)
for ax, (dom, res) in zip(axes, R.items()):
    for mi, m in enumerate(MODELS):
        lg = res[m]["lag_logit"]
        if "error" in lg: continue
        for k, kk, off in (("single", "inj1", -0.2), ("blame", "blm1", 0.0), ("own", "err1", 0.2)):
            b, se = lg[kk]["b"], lg[kk]["se"]
            if se > 3: continue  # not identified: too few agent errors after this kind of event
            ax.errorbar(mi + off, b, yerr=1.96 * se, fmt="o", ms=4, color=COL.get(k, "#6c757d"),
                        label=(NAME.get(k, "agent's own error") if mi == 1 else None))
    ax.axhline(0, color="k", lw=0.6); ax.set_xticks(range(len(MODELS))); ax.set_xticklabels([LAB[m] for m in MODELS], fontsize=7, rotation=20)
    ax.set_title(dom, fontsize=9, loc="left")
axes[0].set_ylabel("Log-odds of an agent error on the next call"); axes[0].legend(fontsize=7, frameon=False, loc="upper left")
fig.tight_layout(); fig.savefig(HERE / "fig3_lag.png", dpi=200)
print("saved")
