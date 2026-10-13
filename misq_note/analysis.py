"""Reproduces every number and Figure 1 in the research note.
Usage: python analysis.py Consumer_Reviews.csv   (Zenodo 10.5281/zenodo.18758751)
Requires: pandas numpy scipy matplotlib numdifftools
"""
import sys, json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from scipy.optimize import minimize
from scipy.special import gammaln
import numdifftools as nd

d = pd.read_csv(sys.argv[1], usecols=["brand", "name", "reviews.date", "reviews.text"], low_memory=False)
# ISO8601 is required: default format inference silently drops 62 records.
d["ym"] = pd.to_datetime(d["reviews.date"], utc=True, format="ISO8601").dt.tz_localize(None).dt.to_period("M")
idx = pd.period_range(d.ym.min(), d.ym.max(), freq="M")
full = d.groupby("ym").size().reindex(idx, fill_value=0)

def nll_p(b, X, y):
    eta = X @ b
    return (np.exp(eta) - y * eta + gammaln(y + 1)).sum()

def nll_nb(th, X, y):
    b, a = th[:-1], np.exp(th[-1]); r = 1 / a; mu = np.exp(X @ b)
    return -(gammaln(y + r) - gammaln(r) - gammaln(y + 1) + r * np.log(r / (r + mu)) + y * np.log(mu / (r + mu))).sum()

def fit(y, quad, unit=12.0):
    n = len(y); t = np.arange(n) / unit; t = t - t.mean()
    X = np.column_stack([np.ones(n), t] + ([t ** 2] if quad else []))
    k = X.shape[1]; b0 = np.linalg.lstsq(X, np.log(y + 1), rcond=None)[0]
    P = minimize(nll_p, b0, args=(X, y), method="BFGS")
    best = None
    for a0 in (-1.0, 0.0, 1.0):
        r = minimize(nll_nb, np.r_[P.x, a0], args=(X, y), method="Nelder-Mead",
                     options={"maxiter": 60000, "xatol": 1e-9, "fatol": 1e-11, "adaptive": True})
        r = minimize(nll_nb, r.x, args=(X, y), method="BFGS")
        if best is None or r.fun < best.fun: best = r
    se = np.sqrt(np.diag(np.linalg.inv(nd.Hessian(lambda th: nll_nb(th, X, y))(best.x))))
    mu = np.exp(X @ P.x)
    return dict(n=n, k=k, pois_b=P.x.tolist(), pois_aic=2 * P.fun + 2 * k,
                pearson_disp=float(((y - mu) ** 2 / mu).sum() / (n - k)),
                nb_b=best.x[:-1].tolist(), nb_se=se[:-1].tolist(),
                nb_p=(2 * stats.norm.sf(abs(best.x[:-1] / se[:-1]))).tolist(),
                alpha=float(np.exp(best.x[-1])), nb_aic=2 * best.fun + 2 * (k + 1),
                lr=2 * (P.fun - best.fun), nb_mu=np.exp(X @ best.x[:-1]).tolist())

y = full.values.astype(float); act = full["2014-06":]; ya = act.values.astype(float)
res = dict(
    n_reviews=int(len(d)), n_months=len(full), n_zero_months=int((full == 0).sum()),
    n_nonempty=int((full > 0).sum()), peak=int(full.max()), peak_month=str(full.idxmax()),
    var_mean=float(y.var(ddof=1) / y.mean()), var_mean_active=float(ya.var(ddof=1) / ya.mean()),
    by_year=full.groupby(full.index.year).sum().to_dict(),
    full_linear=fit(y, False), active_linear=fit(ya, False), active_quad=fit(ya, True),
)
# per-month trend on the calendar-complete series (the note reports monthly rates)
for key in ("full_linear", "active_linear"):
    r = res[key]; r["pois_b_month"] = r["pois_b"][1] / 12; r["nb_b_month"] = r["nb_b"][1] / 12; r["nb_se_month"] = r["nb_se"][1] / 12
res["brand"] = {g: dict(n=int(len(s)), products=int(s.name.nunique())) for g, s in
                d.assign(g=np.where(d.brand == "Amazon", "Amazon", "AmazonBasics")).groupby("g")}
json.dump(res, open("results.json", "w"), indent=1, default=str)

fig, ax = plt.subplots(figsize=(7.2, 3.2), dpi=200)
x = np.arange(len(full))
ax.bar(x, y, color="#9aa5b1", width=0.85, label="Observed monthly reviews")
off = len(full) - len(act)
ax.plot(x[off:], res["active_quad"]["nb_mu"], color="#c0392b", lw=1.6, label="Negative binomial, quadratic trend (Jun 2014–Mar 2019)")
ticks = [i for i, p in enumerate(full.index) if p.month == 1 and p.year % 2 == 1]
ax.set_xticks(ticks); ax.set_xticklabels([str(full.index[i].year) for i in ticks])
ax.set_ylabel("Reviews per month"); ax.spines[["top", "right"]].set_visible(False)
ax.legend(frameon=False, fontsize=7.5, loc="upper left"); fig.tight_layout(); fig.savefig("figure1.png")
print(json.dumps({k: v for k, v in res.items() if not isinstance(v, dict)}, indent=1, default=str))
for k in ("full_linear", "active_linear", "active_quad"):
    print(k, {a: b for a, b in res[k].items() if a != "nb_mu"})

# Dictionary sentiment rates per 1,000 words (active window), correlation with volume
POS = r"\b(great|good|love|excellent|perfect|best|works well|happy|nice)\b"
NEG = r"\b(bad|poor|broke|broken|terrible|worst|disappoint\w*|waste|return\w*|defective|cheap)\b"
tx = d["reviews.text"].fillna("").str.lower()
g = pd.DataFrame({"ym": d.ym, "pos": tx.str.count(POS), "neg": tx.str.count(NEG), "wc": tx.str.split().str.len()}).groupby("ym").sum()
g = g.loc["2014-06":]; g["n"] = full["2014-06":]; g = g[g.wc > 0]
g["posr"] = g.pos / g.wc * 1000; g["negr"] = g.neg / g.wc * 1000
print("sentiment corr with volume (months=%d): pos %.2f neg %.2f" % (len(g), g.n.corr(g.posr), g.n.corr(g.negr)))
