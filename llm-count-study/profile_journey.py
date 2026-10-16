"""Dunnhumby Complete Journey (via completejourney_py parquet files): 4-week basket counts + campaign IRR.

usage: python profile_journey.py <dir with *.parquet>
Campaign exposure is NOT randomized (targeted mailings): the IRR is an association, adjusted for the
previous window's count, not a causal effect.
"""
import sys, os, warnings
import numpy as np, pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

warnings.filterwarnings("ignore")
d = sys.argv[1]
t = pd.read_parquet(os.path.join(d, "transactions.parquet"))
camp = pd.read_parquet(os.path.join(d, "campaigns.parquet"))
desc = pd.read_parquet(os.path.join(d, "campaign_descriptions.parquet"))
t["day"] = (t.transaction_timestamp.dt.normalize() - pd.Timestamp("2017-01-01")).dt.days
b = t.drop_duplicates(["household_id", "basket_id"])[["household_id", "basket_id", "day"]]
b = b[(b.day >= 0) & (b.day < 364)]
b["win"] = b.day // 28
hh = np.sort(t.household_id.unique())
cnt = (b.groupby(["household_id", "win"]).size().unstack(fill_value=0)
       .reindex(index=hh, columns=range(13), fill_value=0))
print(f"{len(hh)} households, 13 four-week windows (2017)\n")

rows = []
for w in range(13):
    x = cnt[w].values.astype(float); m, v = x.mean(), x.var(ddof=1)
    mu = np.full(len(x), m)
    ct = sm.OLS(((x - mu) ** 2 - x) / mu, np.ones(len(x))).fit()
    X = np.ones((len(x), 1))
    aic_p = sm.Poisson(x, X).fit(disp=0).aic
    try:
        aic_nb = sm.NegativeBinomial(x, X).fit(disp=0).aic
    except Exception:
        aic_nb = np.nan
    rows.append(dict(win=w + 1, mean=m, zero=(x == 0).mean(), var_mean=v / m, alpha=(v - m) / m**2,
                     CT_p=float(np.asarray(ct.pvalues)[0]), best="NB" if aic_nb < aic_p else "Poisson"))
print(pd.DataFrame(rows).round(3).to_string(index=False))

# campaign exposure per window (any campaign active during the window, household targeted)
desc["s"] = (pd.to_datetime(desc.start_date) - pd.Timestamp("2017-01-01")).dt.days
desc["e"] = (pd.to_datetime(desc.end_date) - pd.Timestamp("2017-01-01")).dt.days
cm = camp.merge(desc, on="campaign_id")
long = []
for w in range(1, 13):
    lo, hi = w * 28, w * 28 + 27
    act = cm[(cm.s <= hi) & (cm.e >= lo)].household_id.unique()
    long.append(pd.DataFrame({"hh": hh, "win": w, "y": cnt[w].values,
                              "lag": cnt[w - 1].values, "exposed": np.isin(hh, act).astype(int)}))
L = pd.concat(long)
L["loglag"] = np.log1p(L.lag)
print("\nexposed share by window:", L.groupby("win").exposed.mean().round(2).to_dict())
for f, name in [("y ~ exposed", "unadjusted"), ("y ~ exposed + loglag", "adjusted for log(1+lag count)")]:
    r = smf.glm(f, L, family=sm.families.Poisson()).fit(cov_type="cluster", cov_kwds={"groups": L.hh})
    ci = np.exp(r.conf_int().loc["exposed"])
    print(f"IRR ({name}) = {np.exp(r.params['exposed']):.3f}  [{ci[0]:.3f}, {ci[1]:.3f}]")
