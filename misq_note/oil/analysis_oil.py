"""Oil-shock Airbnb analysis as in ANALYSIS_PLAN.md (array-based implementation).
Usage: python analysis_oil.py WORKDIR   (needs listings.parquet, counts.parquet, first.parquet from prep_oil.py and airports.csv)
Deviation from the plan, disclosed: the H1 interrupted time series fits the linear trend on all rows together with the Post dummy
(the plan said the trend is estimated on the pre-period only); H1 is descriptive and H2/H3 do not depend on it.
Second disclosed deviation: for memory reasons the event study uses months 2025-01 to 2026-08 only (reference 2026-02), not the full window."""
import sys, json, time, warnings
import numpy as np, pandas as pd, pyfixest as pf
warnings.filterwarnings("ignore")
W = sys.argv[1]; T0 = time.time()
def log(*a): print(round(time.time() - T0), "s", *a, flush=True)
L = pd.read_parquet(f"{W}/listings.parquet"); C = pd.read_parquet(f"{W}/counts.parquet"); F = pd.read_parquet(f"{W}/first.parquet")
ap = pd.read_csv(f"{W}/airports.csv"); ap = ap[(ap.type == "large_airport") & (ap.scheduled_service == "yes")][["latitude_deg", "longitude_deg"]].values
def mi(y, m): return y * 12 + m - 1
def hav(lat, lon):
    out = np.empty(len(lat))
    a2, o2 = np.radians(ap[:, 0])[None, :], np.radians(ap[:, 1])[None, :]
    for s in range(0, len(lat), 20000):
        la, lo = np.radians(lat[s:s + 20000])[:, None], np.radians(lon[s:s + 20000])[:, None]
        h = np.sin((a2 - la) / 2) ** 2 + np.cos(la) * np.cos(a2) * np.sin((o2 - lo) / 2) ** 2; out[s:s + 20000] = (2 * 6371 * np.arcsin(np.sqrt(h))).min(1)
    return out
def build(m0, m1, a0, a1):
    """Listing-month panel for months m0..m1 (month indices); listings active (>=1 review) in a0..a1."""
    act = C[(C.mi >= a0) & (C.mi <= a1)][["city", "listing_id"]].drop_duplicates()
    Li = L.rename(columns={"id": "listing_id"}).merge(act, on=["city", "listing_id"]).drop_duplicates(["city", "listing_id"]).dropna(subset=["price", "latitude", "longitude"]); Li = Li[Li.price > 0].merge(F, on=["city", "listing_id"], how="left")
    Li["tier"] = Li.groupby("city").price.transform(lambda s: pd.qcut(s.rank(method="first"), 3, labels=False)).astype(int)
    Li["logDist"] = np.log1p(hav(Li.latitude.values, Li.longitude.values)); Li = Li.reset_index(drop=True); N = len(Li); nm = m1 - m0 + 1
    city_id = pd.factorize(Li.city)[0].astype("int32"); start = np.clip(Li.first_mi.fillna(m0).values.astype(int) - m0, 0, None); cnt = nm - start; cnt = np.clip(cnt, 0, None)
    key = np.repeat(np.arange(N, dtype="int32"), cnt); off = np.cumsum(cnt) - cnt; t = (np.arange(cnt.sum()) - np.repeat(off, cnt) + np.repeat(start, cnt)).astype("int16")
    cc = C[(C.mi >= m0) & (C.mi <= m1)].merge(Li[["city", "listing_id"]].reset_index().rename(columns={"index": "k"}), on=["city", "listing_id"])
    code = key.astype("int64") * 100 + t; ccode = cc.k.values.astype("int64") * 100 + (cc.mi.values - m0); order = np.argsort(code); pos = np.searchsorted(code, ccode, sorter=order)
    y = np.zeros(len(code), dtype="int32"); y[order[pos]] = cc.y.values
    P = pd.DataFrame({"key": key, "t": t, "y": y, "city_id": city_id[key], "Low": (Li.tier.values[key] == 0).astype("int8"), "Mid": (Li.tier.values[key] == 1).astype("int8"), "logDist": Li.logDist.values[key].astype("float32")})
    P["cym"] = P.city_id.astype("int32") * 100 + P.t.astype("int32"); cal = ((P.t.astype("int32") + m0) % 12); P["cmo"] = P.city_id.astype("int32") * 12 + cal; P["yr"] = ((P.t.astype("float32") + m0) / 12).astype("float32")
    return P, Li
def tid(m, k): return dict(b=float(m.coef()[k]), se=float(m.se()[k]), p=float(m.pvalue()[k]))
def save(): json.dump(res, open("results_oil.json", "w"), indent=1)
def setpost(P, m0, first_post, drop_transition=True):
    fp = first_post - m0; P = P[P.t != fp - 1].copy() if drop_transition else P.copy()
    P["post"] = (P.t >= fp).astype("int8"); P["LowPost"] = (P.Low * P.post).astype("int8"); P["MidPost"] = (P.Mid * P.post).astype("int8"); P["DistPost"] = (P.logDist * P.post).astype("float32"); return P
res = {}
def main_models(P, label, es_ref=None, full=True):
    m = pf.fepois("y ~ LowPost + MidPost + DistPost | key + cym", data=P, vcov={"CRV1": "key"}); log(label, "H2/H3 fitted")
    for k in ("LowPost", "MidPost", "DistPost"): res[f"{label}: {k}"] = tid(m, k)
    mc = m.vcov({"CRV1": "city_id"}); res[f"{label}: city-clustered LowPost"] = tid(mc, "LowPost"); res[f"{label}: city-clustered DistPost"] = tid(mc, "DistPost")
    save(); m1 = pf.fepois("y ~ post + yr | key + cmo", data=P, vcov={"CRV1": "key"}); res[f"{label}: H1 ITS post"] = tid(m1, "post"); save(); log(label, "H1 fitted")
    if full and es_ref is not None:
        e0 = mi(2025, 1) - mi(2023, 1); Q = P[P.t >= e0].copy(); es = []
        for k in sorted(Q.t.unique()):
            if k != es_ref: Q[f"L{k}"] = (Q.Low * (Q.t == k)).astype("float32"); es.append(f"L{k}")
        me = pf.fepois("y ~ " + " + ".join(es) + " | key + cym", data=Q, vcov={"CRV1": "key"}); res[f"{label}: event study Low (2025-01..2026-08 only)"] = {k: dict(b=float(me.coef()[k]), se=float(me.se()[k]), p=float(me.pvalue()[k])) for k in es}; save(); log(label, "event study fitted")
        del Q
    return m
# main: window 2023-01..2026-08, activity 2024-03..2025-02, post = 2026-04.., March 2026 transition
M0, M1 = mi(2023, 1), mi(2026, 8); P0, Li = build(M0, M1, mi(2024, 3), mi(2025, 2)); log("built main", len(P0), "rows", int(Li.shape[0]), "listings")
res["n_main"] = dict(listings=int(len(Li)), rows=int(len(P0)), cities=int(P0.city_id.nunique()), reviews=int(P0.y.sum())); save()
Pm = setpost(P0, M0, mi(2026, 4)); ref = mi(2026, 2) - M0; main_models(Pm, "main", es_ref=ref)
# robustness: drop top 5% volume; include March as post
tot = Pm.groupby("key").y.sum(); keep = tot[tot <= tot.quantile(0.95)].index; Pk = Pm[Pm.key.isin(keep)]
mk = pf.fepois("y ~ LowPost + MidPost + DistPost | key + cym", data=Pk, vcov={"CRV1": "key"}); res["drop top5%: LowPost"] = tid(mk, "LowPost"); res["drop top5%: DistPost"] = tid(mk, "DistPost"); log("top5 done")
Pm3 = setpost(P0, M0, mi(2026, 3), drop_transition=False); m3 = pf.fepois("y ~ LowPost + MidPost + DistPost | key + cym", data=Pm3, vcov={"CRV1": "key"}); res["incl March: LowPost"] = tid(m3, "LowPost"); res["incl March: DistPost"] = tid(m3, "DistPost"); log("March done")
# placebo: fake shock, first post month 2025-04, window 2022-01..2025-08, activity window 2023-03..2024-02, March 2025 transition
PM0, PM1 = mi(2022, 1), mi(2025, 8); Pp0, Lp = build(PM0, PM1, mi(2023, 3), mi(2024, 2)); Pp = setpost(Pp0, PM0, mi(2025, 4)); res["n_placebo"] = dict(listings=int(len(Lp)), rows=int(len(Pp)))
main_models(Pp, "placebo", es_ref=None, full=False)
save()
for k, v in res.items():
    if "event study" in k: continue
    print(k, v if not isinstance(v, dict) or "b" not in v else {a: round(b, 4) for a, b in v.items()})
print("event study Low x month (reference 2026-02), t offsets from 2023-01:")
for k, v in res["main: event study Low (2025-01..2026-08 only)"].items():
    print("  ", k, round(v["b"], 3), round(v["se"], 3), round(v["p"], 3))
