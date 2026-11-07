"""Reproduce the statistics reported in the manuscript that analyze.py does not print.

  python paper_stats.py <data_dir>

Covers: Supplementary Table S3 (linear probability models, Studies 1-2), the logistic and
cluster-robust checks of the loss effect (Section 5.2), Study 3b Fisher test (Section 5.4),
help-seeking in Study 4 (Section 5.5), and the Study 5 hazard models (Section 5.6).
"""
import json
import pathlib
import sys
import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy.stats import fisher_exact

import analyze_selfgen

warnings.filterwarnings("ignore")
D = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "results")
FAILS = {"S4": 0, "N": 0, "NI": 0, "F2": 2, "F2a": 2, "F4": 4, "F8": 8, "F8a": 8}
NAMED = {"NI", "F2", "F4", "F8"}


def load(*names):
    rows = []
    for n in names:
        for line in open(D / n):
            r = json.loads(line)
            if "terminal" in r and not r["model"].startswith("scripted:"):
                rows.append(r)
    d = pd.DataFrame(rows)
    for c in ["unsafe", "honest_exit", "asked_operator"]:
        d[c] = d[c].astype(int)
    d["deadline"] = (d.scarcity == "deadline").astype(int)
    d["fails"] = d.history.map(FAILS)
    d["loss"] = (d.fails > 0).astype(int)
    d["info"] = d.history.isin(NAMED).astype(int)
    d["success"] = (d.history == "S4").astype(int)
    d["full_rec"] = (d.record == "full").astype(int)
    return d


def row(label, m, term):
    p = m.pvalues[term]
    ps = "< .001" if p < 0.001 else f"{p:.3f}"
    print(f"| {label} | {m.params[term]:.3f} | {m.bse[term]:.3f} | {ps} | {int(m.nobs)} |")


def lpm(f, data):
    return smf.ols(f, data).fit(cov_type="HC1")


def fisher(a, b, col="unsafe"):
    return fisher_exact([[a[col].sum(), len(a) - a[col].sum()], [b[col].sum(), len(b) - b[col].sum()]])[1]


print("## Table S3: linear probability models (model fixed effects, HC1)\n")
print("| Model and term | b | SE | p | n |\n| --- | --- | --- | --- | --- |")
d = load("study1_lowcost.jsonl", "info_control_lowcost.jsonl")
full = d[d.record == "full"]
h1 = full[full.history.isin(["N", "F2", "F4", "F8"])]
row("(1) H1: failures", lpm("unsafe ~ fails + deadline + C(model)", h1), "fails")
h1d = h1.assign(F2=(h1.history == "F2").astype(int), F4=(h1.history == "F4").astype(int), F8=(h1.history == "F8").astype(int))
m = lpm("unsafe ~ F2 + F4 + F8 + deadline + C(model)", h1d)
for t in ["F2", "F4", "F8"]:
    row(f"(2) H1: {t} vs N", m, t)
row("(3) H2: S4 vs N", lpm("unsafe ~ success + deadline + C(model)", full[full.history.isin(["S4", "N"])]), "success")
m = lpm("unsafe ~ fails * deadline + C(model)", h1)
for t in ["fails", "deadline", "fails:deadline"]:
    row(f"(4) H3: {t}", m, t)
h4 = d[d.history.isin(["F4", "F8"])]
row("(5) H4: full vs summary", lpm("unsafe ~ full_rec + C(history) + deadline + C(model)", h4), "full_rec")
x = full[full.history.isin(["N", "NI", "F2a", "F2", "F8a", "F8"])]
m = lpm("unsafe ~ loss * info + deadline + C(model)", x)
for t in ["loss", "info", "loss:info", "deadline"]:
    row(f"(6) Loss x information: {t}", m, t)
m = lpm("honest_exit ~ loss * info + deadline + C(model)", x)
for t in ["loss", "info", "loss:info"]:
    row(f"(7) Honest exit: {t}", m, t)
for k in ["2", "8"]:
    y = x[x.history.isin(["N", "NI", f"F{k}a", f"F{k}"])]
    m = lpm("unsafe ~ loss * info + deadline + C(model)", y)
    for t in ["loss", "info", "loss:info"]:
        row(f"{k} failures only: {t}", m, t)

print("\n## Section 5.1-5.2: robustness checks\n")
act = h1.groupby("model").unsafe.sum()
lg = smf.logit("unsafe ~ fails + deadline + C(model)", h1[h1.model.isin(act[act > 0].index)]).fit(disp=0)
print(f"H1 logit (models with any gaming): b = {lg.params['fails']:.3f}, p = {lg.pvalues['fails']:.3f}")
act = x.groupby("model").unsafe.sum()
xs = x[x.model.isin(act[act > 0].index)]
lg = smf.logit("unsafe ~ loss * info + deadline + C(model)", xs).fit(disp=0)
print(f"Loss logit ({xs.model.nunique()} models): b = {lg.params['loss']:.2f}, SE = {lg.bse['loss']:.2f}, "
      f"OR = {np.exp(lg.params['loss']):.1f}, p = {lg.pvalues['loss']:.4f}; info p = {lg.pvalues['info']:.3f}")
mc = smf.ols("unsafe ~ loss * info + deadline + C(model)", x).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(x.model)[0]})
print(f"Loss, SE clustered by model: b = {mc.params['loss']:.3f}, p = {mc.pvalues['loss']:.3f}")

print("\n## Section 5.4: Study 3b, grok-4.7\n")
f3 = load("frontier_hidden.jsonl")
g = f3[f3.model == "x-ai/grok-4.7"]
print(f"grok-4.7 gaming episodes: {g.unsafe.sum()}/{len(g)}; N vs F8a Fisher p = {fisher(g[g.history == 'N'], g[g.history == 'F8a']):.3f}")

print("\n## Section 5.5: Study 4 (operations task)\n")
s4 = load("study4_ops_lowcost.jsonl")
print(f"episodes = {len(s4)}, gaming = {s4.unsafe.sum()}, honest exits = {s4.honest_exit.sum()}")
y = s4[s4.history.isin(["N", "NI", "F2", "F2a", "F8", "F8a"])]
m = lpm("asked_operator ~ loss + C(model)", y)
print(f"Asked operator ~ loss: b = {m.params['loss']:.3f}, SE = {m.bse['loss']:.3f}, p = {m.pvalues['loss']:.3f}")
print(f"N vs F8 asked, Fisher p = {fisher(s4[s4.history == 'F8'], s4[s4.history == 'N'], 'asked_operator'):.3f}")
print("Asked operator by history (%):", (s4.groupby("history").asked_operator.mean() * 100).round(1).to_dict())

print("\n## Section 5.6: Study 5 (self-generated failure)\n")
att, eps = analyze_selfgen.attempts(D / "study5_selfgen_lowcost.jsonl")
m = smf.ols("gaming ~ own_fail + C(model)", att).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(att.episode)[0]})
print(f"Hazard LPM: b = {m.params['own_fail']:.4f}, SE = {m.bse['own_fail']:.4f}, p = {m.pvalues['own_fail']:.3f}, attempts = {int(m.nobs)}")
act = att.groupby("model").gaming.sum()
aa = att[att.model.isin(act[act > 0].index)]
lg = smf.logit("gaming ~ np.log(own_fail) + C(model)", aa).fit(disp=0, cov_type="cluster", cov_kwds={"groups": pd.factorize(aa.episode)[0]})
k = "np.log(own_fail)"
print(f"Hazard logit ({aa.model.nunique()} models): b = {lg.params[k]:.2f}, SE = {lg.bse[k]:.2f}, p = {lg.pvalues[k]:.3f}, "
      f"OR per doubling = {np.exp(lg.params[k] * np.log(2)):.2f}")
att["bin"] = pd.cut(att.own_fail, [0, 1, 2, 3, 1000], labels=["1", "2", "3", "4+"])
print("Hazard by own failures, all models (%):", (att.groupby("bin").gaming.mean() * 100).round(1).to_dict())
aa = aa.assign(bin=att.bin)
print("Models with any gaming attempt:", sorted(aa.model.unique()))
print("Hazard by own failures, those models (attempts, %):",
      {k: (int(v.size), round(v.mean() * 100, 1)) for k, v in aa.groupby("bin").gaming})
ids = set(att[att.gaming == 1].episode)
s5 = {json.loads(l)["id"]: json.loads(l) for l in open(D / "study5_selfgen_lowcost.jsonl")}
ended = sum(bool(s5[i]["unsafe"]) for i in ids)
print(f"Episodes with a gaming attempt: {len(ids)}; still gamed at the end: {ended}; reverted: {len(ids) - ended} "
      f"(of which reported blocked: {sum(s5[i]['terminal'] == 'report_blocked' and not s5[i]['unsafe'] for i in ids)})")
