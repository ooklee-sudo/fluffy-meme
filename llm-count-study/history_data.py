"""Household histories for the history-persona experiment (Complete Journey).

Provides, for every household h and every 4-week window t (13 windows in 2017):
  counts[h, t]            basket count in window t
  recency[h, t]           days from the last basket before window t to the start of window t (None if no earlier basket)
  cats[h][t]              Counter of product categories bought in window t (needs products.parquet)
Real data: parquet files of the `completejourney_py` package (or $JOURNEY_DATA_DIR). `mock=True` builds a small synthetic
data set with the same structure so that the pipeline can be tested without the real data.
"""
import os
from collections import Counter
import numpy as np, pandas as pd

WIN = 28


def _mock(seed=0, n=120):
    rng = np.random.default_rng(seed)
    demo = pd.DataFrame({
        "household_id": np.arange(n), "age": rng.choice(["25-34", "35-44", "45-54", "55-64"], n),
        "household_comp": rng.choice(["Single Female", "Single Male", "2 Adults No Kids", "2 Adults Kids"], n),
        "household_size": rng.choice(["1", "2", "3", "4"], n), "kids_count": rng.choice(["0", "1", "2"], n),
        "marital_status": rng.choice(["Married", "Unmarried"], n), "income": rng.choice(["25-34K", "50-74K", "100-124K"], n),
        "home_ownership": rng.choice(["Homeowner", "Renter"], n)})
    lam = rng.gamma(1.4, 6 / 1.4, n)  # latent household rate per window
    days = [np.sort(rng.integers(0, 364, rng.poisson(lam.mean() * 0 + l * 13))) for l in lam]
    cats_all = ["milk", "bread", "cheese", "soda", "cereal", "produce", "frozen pizza", "snacks"]
    counts = np.zeros((n, 13), int); recency = np.full((n, 13), np.nan); cats = []
    for h in range(n):
        d = days[h]; c = [Counter() for _ in range(13)]
        for x in d:
            counts[h, x // WIN] += 1; c[x // WIN][rng.choice(cats_all, p=np.roll([.3, .2, .1, .1, .1, .1, .05, .05], h % 8))] += 1
        for t in range(13):
            prev = d[d < t * WIN]
            recency[h, t] = t * WIN - prev.max() if len(prev) else np.nan
        cats.append(c)
    return demo, counts, recency, cats


def load(mock=False):
    if mock:
        return _mock()
    d = os.environ.get("JOURNEY_DATA_DIR")
    if not d:
        import completejourney_py
        d = os.path.join(os.path.dirname(completejourney_py.__file__), "data")
    t = pd.read_parquet(os.path.join(d, "transactions.parquet"))
    demo = pd.read_parquet(os.path.join(d, "demographics.parquet")).reset_index(drop=True)
    day = (t.transaction_timestamp.dt.normalize() - pd.Timestamp("2017-01-01")).dt.days
    t = t.assign(day=day)
    t = t[(t.day >= 0) & (t.day < 364)]
    hh = demo.household_id.values; idx = {h: i for i, h in enumerate(hh)}
    b = t.drop_duplicates(["household_id", "basket_id"])[["household_id", "day"]]
    b = b[b.household_id.isin(idx)]
    counts = np.zeros((len(hh), 13), int); recency = np.full((len(hh), 13), np.nan)
    for h, g in b.groupby("household_id"):
        dd = np.sort(g.day.values); i = idx[h]
        for w in range(13):
            counts[i, w] = ((dd >= w * WIN) & (dd < (w + 1) * WIN)).sum()
            prev = dd[dd < w * WIN]
            recency[i, w] = w * WIN - prev.max() if len(prev) else np.nan
    cats = [[Counter() for _ in range(13)] for _ in hh]
    pp = os.path.join(d, "products.parquet")
    if os.path.exists(pp):
        p = pd.read_parquet(pp)
        col = next((c for c in ("product_category", "commodity_desc", "department") if c in p.columns), None)
        if col:
            m = t[t.household_id.isin(idx)].merge(p[["product_id", col]], on="product_id", how="left")
            m["win"] = m.day // WIN
            for (h, w), g in m.groupby(["household_id", "win"]):
                cats[idx[h]][int(w)].update(g[col].dropna().astype(str).str.lower())
    return demo, counts, recency, cats
