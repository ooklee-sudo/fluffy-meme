"""Yelp COVID analysis exactly as in ANALYSIS_PLAN.md. Usage: python analysis_yelp.py YELPDIR"""
import sys, json, warnings
import numpy as np, pandas as pd, pyfixest as pf
warnings.filterwarnings("ignore")
D = sys.argv[1]
r = pd.read_csv(f"{D}/reviews_flags.csv.gz"); b = pd.read_csv(f"{D}/business_flags.csv.gz")
r["ym"] = r.date.str.slice(0, 7); b = b.set_index("business_id")
res = {"n_reviews": int(len(r)), "n_restaurants": int(r.business_id.nunique())}
# descriptive monthly shares of regex proxies
m = r[(r.ym >= "2019-01") & (r.ym <= "2021-12")].groupby("ym").agg(n=("tk", "size"), tk=("tk", "mean"), cv=("cv", "mean"))
res["monthly_2019_2021"] = {k: dict(n=int(v.n), tk=round(float(v.tk), 4), cv=round(float(v.cv), 4)) for k, v in m.iterrows()}
CAT_TAKE = ["Fast Food", "Pizza", "Sandwiches", "Burgers", "Chicken Wings", "Food Trucks", "Bakeries", "Coffee & Tea"]
CAT_DINE = ["Bars", "Nightlife", "Steakhouses", "Buffets", "Breweries", "Wine Bars"]
def exposure(a, m0, m1, min_n=10):
    p = a[(a.ym >= m0) & (a.ym <= m1)]; g = p.groupby("business_id").agg(n=("tk", "size"), T=("tk", "mean")); g = g[g.n >= min_n].copy()
    g["Tz"] = (g["T"] - g["T"].mean()) / g["T"].std(); return g
def panel(a, g, m0, m1, shock):
    x = a[(a.business_id.isin(g.index)) & (a.ym >= m0) & (a.ym <= m1)]
    c = x.groupby(["business_id", "ym"]).size().rename("y").reset_index(); months = [str(p) for p in pd.period_range(m0, m1, freq="M")]
    full = pd.MultiIndex.from_product([g.index, months], names=["business_id", "ym"]).to_frame(index=False).merge(c, on=["business_id", "ym"], how="left").fillna({"y": 0})
    full = full.merge(g[["Tz", "n"]], left_on="business_id", right_index=True); full["post"] = (full.ym >= shock).astype(int); full["TPost"] = full.Tz * full.post
    full["state"] = full.business_id.map(b.state); return full
def tid(m, k="TPost"): return dict(b=float(m.coef()[k]), se=float(m.se()[k]), p=float(m.pvalue()[k]))
SH = "2020-03"; g = exposure(r, "2018-03", "2020-02"); res["exposure"] = dict(eligible=int(len(g)), T_mean=float(g["T"].mean()), T_sd=float(g["T"].std()))
P = panel(r, g, "2018-03", "2021-12", SH); res["panel"] = dict(rows=int(len(P)))
m1 = pf.fepois("y ~ TPost | business_id + ym", data=P, vcov={"CRV1": "business_id"}); res["C1 volume (Tz x Post)"] = tid(m1)
P["city"] = P.business_id.map(b.city); m1c = pf.fepois("y ~ TPost | business_id + ym", data=P, vcov={"CRV1": "city"}); res["C1 cluster by city"] = tid(m1c)
# rating
R = r[(r.business_id.isin(g.index)) & (r.ym >= "2018-03") & (r.ym <= "2021-12")].merge(g[["Tz"]], left_on="business_id", right_index=True)
R["post"] = (R.ym >= SH).astype(int); R["TPost"] = R.Tz * R.post; m2 = pf.feols("stars ~ TPost | business_id + ym", data=R, vcov={"CRV1": "business_id"}); res["C2 rating (Tz x Post)"] = tid(m2)
# event study (reference 2020-02), months shown from 2019-06
months = sorted(P.ym.unique()); ref = "2020-02"
for mo in months:
    if mo != ref: P[f"e{mo.replace('-', '_')}"] = P.Tz * (P.ym == mo)
es = [f"e{mo.replace('-', '_')}" for mo in months if mo != ref]
m3 = pf.fepois("y ~ " + " + ".join(es) + " | business_id + ym", data=P, vcov={"CRV1": "business_id"})
res["C3 event study"] = {k: dict(b=float(m3.coef()[k]), se=float(m3.se()[k]), p=float(m3.pvalue()[k])) for k in es}
# placebo
gp = exposure(r, "2017-03", "2019-02"); Pp = panel(r, gp, "2017-03", "2020-02", "2019-03")
mp = pf.fepois("y ~ TPost | business_id + ym", data=Pp, vcov={"CRV1": "business_id"}); res["placebo volume (shock 2019-03)"] = tid(mp); res["n_placebo"] = int(len(gp))
Rp = r[(r.business_id.isin(gp.index)) & (r.ym >= "2017-03") & (r.ym <= "2020-02")].merge(gp[["Tz"]], left_on="business_id", right_index=True)
Rp["TPost"] = Rp.Tz * (Rp.ym >= "2019-03").astype(int); res["placebo rating"] = tid(pf.feols("stars ~ TPost | business_id + ym", data=Rp, vcov={"CRV1": "business_id"}))
# exclude Alberta; drop top 5% volume
res["excl Alberta (volume)"] = tid(pf.fepois("y ~ TPost | business_id + ym", data=P[P.state != "AB"], vcov={"CRV1": "business_id"}))
keep = g.n[g.n <= g.n.quantile(0.95)].index; res["drop top 5% (volume)"] = tid(pf.fepois("y ~ TPost | business_id + ym", data=P[P.business_id.isin(keep)], vcov={"CRV1": "business_id"}))
# category exposure: takeout-oriented vs dine-in-oriented categories
def has(cats, lst): return any(f"{c}" in str(cats).split(", ") for c in lst)
cat = b.cat.fillna("").map(lambda s: 1 if has(s, CAT_TAKE) and not has(s, CAT_DINE) else (-1 if has(s, CAT_DINE) and not has(s, CAT_TAKE) else 0))
Pc = P[P.business_id.map(cat).isin([1, -1])].copy(); Pc["TK"] = (Pc.business_id.map(cat) == 1).astype(int); Pc["TKPost"] = Pc.TK * Pc.post
res["category exposure (takeout vs dine-in)"] = tid(pf.fepois("y ~ TKPost | business_id + ym", data=Pc, vcov={"CRV1": "business_id"}), "TKPost"); res["n_cat_businesses"] = int(Pc.business_id.nunique())
# stability of exposure: T from 2017-03..2018-02
g0 = exposure(r, "2017-03", "2018-02"); both = g.join(g0, rsuffix="0", how="inner"); res["exposure_corr_pre_vs_earlier"] = float(both["T"].corr(both["T0"])); res["n_corr"] = int(len(both))
json.dump(res, open("results_yelp.json", "w"), indent=1)
for k, v in res.items():
    if k in ("monthly_2019_2021", "C3 event study"): continue
    print(k, v if not isinstance(v, dict) or "b" not in v else {a: round(b_, 4) for a, b_ in v.items()})
print("event study (Tz x month, ref 2020-02):")
for k, v in res["C3 event study"].items():
    if k >= "e2019_06": print("  ", k, round(v["b"], 3), round(v["se"], 3), round(v["p"], 3))
print("monthly proxies:", {k: (v["n"], v["tk"], v["cv"]) for k, v in res["monthly_2019_2021"].items() if k in ("2019-06", "2020-02", "2020-03", "2020-04", "2020-06", "2020-12", "2021-06", "2021-12")})
