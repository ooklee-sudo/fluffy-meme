"""Steam analysis exactly as in ANALYSIS_PLAN.md. Usage: python analysis_steam.py AGGDIR   (AGGDIR/agg/part_*.csv.gz)"""
import sys, glob, json, warnings
import numpy as np, pandas as pd, pyfixest as pf
warnings.filterwarnings("ignore")
A = pd.concat([pd.read_csv(f) for f in glob.glob(f"{sys.argv[1]}/agg/part_*.csv.gz")])
A = A.groupby(["appid", "ym", "sp", "rff", "up", "en"], as_index=False).n.sum()
res = {"total_reviews": int(A.n.sum()), "games": int(A.appid.nunique())}
mt = A.groupby("ym").n.sum(); res["monthly_totals_2015_2018"] = {k: int(v) for k, v in mt["2015-01":"2018-12"].items()}
res["last_months"] = {k: int(v) for k, v in mt.tail(14).items()}
first = A.groupby("appid").ym.min()
def exposure(a, m0, m1, first_before, kind="sp", min_n=30):
    pre = a[(a.ym >= m0) & (a.ym <= m1)]
    if kind == "sp": pre = pre[pre.sp >= 0]; k = pre.assign(x=(pre.sp == 0) * pre.n).groupby("appid").x.sum(); n = pre.groupby("appid").n.sum()
    else: pre = pre[pre.rff >= 0]; k = pre.assign(x=(pre.rff == 1) * pre.n).groupby("appid").x.sum(); n = pre.groupby("appid").n.sum()
    g = pd.DataFrame({"n": n, "K": k / n}); g = g[(g.n >= min_n) & (first.reindex(g.index) < first_before)]; g["K10"] = g.K / 0.1; return g
def panel(a, g, m0, m1, pol, skip=None):
    a = a[a.appid.isin(g.index) & (a.ym >= m0) & (a.ym <= m1)].copy(); a["key"] = (a.sp == 0) * a.n; a["buy"] = (a.sp == 1) * a.n; a["upn"] = (a.up == 1) * a.n
    c = a.groupby(["appid", "ym"]).agg(y=("n", "sum"), ykey=("key", "sum"), ybuy=("buy", "sum"), up=("upn", "sum")).reset_index()
    months = [str(p) for p in pd.period_range(m0, m1, freq="M")]
    full = pd.MultiIndex.from_product([g.index, months], names=["appid", "ym"]).to_frame(index=False)
    full = full[full.ym >= full.appid.map(first).clip(lower=m0)].merge(c, on=["appid", "ym"], how="left").fillna(0)
    if skip: full = full[full.ym != skip]
    full = full.merge(g[["K", "K10"]], left_on="appid", right_index=True); full["post"] = (full.ym >= pol).astype(int)
    full["K10Post"] = full.K10 * full.post; full["share"] = np.where(full.y > 0, full.up / full.y.replace(0, np.nan), np.nan)
    full["q"] = pd.PeriodIndex(full.ym, freq="M").qyear * 10 + pd.PeriodIndex(full.ym, freq="M").quarter; return full
def tidy(m, nm): return {nm: dict(b=float(m.coef()[nm]), se=float(m.se()[nm]), p=float(m.pvalue()[nm]))}
POL = "2016-10"
g = exposure(A, "2015-01", "2016-08", "2016-01"); res["exposure"] = dict(games=int(len(g)), K_mean=float(g.K.mean()), K_sd=float(g.K.std()), K_median=float(g.K.median()), share_K_ge_10pct=float((g.K >= 0.1).mean()))
P = panel(A, g, "2015-01", "2017-12", POL, skip="2016-09"); res["n_panel"] = dict(rows=int(len(P)), games=int(P.appid.nunique()))
sd10 = g.K.std() / 0.1
for out, nm in (("ykey", "S1 key reviews"), ("y", "S2 all reviews"), ("ybuy", "S2b purchase reviews")):
    m = pf.fepois(f"{out} ~ K10Post | appid + ym", data=P, vcov={"CRV1": "appid"}); res[nm] = tidy(m, "K10Post"); res[nm]["per_SD"] = res[nm]["K10Post"]["b"] * sd10
Ps = P.dropna(subset=["share"]); m = pf.feols("share ~ K10Post | appid + ym", data=Ps, weights="y", vcov={"CRV1": "appid"}); res["S3 positive share"] = tidy(m, "K10Post"); res["S3 positive share"]["per_SD"] = res["S3 positive share"]["K10Post"]["b"] * sd10
# S4 gap between key and purchase positive shares, descriptive, game-months with both
a = A[(A.appid.isin(g.index)) & (A.ym >= "2015-01") & (A.ym <= "2017-12") & (A.ym != "2016-09") & (A.sp >= 0)].copy(); a["post"] = (a.ym >= POL).astype(int)
s4 = {}
for post in (0, 1):
    for sp in (0, 1):
        x = a[(a.post == post) & (a.sp == sp)]; s4[f"post{post}_{'key' if sp == 0 else 'buy'}"] = float((x.n * (x.up == 1)).sum() / x.n.sum())
res["S4 positive share by group"] = s4
# event study, reference 2016Q2
qs = sorted(P.q.unique()); ref = 20162
for q in qs:
    if q != ref and q != 20163: P[f"e{q}"] = P.K10 * (P.q == q)
es = [f"e{q}" for q in qs if q != ref and q != 20163]
for out, nm in (("ykey", "event study key reviews"), ("y", "event study all reviews")):
    m = pf.fepois(f"{out} ~ " + " + ".join(es) + " | appid + ym", data=P, vcov={"CRV1": "appid"}); res[nm] = {k: dict(b=float(m.coef()[k]), se=float(m.se()[k]), p=float(m.pvalue()[k])) for k in es}
# placebo
gp = exposure(A, "2014-03", "2015-08", "2015-01"); Pp = panel(A, gp, "2014-03", "2016-08", "2015-10", skip="2015-09")
for out, nm in (("ykey", "placebo key reviews"), ("y", "placebo all reviews")):
    m = pf.fepois(f"{out} ~ K10Post | appid + ym", data=Pp, vcov={"CRV1": "appid"}); res[nm] = tidy(m, "K10Post")
Pps = Pp.dropna(subset=["share"]); m = pf.feols("share ~ K10Post | appid + ym", data=Pps, weights="y", vcov={"CRV1": "appid"}); res["placebo positive share"] = tidy(m, "K10Post"); res["n_placebo_games"] = int(len(gp))
# english only
Ae = A[A.en == 1]; ge = exposure(Ae, "2015-01", "2016-08", "2016-01"); Pe = panel(Ae, ge, "2015-01", "2017-12", POL, skip="2016-09")
for out, nm in (("ykey", "english key reviews"), ("y", "english all reviews")):
    m = pf.fepois(f"{out} ~ K10Post | appid + ym", data=Pe, vcov={"CRV1": "appid"}); res[nm] = tidy(m, "K10Post")
# alternative exposure: received_for_free
gr = exposure(A, "2015-01", "2016-08", "2016-01", kind="rff"); Pr = panel(A, gr, "2015-01", "2017-12", POL, skip="2016-09")
for out, nm in (("ykey", "rff exposure key reviews"), ("y", "rff exposure all reviews")):
    m = pf.fepois(f"{out} ~ K10Post | appid + ym", data=Pr, vcov={"CRV1": "appid"}); res[nm] = tidy(m, "K10Post")
# drop top 5% volume; wider window
vol = g.n; keep = vol[vol <= vol.quantile(0.95)].index; m = pf.fepois("ykey ~ K10Post | appid + ym", data=P[P.appid.isin(keep)], vcov={"CRV1": "appid"}); res["drop top5% key reviews"] = tidy(m, "K10Post")
P2 = panel(A, g, "2015-01", "2018-12", POL, skip="2016-09"); m = pf.fepois("ykey ~ K10Post | appid + ym", data=P2, vcov={"CRV1": "appid"}); res["window 2018 key reviews"] = tidy(m, "K10Post")
json.dump(res, open("results_steam.json", "w"), indent=1)
for k, v in res.items():
    if k.startswith("event"): print(k); [print("  ", a_, round(b["b"], 3), round(b["se"], 3), round(b["p"], 3)) for a_, b in v.items()]
    elif k in ("monthly_totals_2015_2018",): continue
    else: print(k, v if not isinstance(v, dict) else {a_: (round(b["b"], 4), round(b["se"], 4), round(b["p"], 4)) if isinstance(b, dict) and "b" in b else b for a_, b in v.items()})
