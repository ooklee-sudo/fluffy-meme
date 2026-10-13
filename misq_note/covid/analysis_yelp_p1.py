"""Prediction P1 as in ANALYSIS_PLAN_ADDENDUM_P1.md. Usage: python analysis_yelp_p1.py YELPDIR"""
import sys, json, warnings
import numpy as np, pandas as pd, pyfixest as pf
warnings.filterwarnings("ignore")
D = sys.argv[1]; r = pd.read_csv(f"{D}/reviews_flags.csv.gz"); b = pd.read_csv(f"{D}/business_flags.csv.gz").set_index("business_id"); r["ym"] = r.date.str.slice(0, 7)
CAT_TAKE = ["Fast Food", "Pizza", "Sandwiches", "Burgers", "Chicken Wings", "Food Trucks", "Bakeries", "Coffee & Tea"]; CAT_DINE = ["Bars", "Nightlife", "Steakhouses", "Buffets", "Breweries", "Wine Bars"]
def exposure(a, m0, m1, min_n=10):
    p = a[(a.ym >= m0) & (a.ym <= m1)]; g = p.groupby("business_id").agg(n=("tk", "size"), T=("tk", "mean")); g = g[g.n >= min_n].copy(); g["Tz"] = (g["T"] - g["T"].mean()) / g["T"].std(); return g
def vtable(a, g, bounds, thr=3, minmonths=6):
    x = a[a.business_id.isin(g.index)]; mm = x.groupby(["business_id", "ym"]).stars.agg(["mean", "size"]).reset_index(); mm = mm[mm["size"] >= thr]
    rows = []
    for post, (m0, m1) in enumerate(bounds):
        y = mm[(mm.ym >= m0) & (mm.ym <= m1)]; k = y.groupby("business_id")["mean"].agg(["var", "size"]); h = y.groupby("business_id")["size"].apply(lambda s: len(s) / np.sum(1.0 / s))
        k = k[k["size"] >= minmonths].join(h.rename("nh")); k["post"] = post; rows.append(k.reset_index())
    t = pd.concat(rows); cnt = t.groupby("business_id").post.nunique(); t = t[t.business_id.isin(cnt[cnt == 2].index)].copy()
    t = t[t["var"] > 0]; t["logV"] = np.log(t["var"]); t["lognh"] = np.log(t.nh); t = t.merge(g[["Tz"]], left_on="business_id", right_index=True); t["PostT"] = t.post * t.Tz; return t
def tid(m, k): return dict(b=float(m.coef()[k]), se=float(m.se()[k]), p=float(m.pvalue()[k]))
res = {}
g = exposure(r, "2018-03", "2020-02"); t = vtable(r, g, [("2018-03", "2020-02"), ("2020-03", "2021-12")]); res["n_restaurants"] = int(t.business_id.nunique())
res["descriptive"] = {f"post{p}": dict(median_var=float(t[t.post == p]["var"].median()), median_nh=float(t[t.post == p].nh.median())) for p in (0, 1)}
res["P1 primary: logV ~ Post x T"] = tid(pf.feols("logV ~ post + PostT | business_id", data=t, vcov={"CRV1": "business_id"}), "PostT")
res["S1 elasticity logV ~ log n_h"] = tid(pf.feols("logV ~ lognh | business_id", data=t, vcov={"CRV1": "business_id"}), "lognh")
res["S2 mediation: PostT with log n_h"] = tid(pf.feols("logV ~ post + PostT + lognh | business_id", data=t, vcov={"CRV1": "business_id"}), "PostT")
t5 = vtable(r, g, [("2018-03", "2020-02"), ("2020-03", "2021-12")], thr=5); res["check n>=5"] = tid(pf.feols("logV ~ post + PostT | business_id", data=t5, vcov={"CRV1": "business_id"}), "PostT"); res["n_check5"] = int(t5.business_id.nunique())
gp = exposure(r, "2017-03", "2019-02"); tp = vtable(r, gp, [("2017-03", "2019-02"), ("2019-03", "2020-02")]); res["placebo (shock 2019-03)"] = tid(pf.feols("logV ~ post + PostT | business_id", data=tp, vcov={"CRV1": "business_id"}), "PostT"); res["n_placebo"] = int(tp.business_id.nunique())
bab = b.index[b.state != "AB"]; res["excl Alberta"] = tid(pf.feols("logV ~ post + PostT | business_id", data=t[t.business_id.isin(bab)], vcov={"CRV1": "business_id"}), "PostT")
def cat(s):
    L = str(s).split(", "); tk = any(c in L for c in CAT_TAKE); dn = any(c in L for c in CAT_DINE); return 1 if tk and not dn else (-1 if dn and not tk else 0)
c = b.cat.fillna("").map(cat); tc = t[t.business_id.map(c).isin([1, -1])].copy(); tc["TK"] = (tc.business_id.map(c) == 1).astype(int); tc["PostTK"] = tc.post * tc.TK
res["category exposure"] = tid(pf.feols("logV ~ post + PostTK | business_id", data=tc, vcov={"CRV1": "business_id"}), "PostTK"); res["n_cat"] = int(tc.business_id.nunique())
json.dump(res, open("results_yelp_p1.json", "w"), indent=1)
for k, v in res.items(): print(k, {a: round(b_, 4) for a, b_ in v.items()} if isinstance(v, dict) and "b" in v else v)
