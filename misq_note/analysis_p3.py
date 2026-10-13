"""Prediction P3 exactly as in PREREG_P3.md. Usage: python analysis_p3.py STEAMDIR AMAZON_META.csv.gz
STEAMDIR/agg/part_*.csv.gz from steam/aggregate_steam.py; AMAZON_META from study3/prep (all_reviews_meta.csv.gz)."""
import sys, glob, json, warnings
import numpy as np, pandas as pd, pyfixest as pf
sys.path.insert(0, "study3"); warnings.filterwarnings("ignore")
from incentive import disclosed  # noqa (flag already stored in the meta file; import kept for provenance)
res = {}
def tid(m, k): return dict(b=float(m.coef()[k]), se=float(m.se()[k]), p=float(m.pvalue()[k]))
# ---------------- Steam ----------------
A = pd.concat([pd.read_csv(f) for f in glob.glob(f"{sys.argv[1]}/agg/part_*.csv.gz")]); A = A.groupby(["appid", "ym", "sp", "rff", "up", "en"], as_index=False).n.sum()
first = A.groupby("appid").ym.min()
def s_exposure(a, m0, m1, first_before, min_n=30):
    p = a[(a.ym >= m0) & (a.ym <= m1) & (a.sp >= 0)]; k = p.assign(x=(p.sp == 0) * p.n).groupby("appid").x.sum(); n = p.groupby("appid").n.sum()
    g = pd.DataFrame({"n": n, "K": k / n}); g = g[(g.n >= min_n) & (first.reindex(g.index) < first_before)].copy(); g["K10"] = g.K / 0.1; g["zN0"] = (np.log(g.n) - np.log(g.n).mean()) / np.log(g.n).std(); return g
def s_panel(a, g, m0, m1, pol, skip):
    a = a[a.appid.isin(g.index) & (a.ym >= m0) & (a.ym <= m1)].copy(); a["buy"] = (a.sp == 1) * a.n
    c = a.groupby(["appid", "ym"]).agg(ybuy=("buy", "sum")).reset_index(); months = [str(p) for p in pd.period_range(m0, m1, freq="M")]
    full = pd.MultiIndex.from_product([g.index, months], names=["appid", "ym"]).to_frame(index=False); full = full[full.ym >= full.appid.map(first).clip(lower=m0)].merge(c, on=["appid", "ym"], how="left").fillna({"ybuy": 0})
    full = full[full.ym != skip].merge(g[["K10", "zN0"]], left_on="appid", right_index=True); full["post"] = (full.ym >= pol).astype(int)
    full["KP"] = full.K10 * full.post; full["KPz"] = full.KP * full.zN0; return full
def s_fit(P, label):
    m = pf.fepois("ybuy ~ KP + KPz | appid + ym", data=P, vcov={"CRV1": "appid"}); res[f"{label}: KP (main)"] = tid(m, "KP"); res[f"{label}: KPz (P3 interaction)"] = tid(m, "KPz")
g = s_exposure(A, "2015-01", "2016-08", "2016-01"); res["steam: corr(K10, zN0)"] = float(g.K10.corr(g.zN0)); P = s_panel(A, g, "2015-01", "2017-12", "2016-10", "2016-09"); res["steam: n"] = dict(games=int(len(g)), rows=int(len(P)))
s_fit(P, "steam")
Ae = A[A.en == 1]; ge = s_exposure(Ae, "2015-01", "2016-08", "2016-01"); s_fit(s_panel(Ae, ge, "2015-01", "2017-12", "2016-10", "2016-09"), "steam english")
keep = g.n[g.n <= g.n.quantile(0.95)].index; s_fit(P[P.appid.isin(keep)], "steam drop top5%")
gp = s_exposure(A, "2014-03", "2015-08", "2015-01"); s_fit(s_panel(A, gp, "2014-03", "2016-08", "2015-10", "2015-09"), "steam placebo")
json.dump(res, open("results_p3.json", "w"), indent=1); print("steam done", flush=True)
del A, Ae
# ---------------- Amazon ----------------
d = pd.read_csv(sys.argv[2]); d["t"] = pd.to_datetime(d.ts, unit="ms"); d["ym"] = d.t.dt.to_period("M")
def a_exposure(pre0, pol, first_before, min_n=20):
    pre = d[(d.t >= pre0) & (d.t < pol)]; g = pre.groupby("pa").agg(n=("inc", "size"), k=("inc", "sum"), first=("t", "min")); g = g[(g.n >= min_n) & (g["first"] < first_before)].copy()
    g["E10"] = g.k / g.n / 0.1; g["zN0"] = (np.log(g.n) - np.log(g.n).mean()) / np.log(g.n).std(); return g
def a_panel(g, m0, m1, pol):
    x = d[d.pa.isin(g.index) & (d.ym >= m0) & (d.ym <= m1)]; y = x.groupby(["pa", "ym"]).agg(y=("inc", "size"), fl=("inc", "sum")).reset_index(); y["yn"] = y.y - y.fl
    months = pd.period_range(m0, m1, freq="M"); start = g["first"].dt.to_period("M").clip(lower=m0)
    full = pd.MultiIndex.from_product([g.index, months], names=["pa", "ym"]).to_frame(index=False); full = full[full.ym >= full.pa.map(start)].merge(y[["pa", "ym", "yn"]], on=["pa", "ym"], how="left").fillna({"yn": 0})
    full = full.merge(g[["E10", "zN0"]], left_on="pa", right_index=True); full["post"] = (full.ym >= pd.Period(pol, "M")).astype(int); full["mo"] = full.ym.astype(str)
    full["EP"] = full.E10 * full.post; full["EPz"] = full.EP * full.zN0; return full
def a_fit(P, label):
    m = pf.fepois("yn ~ EP + EPz | pa + mo", data=P, vcov={"CRV1": "pa"}); res[f"{label}: EP (main)"] = tid(m, "EP"); res[f"{label}: EPz (P3 interaction)"] = tid(m, "EPz")
ga = a_exposure(pd.Timestamp("2014-01-01"), pd.Timestamp("2016-10-01"), pd.Timestamp("2016-07-01")); res["amazon: corr(E10, zN0)"] = float(ga.E10.corr(ga.zN0))
Pa = a_panel(ga, pd.Period("2015-01", "M"), pd.Period("2017-12", "M"), "2016-10"); res["amazon: n"] = dict(products=int(len(ga)), rows=int(len(Pa))); a_fit(Pa, "amazon")
keep = ga.n[ga.n <= ga.n.quantile(0.95)].index; a_fit(Pa[Pa.pa.isin(keep)], "amazon drop top5%")
gpl = a_exposure(pd.Timestamp("2014-01-01"), pd.Timestamp("2015-10-01"), pd.Timestamp("2015-07-01")); a_fit(a_panel(gpl, pd.Period("2014-07", "M"), pd.Period("2016-09", "M"), "2015-10"), "amazon placebo"); res["amazon placebo: n"] = dict(products=int(len(gpl)))
# Holm over the two primary tests (P3-S, P3-A): predicted beta2 < 0, two-sided p reported; one-sided p = p/2 if negative else 1 - p/2
def one_sided(r): return r["p"] / 2 if r["b"] < 0 else 1 - r["p"] / 2
pv = {"P3-S steam": one_sided(res["steam: KPz (P3 interaction)"]), "P3-A amazon": one_sided(res["amazon: EPz (P3 interaction)"])}
order = sorted(pv, key=pv.get); run = 0.0; holm = {}
for i, k in enumerate(order): run = max(run, min(1.0, pv[k] * (len(pv) - i))); holm[k] = {"one_sided_p": pv[k], "holm_p": run}
res["holm_primary"] = holm
json.dump(res, open("results_p3.json", "w"), indent=1)
for k, v in res.items(): print(k, {a: round(b, 4) for a, b in v.items()} if isinstance(v, dict) and "b" in v else v)
