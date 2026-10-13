"""Yelp LLM content analysis exactly as in ANALYSIS_PLAN_ADDENDUM_LLM.md. Usage: python analysis_yelp_llm.py   (run from misq_note/covid/llm)"""
import glob, json, re, warnings
import numpy as np, pandas as pd, pyfixest as pf
from sklearn.metrics import cohen_kappa_score
from scipy.stats import spearmanr
warnings.filterwarnings("ignore")
COLS = ["rid", "overall", "safety", "takeout", "service", "price", "food", "space"]; ASP = COLS[2:]
PAT = re.compile(r"\d+,(neg|neu|pos)(,(0|-1|1|2)){6}")
res = {}
def load(pat, nrows_expected=None):
    rows = []
    for f in sorted(glob.glob(pat)):
        L = [l.strip() for l in open(f).read().splitlines() if l.strip()]
        bad = [l for l in L if not PAT.fullmatch(l)]
        if bad: res.setdefault("format_problems", []).append((f, len(bad)))
        rows += [dict(zip(COLS, l.split(","))) for l in L if PAT.fullmatch(l)]
    d = pd.DataFrame(rows); d["rid"] = d.rid.astype(int)
    for a in ASP: d[a] = d[a].astype(int)
    return d.drop_duplicates("rid")
H = load("out/H_*.csv"); A = load("out/A_*.csv"); meta = pd.read_csv("sample_meta.csv")
res["coded_H"] = int(len(H)); res["sample"] = int(len(meta)); res["coded_A"] = int(len(A))
S = meta.merge(H, on="rid", how="inner"); res["analysis_n"] = int(len(S))
# ---- validation: coder A vs coder H on the 400 shared reviews
V = A.merge(H, on="rid", suffixes=("_A", "_H")); res["n_val_pairs"] = int(len(V))
F = ["overall"] + ASP
res["kappa_A_vs_H"] = {f: float(cohen_kappa_score(V[f + "_A"].astype(str), V[f + "_H"].astype(str))) for f in F}
res["kappa_mention_A_vs_H"] = {a: float(cohen_kappa_score(V[a + "_A"] != 0, V[a + "_H"] != 0)) for a in ASP}
res["agree_A_vs_H"] = {f: float((V[f + "_A"].astype(str) == V[f + "_H"].astype(str)).mean()) for f in F}
num = {"neg": -1, "neu": 0, "pos": 1}; st = meta.set_index("rid").stars
res["spearman_H_vs_stars_all"] = float(spearmanr(S.overall.map(num), S.stars)[0])
low = [a for a in ("safety", "takeout") if res["kappa_mention_A_vs_H"][a] < 0.60]; res["primary_aspects_excluded_for_kappa<0.60"] = low
# regex proxies vs LLM mention on the whole sample
for a, flag in (("takeout", "tk"), ("safety", "cv")):
    res[f"regex_vs_LLM {a}"] = dict(kappa=float(cohen_kappa_score(S[flag] == 1, S[a] != 0)), regex_share=float((S[flag] == 1).mean()), llm_share=float((S[a] != 0).mean()))
# ---- outcomes
S["safety_m"] = (S.safety != 0).astype(int); S["takeout_m"] = (S.takeout != 0).astype(int); S["neg"] = (S.overall == "neg").astype(int)
S["post"] = (S.period == "Post").astype(int); S["Low"] = (S.tercile == "Low").astype(int); S["Mid"] = (S.tercile == "Mid").astype(int)
S["PostLow"] = S.post * S.Low; S["PostMid"] = S.post * S.Mid
for o in ("safety_m", "takeout_m", "neg"):
    res[f"mean {o} by tercile x period"] = {f"{t}_{p}": float(S[(S.tercile == t) & (S.period == p)][o].mean()) for t in ("Low", "Mid", "High") for p in ("Pre", "Post")}
def tid(m, k): return dict(b=float(m.coef()[k]), se=float(m.se()[k]), p=float(m.pvalue()[k]))
# L1: pooled Post effect, state FE, clustered by restaurant
pv = {}
for o, nm in (("safety_m", "L1-safety"), ("takeout_m", "L1-takeout")):
    m = pf.feols(f"{o} ~ post + Low + Mid | state", data=S, vcov={"CRV1": "business_id"}); res[nm] = tid(m, "post"); pv[nm] = res[nm]["p"] / 2 if res[nm]["b"] > 0 else 1 - res[nm]["p"] / 2
# L2: change in overall negative share, 90% CI vs +-3 pp
m = pf.feols("neg ~ post + Low + Mid | state", data=S, vcov={"CRV1": "business_id"}); b, se = float(m.coef()["post"]), float(m.se()["post"])
res["L2 negative share change"] = dict(b=b, se=se, ci90=[b - 1.645 * se, b + 1.645 * se], within_3pp=bool(abs(b) + 1.645 * se < 0.03))
# L3/L4: Post x tercile interactions with High as the reference
for o, nm in (("safety_m", "L3-safety"), ("takeout_m", "L4-takeout")):
    m = pf.feols(f"{o} ~ post + PostLow + PostMid + Low + Mid | state", data=S, vcov={"CRV1": "business_id"}); res[nm + " PostLow-vs-High"] = tid(m, "PostLow"); res[nm + " PostMid-vs-High"] = tid(m, "PostMid"); res[nm + " Post (High)"] = tid(m, "post")
    p = res[nm + " PostLow-vs-High"]; pv[nm] = (p["p"] / 2 if p["b"] > 0 else 1 - p["p"] / 2) if nm.startswith("L3") else p["p"]
order = sorted(pv, key=pv.get); run = 0.0; holm = {}
for i, k in enumerate(order): run = max(run, min(1.0, pv[k] * (len(pv) - i))); holm[k] = dict(p_used=pv[k], holm_p=run)
res["holm_primary"] = holm
# checks: drop Alberta
Sx = S[S.state != "AB"]
for o, nm in (("safety_m", "L3-safety"), ("takeout_m", "L4-takeout")):
    m = pf.feols(f"{o} ~ post + PostLow + PostMid + Low + Mid | state", data=Sx, vcov={"CRV1": "business_id"}); res[f"excl Alberta {nm} PostLow-vs-High"] = tid(m, "PostLow")
json.dump(res, open("results_yelp_llm.json", "w"), indent=1)
for k, v in res.items():
    if isinstance(v, dict) and "b" in v and "se" in v and "ci90" not in v: print(k, {a: round(b_, 4) for a, b_ in v.items()})
    elif isinstance(v, dict): print(k, {a: (round(b_, 4) if isinstance(b_, float) else b_) for a, b_ in v.items()})
    else: print(k, v)
