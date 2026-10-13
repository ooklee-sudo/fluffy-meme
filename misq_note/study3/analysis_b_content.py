"""Study 3: LLM-coded content outcomes (H3) and LLM-coding validation, as pre-specified in ANALYSIS_PLAN.md.
Usage: python analysis_b_content.py   (reads sample_meta.csv, out/H_*.csv, out/A_*.csv, results_b_volume.json, results_b_reviewlevel_checks.json)"""
import glob, json, warnings
import numpy as np, pandas as pd, pyfixest as pf
from scipy.stats import spearmanr
from sklearn.metrics import cohen_kappa_score
warnings.filterwarnings("ignore")
COLS = ["rid", "overall", "defect", "price", "durability", "performance", "fit", "ease", "design", "service"]
load = lambda pat: pd.concat([pd.read_csv(f, header=None, names=COLS) for f in sorted(glob.glob(pat))]).drop_duplicates("rid")
H = load("out/H_*.csv"); A = load("out/A_*.csv"); meta = pd.read_csv("sample_meta.csv")
res = {"coded_H": int(len(H)), "sample": int(len(meta)), "coded_A": int(len(A))}
S = meta.merge(H, on="rid", how="inner"); res["analysis_n"] = int(len(S))
S["q"] = pd.to_datetime(S.ts, unit="ms").dt.to_period("Q").astype(str)
S["neg"] = (S.overall == "neg").astype(int); S["perfpos"] = (S.performance == 1).astype(int); S["lenlog"] = np.log1p(S["len"]); S["hvlog"] = np.log1p(S.hv); S["vp"] = S.vp.astype(int)
S["tp"] = S.treated * S.post; S["pid"] = pd.factorize(S.pa)[0]
def tid(m): return dict(b=float(m.coef()["tp"]), se=float(m.se()["tp"]), p=float(m.pvalue()["tp"]))
for out in ("defect", "neg", "perfpos", "rating", "lenlog", "vp", "hvlog"):
    res[f"DiD {out}"] = tid(pf.feols(f"{out} ~ tp | pa + q", data=S, vcov={"CRV1": "pa"}))
# raw means by cell for context
res["cell_means"] = {f"treated{t}_post{p}": {o: float(S[(S.treated == t) & (S.post == p)][o].mean()) for o in ("defect", "neg", "perfpos", "rating")} for t in (0, 1) for p in (0, 1)}
# Holm across the five primary tests: H1a volume, H2 rating (review-level, continuous), H3 defect, neg, perfpos
vol = json.load(open("results_b_volume.json")); chk = json.load(open("results_b_reviewlevel_checks.json"))
pv = {"H1a volume": list(vol["H1a all reviews (continuous E, per +10pp)"].values())[0]["p"], "H2 rating (continuous E)": chk["actual rating"]["p"],
      "H3 defect": res["DiD defect"]["p"], "H3 negative": res["DiD neg"]["p"], "H3 performance praised": res["DiD perfpos"]["p"]}
order = sorted(pv, key=pv.get); holm = {}; run = 0.0
for i, k in enumerate(order): run = max(run, min(1.0, pv[k] * (len(pv) - i))); holm[k] = {"raw_p": pv[k], "holm_p": run}
res["holm"] = holm
# validation of LLM coding: coder A (larger model) vs coder H (smaller model) on the 400 validation reviews; star correlation
V = A.merge(H, on="rid", suffixes=("_A", "_H")); res["n_val_pairs"] = int(len(V))
F = ["overall", "defect", "price", "durability", "performance", "fit", "ease", "design", "service"]
if len(V):
    res["kappa_A_vs_H"] = {f: float(cohen_kappa_score(V[f + "_A"].astype(str), V[f + "_H"].astype(str))) for f in F}
    res["agree_A_vs_H"] = {f: float((V[f + "_A"].astype(str) == V[f + "_H"].astype(str)).mean()) for f in F}
    num = {"neg": -1, "neu": 0, "pos": 1}; st = meta.set_index("rid").rating
    for nm in ("A", "H"): s = V["overall_" + nm].map(num); res[f"spearman_{nm}_vs_stars"] = float(spearmanr(s, st.reindex(V.rid).values)[0])
    res["prevalence_H_all"] = {f: float((H[f].astype(int) != 0).mean()) for f in F[2:]}; res["defect_rate_H_all"] = float(H.defect.astype(int).mean())
json.dump(res, open("results_b_content.json", "w"), indent=1)
for k, v in res.items():
    if k in ("cell_means", "holm", "kappa_A_vs_H", "agree_A_vs_H", "prevalence_H_all"): print(k, {a: (round(b, 3) if isinstance(b, float) else b) for a, b in v.items()})
    elif isinstance(v, dict) and "b" in v: print(k, {a: round(b, 4) for a, b in v.items()})
    else: print(k, v)
