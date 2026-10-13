"""Study 3, non-LLM analyses of the Oct-2016 incentivized-review ban, as pre-specified in ANALYSIS_PLAN.md.
Usage: python analysis_b_volume.py all_reviews_meta.csv.gz"""
import sys, json, warnings
import numpy as np, pandas as pd, pyfixest as pf
warnings.filterwarnings("ignore")
d = pd.read_csv(sys.argv[1]); d["t"] = pd.to_datetime(d.ts, unit="ms"); d["ym"] = d.t.dt.to_period("M")
def exposure(pre0, pol, first_before, min_n=20):
    pre = d[(d.t >= pre0) & (d.t < pol)]
    g = pre.groupby("pa").agg(n=("inc", "size"), k=("inc", "sum"), first=("t", "min"))
    g = g[(g.n >= min_n) & (g["first"] < first_before)].copy(); g["E"] = g.k / g.n; g["E10"] = g.E / 0.1; return g
def panel(g, m0, m1, pol):
    x = d[d.pa.isin(g.index) & (d.ym >= m0) & (d.ym <= m1)]
    y = x.groupby(["pa", "ym"]).agg(y=("inc", "size"), flagged=("inc", "sum")).reset_index(); y["yn"] = y.y - y.flagged
    months = pd.period_range(m0, m1, freq="M"); start = g["first"].dt.to_period("M").clip(lower=m0)
    full = pd.MultiIndex.from_product([g.index, months], names=["pa", "ym"]).to_frame(index=False)
    full = full[full.ym >= full.pa.map(start)].merge(y, on=["pa", "ym"], how="left").fillna({"y": 0, "yn": 0, "flagged": 0})
    full = full.merge(g[["k", "E", "E10"]], left_on="pa", right_index=True)
    full["post"] = (full.ym >= pd.Period(pol, "M")).astype(int); full["mo"] = full.ym.astype(str)
    full["q"] = full.ym.dt.qyear * 10 + full.ym.dt.quarter; full["E10Post"] = full.E10 * full.post; full["pid"] = pd.factorize(full.pa)[0]
    return full
def tidy(m, name):
    return {k: dict(b=float(m.coef()[k]), se=float(m.se()[k]), p=float(m.pvalue()[k])) for k in m.coef().index if k == name}
res = {}
POL = "2016-10"; g = exposure(pd.Timestamp("2014-01-01"), pd.Timestamp("2016-10-01"), pd.Timestamp("2016-07-01"))
P = panel(g, pd.Period("2015-01", "M"), pd.Period("2017-12", "M"), POL)
res["n"] = dict(products=int(P.pa.nunique()), product_months=int(len(P)), treated_k2=int((g.k >= 2).sum()), control_k0=int((g.k == 0).sum()), reviews=int(P.y.sum()), flagged_pre=int(P[P.post == 0].flagged.sum()), flagged_post=int(P[P.post == 1].flagged.sum()))
for out, nm in (("y", "H1a all reviews"), ("yn", "H1b non-flagged reviews")):
    m = pf.fepois(f"{out} ~ E10Post | pa + mo", data=P, vcov={"CRV1": "pa"}); res[nm + " (continuous E, per +10pp)"] = tidy(m, "E10Post")
for lab, cond in (("k>=1 vs 0", lambda k: k >= 1), ("k>=2 vs 0", lambda k: k >= 2), ("k>=3 vs 0", lambda k: k >= 3)):
    Q = P[(P.k == 0) | cond(P.k)].copy(); Q["tp"] = (cond(Q.k) & (Q.post == 1)).astype(int)
    for out in ("y", "yn"):
        m = pf.fepois(f"{out} ~ tp | pa + mo", data=Q, vcov={"CRV1": "pa"}); res[f"binary {lab} [{out}]"] = tidy(m, "tp")
# event study (all reviews), reference 2016Q3
qs = sorted(P.q.unique()); ref = 20163
for q in qs:
    if q != ref: P[f"e{q}"] = P.E10 * (P.q == q)
es = [f"e{q}" for q in qs if q != ref]; m = pf.fepois("y ~ " + " + ".join(es) + " | pa + mo", data=P, vcov={"CRV1": "pa"})
res["event study (all reviews), ref 2016Q3"] = {k: dict(b=float(m.coef()[k]), se=float(m.se()[k]), p=float(m.pvalue()[k])) for k in es}
# drop top 5% by pre volume
pre_n = g.n; keep = pre_n[pre_n <= pre_n.quantile(0.95)].index; Pt = P[P.pa.isin(keep)]
m = pf.fepois("y ~ E10Post | pa + mo", data=Pt, vcov={"CRV1": "pa"}); res["drop top 5% volume [y]"] = tidy(m, "E10Post")
# wider window
P2 = panel(g, pd.Period("2015-01", "M"), pd.Period("2018-12", "M"), POL); m = pf.fepois("y ~ E10Post | pa + mo", data=P2, vcov={"CRV1": "pa"}); res["window to 2018-12 [y]"] = tidy(m, "E10Post")
# placebo: fake policy 2015-10, exposure from 2014-01..2015-09, window 2014-07..2016-09
gp = exposure(pd.Timestamp("2014-01-01"), pd.Timestamp("2015-10-01"), pd.Timestamp("2015-07-01"))
Pp = panel(gp, pd.Period("2014-07", "M"), pd.Period("2016-09", "M"), "2015-10")
for out in ("y", "yn"):
    m = pf.fepois(f"{out} ~ E10Post | pa + mo", data=Pp, vcov={"CRV1": "pa"}); res[f"placebo 2015-10 [{out}]"] = tidy(m, "E10Post")
res["n_placebo"] = dict(products=int(Pp.pa.nunique()), exposed_k2=int((gp.k >= 2).sum()))
# rating, length, verified, helpful: review level, non-flagged, same window
R = d[(d.pa.isin(g.index)) & (d.t >= "2015-01-01") & (d.t < "2018-01-01") & (~d.inc)].merge(g[["E10"]], left_on="pa", right_index=True)
R["post"] = (R.t >= "2016-10-01").astype(int); R["E10Post"] = R.E10 * R.post; R["mo"] = R.ym.astype(str); R["lenlog"] = np.log1p(R["len"]); R["vp"] = R.vp.astype(int); R["hvlog"] = np.log1p(R.hv)
for out in ("rating", "lenlog", "vp", "hvlog"):
    m = pf.feols(f"{out} ~ E10Post | pa + mo", data=R, vcov={"CRV1": "pa"}); res[f"review-level {out} (non-flagged)"] = tidy(m, "E10Post")
res["n_review_level"] = int(len(R))
# aggregate series diagnostics for the whole category
s = d.groupby("ym").size().reindex(pd.period_range("2012-01", "2022-12", freq="M"), fill_value=0)
res["aggregate"] = dict(months=int(len(s)), mean=float(s.mean()), var_mean=float(s.var() / s.mean()))
json.dump(res, open("results_b_volume.json", "w"), indent=1)
for k, v in res.items():
    if k.startswith("event"): print(k); [print("  ", a, round(b["b"], 3), round(b["se"], 3), round(b["p"], 3)) for a, b in v.items()]
    else: print(k, v if not isinstance(v, dict) or "n" in k or "aggregate" in k else {a: (round(b["b"], 3), round(b["se"], 3), round(b["p"], 4)) for a, b in v.items()})
