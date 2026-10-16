"""Reproduce the Retail II 4-week purchase-count profile (Section 4 of the proposal)."""
import sys
import numpy as np, pandas as pd
import statsmodels.api as sm
from scipy import stats

path = sys.argv[1]
sheets = pd.read_excel(path, sheet_name=None)
df = pd.concat(sheets.values())
df = df.dropna(subset=["Customer ID"])
df = df[~df["Invoice"].astype(str).str.startswith("C")]  # drop cancellations
df["d"] = pd.to_datetime(df["InvoiceDate"]).dt.normalize()
inv = df.drop_duplicates(["Customer ID", "Invoice"])[["Customer ID", "Invoice", "d"]]
first = inv.groupby("Customer ID")["d"].min()
start = inv["d"].min()
cohort = first[first < start + pd.Timedelta(days=91)].index
inv = inv[inv["Customer ID"].isin(cohort)]
print("cohort size", len(cohort))

for k in range(1, 8):  # 7 consecutive 4-week windows after first purchase
    lo, hi = 28 * k, 28 * (k + 1)
    rel = (inv["d"] - inv["Customer ID"].map(first)).dt.days
    cnt = inv[(rel >= lo) & (rel < hi)].groupby("Customer ID").size().reindex(cohort, fill_value=0)
    m, v = cnt.mean(), cnt.var()
    alpha = (v - m) / m**2
    # Cameron-Trivedi aux regression for overdispersion
    mu = np.full(len(cnt), m)
    aux = ((cnt - mu) ** 2 - cnt) / mu
    t = sm.OLS(aux, np.ones(len(cnt))).fit()
    print(f"win{k}: mean={m:.2f} zero={np.mean(cnt==0):.2f} v/m={v/m:.2f} alpha={alpha:.2f} CT_p={float(np.asarray(t.pvalues)[0]):.3g}")
