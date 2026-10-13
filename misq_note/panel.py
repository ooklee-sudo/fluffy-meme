"""Product-month panel models (Section: Panel analysis). Usage: python panel.py Consumer_Reviews.csv"""
import sys, json, warnings
import numpy as np, pandas as pd, statsmodels.api as sm, statsmodels.formula.api as smf
warnings.filterwarnings("ignore")
d = pd.read_csv(sys.argv[1], usecols=["id", "name", "brand", "reviews.date", "reviews.rating"], low_memory=False)
d["ym"] = pd.to_datetime(d["reviews.date"], utc=True, format="ISO8601").dt.tz_localize(None).dt.to_period("M")
d["neg"] = (d["reviews.rating"] <= 2).astype(int)
END = d.ym.max(); MINREV = 50
meta = d.groupby("id").agg(name=("name", "first"), brand=("brand", "first"), n=("ym", "size"), first=("ym", "min"))
meta["device"] = (meta.brand == "Amazon").astype(int)
keep = meta[meta.n >= MINREV].index
rows = []
for pid in keep:
    s = d[d.id == pid]; per = pd.period_range(meta.loc[pid, "first"], END, freq="M")
    c = s.groupby("ym").agg(y=("ym", "size"), r=("reviews.rating", "sum"), ng=("neg", "sum")).reindex(per, fill_value=0)
    c["id"] = pid; c["ym"] = per; c["age"] = np.arange(len(per))
    c["cum"] = c.y.cumsum().shift(1).fillna(0); c["cum_r"] = c.r.cumsum().shift(1); c["cum_ng"] = c.ng.cumsum().shift(1)
    c["avg_prev"] = c.cum_r / c.cum.replace(0, np.nan); c["negshare_prev"] = c.cum_ng / c.cum.replace(0, np.nan)
    rows.append(c)
P = pd.concat(rows, ignore_index=True)
P["mo"] = P.ym.astype(str); P["age_y"] = P.age / 12; P["lcum"] = np.log1p(P.cum)
P = P[P.cum > 0].copy()
P = P[P.groupby("mo").y.transform("sum") > 0].copy()      # month FE are not identified where nobody posts (crawl end)                                   # lagged covariates need a prior review
P["avg_prev_c"] = P.avg_prev - 4.5
P["pid"] = pd.factorize(P.id)[0]
out = dict(n_products=int(P.id.nunique()), n_obs=int(len(P)), n_reviews=int(P.y.sum()),
           zero_share=float((P.y == 0).mean()), var_mean=float(P.y.var() / P.y.mean()))
def run(f, nb=False):
    if nb:
        m = smf.glm(f, P, family=sm.families.NegativeBinomial(alpha=ALPHA)).fit(cov_type="cluster", cov_kwds={"groups": P.pid}, maxiter=300)
    else:
        m = smf.glm(f, P, family=sm.families.Poisson()).fit(cov_type="cluster", cov_kwds={"groups": P.pid}, maxiter=300)
    return m
# alpha for NB2 from a Poisson-FE fit by moment (Pearson/df) — plain NB2 with dummies is unstable at this size
base = "y ~ C(id) + C(mo)"
specs = {
  "M1 FE only": base,
  "M2 +social proof": base + " + lcum",
  "M3 +quality": base + " + lcum + avg_prev_c",
  "M4 +neg share": base + " + lcum + negshare_prev",
}
res = {}
for k, f in specs.items():
    m = run(f)
    res[k] = {v: dict(b=float(m.params[v]), se=float(m.bse[v]), p=float(m.pvalues[v])) for v in m.params.index if not v.startswith("C(")}
    mu = m.fittedvalues; res[k]["pearson_disp"] = float(((P.y - mu) ** 2 / mu).sum() / m.df_resid)
    res[k]["n"] = int(m.nobs)
# NB2 check: estimate alpha by regressing ((y-mu)^2 - mu) on mu^2 from M3, refit GLM NB2 with that alpha
m3 = run(specs["M3 +quality"]); mu = m3.fittedvalues
ALPHA = float(((P.y - mu) ** 2 - mu).dot(mu ** 2) / (mu ** 2).dot(mu ** 2)); ALPHA = max(ALPHA, 0.05)
mn = run(specs["M3 +quality"], nb=True)
res["M3-NB2"] = {v: dict(b=float(mn.params[v]), se=float(mn.bse[v]), p=float(mn.pvalues[v])) for v in mn.params.index if not v.startswith("C(")}
res["M3-NB2"]["alpha_used"] = ALPHA
# product heterogeneity: device vs basics growth in cumulative reviews (interaction, month FE only)
P = P.merge(meta[["device"]], left_on="id", right_index=True)
mh = smf.glm("y ~ C(mo) + device + lcum + avg_prev_c", P, family=sm.families.Poisson()).fit(cov_type="cluster", cov_kwds={"groups": P.pid}, maxiter=300)
res["M5 between (no product FE)"] = {v: dict(b=float(mh.params[v]), se=float(mh.bse[v]), p=float(mh.pvalues[v])) for v in ["device", "lcum", "avg_prev_c"]}
out["models"] = res
json.dump(out, open("panel_results.json", "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "models"}, indent=1))
for k, v in res.items():
    print(k); [print("  ", a, {x: round(y, 4) for x, y in b.items()}) for a, b in v.items() if isinstance(b, dict)]
    print("  ", {a: b for a, b in v.items() if not isinstance(b, dict)})
