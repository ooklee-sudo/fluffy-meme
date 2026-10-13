"""Study 3: placebo and event-study checks for review-level outcomes (plan: Identification checks ii).
Usage: python analysis_b_reviewlevel_checks.py all_reviews_meta.csv.gz"""
import sys, json, warnings
import numpy as np, pandas as pd, pyfixest as pf
warnings.filterwarnings("ignore")
d = pd.read_csv(sys.argv[1]); d["t"] = pd.to_datetime(d.ts, unit="ms"); d["ym"] = d.t.dt.to_period("M")
def exposure(pre0, pol, first_before, min_n=20):
    pre = d[(d.t >= pre0) & (d.t < pol)]; g = pre.groupby("pa").agg(n=("inc", "size"), k=("inc", "sum"), first=("t", "min"))
    g = g[(g.n >= min_n) & (g["first"] < first_before)].copy(); g["E10"] = g.k / g.n / 0.1; return g
def reviews(g, t0, t1, pol):
    R = d[(d.pa.isin(g.index)) & (d.t >= t0) & (d.t < t1) & (~d.inc)].merge(g[["E10"]], left_on="pa", right_index=True)
    R["post"] = (R.t >= pol).astype(int); R["E10Post"] = R.E10 * R.post; R["mo"] = R.ym.astype(str)
    R["lenlog"] = np.log1p(R["len"]); R["vp"] = R.vp.astype(int); R["hvlog"] = np.log1p(R.hv); R["q"] = R.t.dt.year * 10 + R.t.dt.quarter; return R
def tidy(m): k = "E10Post"; return dict(b=float(m.coef()[k]), se=float(m.se()[k]), p=float(m.pvalue()[k]))
res = {}
g = exposure(pd.Timestamp("2014-01-01"), pd.Timestamp("2016-10-01"), pd.Timestamp("2016-07-01"))
R = reviews(g, "2015-01-01", "2018-01-01", "2016-10-01")
for out in ("rating", "lenlog", "vp", "hvlog"): res[f"actual {out}"] = tidy(pf.feols(f"{out} ~ E10Post | pa + mo", data=R, vcov={"CRV1": "pa"}))
gp = exposure(pd.Timestamp("2014-01-01"), pd.Timestamp("2015-10-01"), pd.Timestamp("2015-07-01"))
Rp = reviews(gp, "2014-07-01", "2016-10-01", "2015-10-01")
for out in ("rating", "lenlog", "vp", "hvlog"): res[f"placebo {out}"] = tidy(pf.feols(f"{out} ~ E10Post | pa + mo", data=Rp, vcov={"CRV1": "pa"}))
res["n"] = dict(actual=int(len(R)), placebo=int(len(Rp)), placebo_products=int(Rp.pa.nunique()), placebo_exposed_k2=int((gp.k >= 2).sum()))
# event study for rating (actual), reference 2016Q3
for q in sorted(R.q.unique()):
    if q != 20163: R[f"e{q}"] = R.E10 * (R.q == q)
es = [f"e{q}" for q in sorted(R.q.unique()) if q != 20163]
m = pf.feols("rating ~ " + " + ".join(es) + " | pa + mo", data=R, vcov={"CRV1": "pa"})
res["event study rating"] = {k: dict(b=float(m.coef()[k]), se=float(m.se()[k]), p=float(m.pvalue()[k])) for k in es}
# binary treated (k>=2) vs k==0, rating, actual
g2 = g[(g.k == 0) | (g.k >= 2)].copy(); R2 = R[R.pa.isin(g2.index)].copy(); R2["tp"] = ((R2.pa.map(g2.k) >= 2) & (R2.post == 1)).astype(int)
m = pf.feols("rating ~ tp | pa + mo", data=R2, vcov={"CRV1": "pa"}); res["binary k>=2 rating"] = dict(b=float(m.coef()["tp"]), se=float(m.se()["tp"]), p=float(m.pvalue()["tp"]))
json.dump(res, open("results_b_reviewlevel_checks.json", "w"), indent=1)
for k, v in res.items():
    if k.startswith("event"): print(k); [print("  ", a, round(b["b"], 3), round(b["se"], 3), round(b["p"], 3)) for a, b in v.items()]
    else: print(k, {a: (round(b, 4) if isinstance(b, float) else b) for a, b in v.items()})
