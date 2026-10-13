"""Study-2 panel models, as pre-specified in ANALYSIS_PLAN.md. Usage: python analysis_panel.py
Reads sample_meta.csv and out/H_*.csv."""
import glob, json, warnings
import numpy as np, pandas as pd, statsmodels.api as sm, statsmodels.formula.api as smf
warnings.filterwarnings("ignore")
COLS = ["rid", "overall", "defect", "price", "durability", "performance", "fit", "ease", "design", "service"]
code = pd.concat([pd.read_csv(f, header=None, names=COLS) for f in sorted(glob.glob("out/H_*.csv"))]).drop_duplicates("rid")
meta = pd.read_csv("sample_meta.csv").merge(code, on="rid", how="inner")
meta["ym"] = pd.to_datetime(meta.ts, unit="ms").dt.to_period("M")
meta["v_defect"] = meta.defect; meta["v_perfpos"] = (meta.performance == 1).astype(int); meta["v_priceneg"] = (meta.price == -1).astype(int)
meta["v_durneg"] = (meta.durability == -1).astype(int); meta["v_fitneg"] = (meta.fit == -1).astype(int); meta["v_svcneg"] = (meta.service == -1).astype(int)
meta["v_easepos"] = (meta.ease == 1).astype(int); meta["v_neg"] = (meta.overall == "neg").astype(int)
V = ["v_defect", "v_perfpos", "v_priceneg", "v_durneg", "v_fitneg", "v_svcneg", "v_easepos", "v_neg"]
END = pd.Period("2023-08", "M")
rows = []
for pid, s in meta.groupby("pa"):
    per = pd.period_range(s.ym.min(), END, freq="M")
    g = s.groupby("ym").agg(y=("rid", "size"), rs=("rating", "sum"), **{v: (v, "sum") for v in V}).reindex(per, fill_value=0)
    g["pa"] = pid; g["mo"] = per.astype(str)
    for lag in (1, 0, -2):                                   # cum through t-1 (main); through t (lead 1); through t+2 (lead 3)
        sh = 1 - lag                                         # shift
        n = g.y.cumsum().shift(sh); g[f"n_{lag}"] = n; g[f"avg_{lag}"] = g.rs.cumsum().shift(sh) / n
        for v in V: g[f"{v}_{lag}"] = g[v].cumsum().shift(sh) / n
    for w in (6, 12):                                        # windowed shares over months t-w..t-1
        n = g.y.rolling(w).sum().shift(1)
        for v in V: g[f"{v}_w{w}"] = g[v].rolling(w).sum().shift(1) / n
        g[f"n_w{w}"] = n
    rows.append(g.reset_index(drop=True))
P = pd.concat(rows, ignore_index=True)
P["pid"] = pd.factorize(P.pa)[0]; P["lcum"] = np.log1p(P["n_1"]); P["avg_c"] = P["avg_1"] - 4.5
P = P[P["n_1"] > 0]; P = P[P.groupby("mo").y.transform("sum") > 0].copy()
out = dict(n_products=int(P.pa.nunique()), n_obs=int(len(P)), n_reviews=int(P.y.sum()), zero_share=float((P.y == 0).mean()),
           coded_reviews=int(len(meta)))
def fit(f, data=None, nb=False):
    data = P if data is None else data
    d = data.dropna(subset=[c for c in data.columns if c in f]) if False else data
    m = smf.glm(f, d, family=sm.families.Poisson()).fit(cov_type="cluster", cov_kwds={"groups": d.pid}, maxiter=200)
    return m
def pack(m, keys): return {k: dict(b=float(m.params[k]), se=float(m.bse[k]), p=float(m.pvalues[k])) for k in keys if k in m.params}
base = "y ~ C(pa) + C(mo)"
prim = ["v_defect_1", "v_perfpos_1", "v_priceneg_1"]
Q = P.dropna(subset=prim + ["avg_c"]).copy()
res = {}
m0 = fit(base + " + lcum + avg_c", Q); res["M0 controls"] = pack(m0, ["lcum", "avg_c"])
m1 = fit(base + " + lcum + avg_c + " + " + ".join(prim), Q); res["M1 primary"] = pack(m1, ["lcum", "avg_c"] + prim)
pv = sorted([(m1.pvalues[k], k) for k in prim]); holm = {}; run = 0.0
for i, (p, k) in enumerate(pv): run = max(run, min(1.0, p * (len(prim) - i))); holm[k] = run
res["M1 primary"]["holm_p"] = holm
exp = [v + "_1" for v in V if v + "_1" not in prim]
m2 = fit(base + " + lcum + avg_c + " + " + ".join(prim + exp), Q.dropna(subset=exp)); res["M2 all aspects (exploratory)"] = pack(m2, prim + exp)
# robustness: placebo leads
Ql = P.dropna(subset=prim + ["avg_c"] + [v + "_0" for v in ("v_defect", "v_perfpos", "v_priceneg")] + [v + "_-2" for v in ("v_defect", "v_perfpos", "v_priceneg")]).copy()
lead = " + ".join([f"{v}_0" for v in ("v_defect", "v_perfpos", "v_priceneg")] + [f"Q('{v}_-2')" for v in ("v_defect", "v_perfpos", "v_priceneg")])
m3 = fit(base + " + lcum + avg_c + " + " + ".join(prim) + " + " + lead, Ql)
res["M3 placebo leads"] = {k: dict(b=float(m3.params[k]), se=float(m3.bse[k]), p=float(m3.pvalues[k])) for k in m3.params.index if k.startswith("v_") or k.startswith("Q(")}
# windowed shares
for w in (6, 12):
    ks = [f"v_defect_w{w}", f"v_perfpos_w{w}", f"v_priceneg_w{w}"]; Qw = P.dropna(subset=ks + ["avg_c"]).copy()
    mw = fit(base + " + lcum + avg_c + " + " + " + ".join(ks), Qw); res[f"M4 window {w}m"] = pack(mw, ks + ["lcum", "avg_c"]); res[f"M4 window {w}m"]["n"] = int(len(Qw))
# drop top decile by volume; drop first 12 months
tot = P.groupby("pa").y.sum(); keep = tot[tot <= tot.quantile(0.9)].index
mt = fit(base + " + lcum + avg_c + " + " + ".join(prim), Q[Q.pa.isin(keep)]); res["M5 drop top10% volume"] = pack(mt, prim + ["lcum"])
first = P.groupby("pa").mo.min(); Q2 = Q.merge(first.rename("m0"), left_on="pa", right_index=True)
Q2 = Q2[pd.PeriodIndex(Q2.mo, freq="M") >= pd.PeriodIndex(Q2.m0, freq="M") + 12]
m6 = fit(base + " + lcum + avg_c + " + " + ".join(prim), Q2); res["M6 drop first 12 months"] = pack(m6, prim + ["lcum"])
res["_n"] = {k: int(m.nobs) for k, m in (("M1", m1), ("M3", m3), ("M5", mt), ("M6", m6))}
out["models"] = res
json.dump(out, open("panel_results.json", "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "models"}))
for k, v in res.items():
    print(k)
    for a, b in v.items(): print("  ", a, {x: (round(y, 4) if isinstance(y, float) else y) for x, y in b.items()} if isinstance(b, dict) else b)
