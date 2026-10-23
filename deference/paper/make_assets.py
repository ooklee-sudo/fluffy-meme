"""Builds the LaTeX table bodies and figures of the manuscript from the result CSVs (no number is typed by hand)."""
import json, os
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = os.path.join(os.path.dirname(__file__), "..", "results"); OUT = os.path.dirname(__file__)
M = pd.read_csv(f"{R}/primary/model_metrics.csv")
D = json.load(open(f"{R}/primary/decisions.json"))
est = M.pivot(index="model", columns="metric", values="est"); lo = M.pivot(index="model", columns="metric", values="lo"); hi = M.pivot(index="model", columns="metric", values="hi")
ORDER = ["Qwen2.5-7B", "Qwen2.5-72B", "Llama3.1-8B", "Llama3.1-70B", "Gemma3-4B", "Gemma3-12B", "Gemma3-27B", "Ministral-3B", "Ministral-8B", "Ministral-14B",
         "Haiku4.5", "Sonnet5.5", "Opus5.5", "Fable5.1"]
NAME = {m: m.replace("Qwen2.5-", "Qwen2.5 ").replace("Llama3.1-", "Llama-3.1 ").replace("Gemma3-", "Gemma-3 ").replace("Ministral-", "Ministral ")
        .replace("Haiku4.5", "Haiku 4.5").replace("Sonnet5.5", "Sonnet 5.5").replace("Opus5.5", "Opus 5.5").replace("Fable5.1", "Fable 5.1") for m in ORDER}
CODE = {"evidence-weighing-consistent": "W", "deference-consistent": "D", "mixed or unclassified": "M"}
f2 = lambda x: "--" if not np.isfinite(x) else f"{x:.2f}"
ci = lambda m, k: f"[{f2(lo.loc[m, k])}, {f2(hi.loc[m, k])}]"

rows = []
for m in ORDER:
    e = est.loc[m]
    rows.append(f"{NAME[m]} & {f2(e.a)} & {f2(e.nu)} & {f2(e.rho)} & {f2(e.f_star)} & {f2(e.s_star)} {ci(m,'s_star')} & {f2(e.removed) if e.f_star > .02 else '--'} \\\\")
open(f"{OUT}/tab_main.tex", "w").write("\n".join(rows) + "\n")

rows = []
for m in ORDER:
    e = est.loc[m]
    rows.append(f"{NAME[m]} & {e.slope:+.2f} & {e.acc_slope:+.2f} & {e.disclaimer_effect:+.2f} & {CODE[D['H3'][m]]} \\\\")
open(f"{OUT}/tab_mechanism.tex", "w").write("\n".join(rows) + "\n")

# reasoning on/off
dl = pd.read_csv(f"{R}/extra/delta_onoff.csv"); di = pd.read_csv(f"{R}/extra/delta_intersection.csv"); cov = pd.read_csv(f"{R}/extra/coverage.csv").set_index("model")
rows = []
for b in ["Haiku4.5", "Qwen3.6-27B", "Qwen3.8-27B"]:
    g = dl[dl.model == b].set_index("metric"); gi = di[di.model == b].set_index("metric")
    lab = b.replace("Haiku4.5", "Haiku 4.5").replace("Qwen", "Qwen")
    tr = cov.loc[f"{b}|on", "truncated"]
    rows.append(f"{lab} & {int(g['items'].iloc[0])} & {g.loc['a','off']:.2f} / {g.loc['a','on']:.2f} & {g.loc['s_star','off']:.2f} / {g.loc['s_star','on']:.2f} & "
                f"{g.loc['s_star','delta']:+.2f} [{g.loc['s_star','lo']:+.2f}, {g.loc['s_star','hi']:+.2f}] & {int(gi['items'].iloc[0])} & "
                f"{gi.loc['s_star','delta']:+.2f} [{gi.loc['s_star','lo']:+.2f}, {gi.loc['s_star','hi']:+.2f}] & {tr*100:.1f}\\% \\\\")
open(f"{OUT}/tab_reasoning.tex", "w").write("\n".join(rows) + "\n")

# Fig 1: conventional deference f(e*) versus corrected s*
fig, ax = plt.subplots(figsize=(3.4, 3.1)); x = np.arange(len(ORDER)); w = .38
ax.bar(x - w/2, [est.loc[m, "f_star"] for m in ORDER], w, label=r"$f(e^*)$ (conventional)", color="#9aa5b1")
ax.bar(x + w/2, [est.loc[m, "s_star"] for m in ORDER], w, yerr=[[est.loc[m, "s_star"] - lo.loc[m, "s_star"] for m in ORDER], [hi.loc[m, "s_star"] - est.loc[m, "s_star"] for m in ORDER]],
       error_kw=dict(lw=.6, capsize=1), label=r"$s^*$ (baseline-corrected)", color="#1f4e79")
ax.set_xticks(x); ax.set_xticklabels([NAME[m] for m in ORDER], rotation=75, ha="right", fontsize=5.5); ax.set_ylabel("Rate of stance-endorsed answer", fontsize=7)
ax.tick_params(axis="y", labelsize=6); ax.legend(fontsize=6, frameon=False, loc="upper right"); ax.set_ylim(0, 1.05)
fig.tight_layout(); fig.savefig(f"{OUT}/figs/fig_decomp.pdf"); plt.close(fig)

# Fig 2: s* with reasoning off and on
fig, ax = plt.subplots(figsize=(3.4, 2.3)); C = pd.read_csv(f"{R}/extra/condition_metrics.csv"); c = C[C.metric == "s_star"].set_index("condition")
bases = ["Haiku4.5", "Qwen3.6-27B", "Qwen3.8-27B"]; x = np.arange(3)
for j, (mode, col) in enumerate((("off", "#9aa5b1"), ("on", "#1f4e79"))):
    v = [c.loc[f"{b}|{mode}"] for b in bases]
    ax.bar(x + (j - .5) * .38, [r.est for r in v], .38, yerr=[[r.est - r.lo for r in v], [r.hi - r.est for r in v]], error_kw=dict(lw=.6, capsize=1.5), color=col, label=f"reasoning {mode}")
ax.set_xticks(x); ax.set_xticklabels(["Haiku 4.5", "Qwen3.6-27B", "Qwen3.8-27B"], fontsize=7); ax.set_ylabel(r"$s^*$", fontsize=8); ax.tick_params(axis="y", labelsize=6)
ax.legend(fontsize=6, frameon=False); fig.tight_layout(); fig.savefig(f"{OUT}/figs/fig_reasoning.pdf"); plt.close(fig)
print("ok"); print(open(f"{OUT}/tab_reasoning.tex").read())
