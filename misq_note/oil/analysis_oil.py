"""Oil-shock Airbnb analysis exactly as in ANALYSIS_PLAN.md. Usage: python analysis_oil.py DATADIR  (DATADIR has <state>_<city>_{reviews,listings}.csv.gz and airports.csv)"""
import sys, glob, json, re, warnings
import numpy as np, pandas as pd, pyfixest as pf
warnings.filterwarnings("ignore")
D = sys.argv[1]
ap = pd.read_csv(f"{D}/airports.csv"); ap = ap[(ap.type == "large_airport") & (ap.scheduled_service == "yes")][["latitude_deg", "longitude_deg"]].values
def hav(lat, lon):
    la, lo = np.radians(lat)[:, None], np.radians(lon)[:, None]; a2, o2 = np.radians(ap[:, 0])[None, :], np.radians(ap[:, 1])[None, :]
    h = np.sin((a2 - la) / 2) ** 2 + np.cos(la) * np.cos(a2) * np.sin((o2 - lo) / 2) ** 2; return (2 * 6371 * np.arcsin(np.sqrt(h))).min(1)
def load(region):
    L, R = [], []
    for f in sorted(glob.glob(f"{D}/{region}_*_listings.csv.gz")):
        city = f.split("/")[-1].replace("_listings.csv.gz", ""); l = pd.read_csv(f, usecols=["id", "price", "room_type", "latitude", "longitude"]); l["city"] = city
        r = pd.read_csv(f.replace("listings", "reviews"), usecols=["listing_id", "date"]); r["city"] = city; L.append(l); R.append(r)
    L = pd.concat(L); R = pd.concat(R); L["price"] = pd.to_numeric(L.price.astype(str).str.replace(r"[$,]", "", regex=True), errors="coerce"); return L, R
def build(L, R, m0, m1, act0, act1):
    R = R.copy(); R["ym"] = R.date.str.slice(0, 7); R["key"] = R.city + "|" + R.listing_id.astype(str); L = L.copy(); L["key"] = L.city + "|" + L.id.astype(str)
    act = R[(R.ym >= act0) & (R.ym <= act1)].key.unique(); L = L[L.key.isin(act)].drop_duplicates("key").dropna(subset=["price", "latitude", "longitude"]); L = L[L.price > 0]
    L["tier"] = L.groupby("city").price.transform(lambda s: pd.qcut(s.rank(method="first"), 3, labels=False)); L["logDist"] = np.log1p(hav(L.latitude.values, L.longitude.values))
    L["Low"] = (L.tier == 0).astype(int); L["Mid"] = (L.tier == 1).astype(int); L["entire"] = (L.room_type == "Entire home/apt").astype(int)
    first = R.groupby("key").ym.min(); months = [str(p) for p in pd.period_range(m0, m1, freq="M")]
    c = R[(R.ym >= m0) & (R.ym <= m1) & R.key.isin(L.key)].groupby(["key", "ym"]).size().rename("y").reset_index()
    P = pd.MultiIndex.from_product([L.key.values, months], names=["key", "ym"]).to_frame(index=False)
    P = P[P.ym >= P.key.map(first).clip(lower=m0)].merge(c, on=["key", "ym"], how="left").fillna({"y": 0}).merge(L[["key", "city", "Low", "Mid", "logDist", "entire"]], on="key")
    P["cym"] = P.city + "|" + P.ym; P["cmo"] = P.city + "|" + P.ym.str.slice(5, 7); P["yr"] = P.ym.str.slice(0, 4).astype(int) + (P.ym.str.slice(5, 7).astype(int) - 1) / 12; return P
def tid(m, k): return dict(b=float(m.coef()[k]), se=float(m.se()[k]), p=float(m.pvalue()[k]))
def run(L, R, shock_first_post, m0, m1, drop_transition, label, res, full=True):
    P = build(L, R, m0, m1, str(pd.Period(shock_first_post, "M") - 12 - 0)[:7] if False else "2024-03", "2025-02") if label == "main" else build(L, R, m0, m1, "2023-03", "2024-02")
    trans = str(pd.Period(shock_first_post, "M") - 1)
    if drop_transition: P = P[P.ym != trans]
    P["post"] = (P.ym >= shock_first_post).astype(int); P["LowPost"] = P.Low * P.post; P["MidPost"] = P.Mid * P.post; P["DistPost"] = P.logDist * P.post
    res[f"{label}: n"] = dict(listings=int(P.key.nunique()), rows=int(len(P)), cities=int(P.city.nunique()), reviews=int(P.y.sum()))
    m = pf.fepois("y ~ LowPost + MidPost + DistPost | key + cym", data=P, vcov={"CRV1": "key"})
    for k in ("LowPost", "MidPost", "DistPost"): res[f"{label}: H2/H3 {k}"] = tid(m, k)
    mc = pf.fepois("y ~ LowPost + MidPost + DistPost | key + cym", data=P, vcov={"CRV1": "city"}); res[f"{label}: city-clustered LowPost"] = tid(mc, "LowPost"); res[f"{label}: city-clustered DistPost"] = tid(mc, "DistPost")
    # H1 interrupted time series: trend on pre-period, Post deviation
    pre_end = str(pd.Period(shock_first_post, "M") - 2)
    P2 = P[(P.ym <= pre_end) | (P.ym >= shock_first_post)].copy(); P2["trend"] = np.where(P2.ym <= pre_end, P2.yr, P2.yr[P2.ym <= pre_end].max() if (P2.ym <= pre_end).any() else 0)
    # linear year trend estimated through the pre-period only; post months carry the post dummy
    P2["trend"] = P2.yr
    m1_ = pf.fepois("y ~ post + trend | key + cmo", data=P2, vcov={"CRV1": "key"}); res[f"{label}: H1 ITS post"] = tid(m1_, "post")
    if full:
        ref = "2026-02" if label == "main" else "2025-02"; months = sorted(P.ym.unique()); es = []
        for mo in months:
            if mo != ref:
                P[f"L{mo.replace('-', '_')}"] = P.Low * (P.ym == mo); es.append(f"L{mo.replace('-', '_')}")
        me = pf.fepois("y ~ " + " + ".join(es) + " | key + cym", data=P, vcov={"CRV1": "key"}); res[f"{label}: event study Low"] = {k: dict(b=float(me.coef()[k]), se=float(me.se()[k]), p=float(me.pvalue()[k])) for k in es}
    return P
res = {}; LU, RU = load("[a-z][a-z]"); res["n_us_cities"] = int(LU.city.nunique()); res["n_us_listings_snapshot"] = int(len(LU)); res["n_us_reviews"] = int(len(RU))
mon = RU.date.str.slice(0, 7).value_counts().sort_index(); res["monthly_reviews_2025_2026"] = {k: int(v) for k, v in mon["2025-01":"2026-09"].items()}
Pm = run(LU, RU, "2026-04", "2023-01", "2026-08", True, "main", res)
# robustness: include March as post; drop top 5% volume
Pm_ = Pm.copy(); tot = Pm_.groupby("key").y.sum(); keep = tot[tot <= tot.quantile(0.95)].index; Pk = Pm_[Pm_.key.isin(keep)]
mk = pf.fepois("y ~ LowPost + MidPost + DistPost | key + cym", data=Pk, vcov={"CRV1": "key"}); res["drop top5%: LowPost"] = tid(mk, "LowPost"); res["drop top5%: DistPost"] = tid(mk, "DistPost")
Pm3 = build(LU, RU, "2023-01", "2026-08", "2024-03", "2025-02"); Pm3["post"] = (Pm3.ym >= "2026-03").astype(int); Pm3["LowPost"] = Pm3.Low * Pm3.post; Pm3["MidPost"] = Pm3.Mid * Pm3.post; Pm3["DistPost"] = Pm3.logDist * Pm3.post
m3 = pf.fepois("y ~ LowPost + MidPost + DistPost | key + cym", data=Pm3, vcov={"CRV1": "key"}); res["incl March: LowPost"] = tid(m3, "LowPost"); res["incl March: DistPost"] = tid(m3, "DistPost")
# placebo: fake shock 2025-04 (post 2025-04..2025-08), window 2022-01..2025-08, activity window 2023-03..2024-02
run(LU, RU, "2025-04", "2022-01", "2025-08", True, "placebo", res, full=False)
json.dump(res, open("results_oil.json", "w"), indent=1)
for k, v in res.items():
    if k.startswith("monthly") or "event study" in k: continue
    print(k, v if not isinstance(v, dict) or "b" not in v else {a: round(b, 4) for a, b in v.items()})
print("event study Low x month (ref 2026-02), 2025-09 onward:")
for k, v in res["main: event study Low"].items():
    if k >= "L2025_09": print("  ", k, round(v["b"], 3), round(v["se"], 3), round(v["p"], 3))
