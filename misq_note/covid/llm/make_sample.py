"""Yelp LLM sample as pre-registered in ANALYSIS_PLAN_ADDENDUM_LLM.md. Usage: python make_sample.py YELPDIR"""
import sys, json, random, re
import numpy as np, pandas as pd, pyarrow.parquet as pq
D = sys.argv[1]
r = pd.read_csv(f"{D}/reviews_flags.csv.gz"); r["ym"] = r.date.str.slice(0, 7); b = pd.read_csv(f"{D}/business_flags.csv.gz").set_index("business_id")
p = r[(r.ym >= "2018-03") & (r.ym <= "2020-02")]; g = p.groupby("business_id").agg(n=("tk", "size"), T=("tk", "mean")); g = g[g.n >= 10].copy()
g["tercile"] = pd.qcut(g["T"].rank(method="first"), 3, labels=["Low", "Mid", "High"]); print(g.tercile.value_counts().to_dict())
r = r.reset_index().rename(columns={"index": "row"}); r = r[r.business_id.isin(g.index)].merge(g[["tercile"]], left_on="business_id", right_index=True)
r["period"] = np.where((r.ym >= "2019-03") & (r.ym <= "2020-02"), "Pre", np.where((r.ym >= "2020-03") & (r.ym <= "2021-02"), "Post", "x")); r = r[r.period != "x"]
rng = np.random.RandomState(20261020); picks = []
for (t, per), c in r.groupby(["tercile", "period"]):
    c = c.iloc[rng.permutation(len(c))]; c = c.assign(k=c.groupby("business_id").cumcount()); c = c[c.k < 5]; picks.append(c.iloc[:3300])      # at most 5 per restaurant per cell
S = pd.concat(picks).reset_index(drop=True); S["rid"] = np.arange(len(S)); print(len(S), S.groupby(["tercile", "period"]).size().to_dict())
S[["rid", "business_id", "date", "stars", "tercile", "period", "tk", "cv"]].assign(state=S.business_id.map(b.state)).to_csv("sample_meta.csv", index=False)
need = set(zip(S.business_id, S.date)); txt = {}
f = pq.ParquetFile(f"{D}/review.parquet")
for batch in f.iter_batches(batch_size=250000, columns=["business_id", "date", "text"]):
    d = batch.to_pandas(); d["date"] = pd.to_datetime(d.date).dt.strftime("%Y-%m-%d"); d = d[d.business_id.isin(set(S.business_id))]
    for bid, dt, tx in zip(d.business_id, d.date, d.text):
        if (bid, dt) in need and (bid, dt) not in txt: txt[(bid, dt)] = tx[:1500]
S["text"] = [txt.get((a, c), "") for a, c in zip(S.business_id, S.date)]; print("missing text", int((S.text == "").sum()))
import os; os.makedirs("batches", exist_ok=True); os.makedirs("val", exist_ok=True); os.makedirs("out", exist_ok=True)
N = 150; nb = (len(S) + N - 1) // N
S = S.sample(frac=1, random_state=20261021).reset_index(drop=True); S["rid"] = np.arange(len(S))                        # shuffle so batches mix cells
S[["rid", "business_id", "date", "stars", "tercile", "period", "tk", "cv"]].assign(state=S.business_id.map(b.state)).to_csv("sample_meta.csv", index=False)
for k in range(nb): json.dump([{"rid": int(x.rid), "text": x.text} for x in S.iloc[k * N:(k + 1) * N].itertuples()], open(f"batches/batch_{k:03d}.json", "w"), ensure_ascii=False)
ids = sorted(random.Random(20261022).sample(range(len(S)), 400)); json.dump(ids, open("val_ids.json", "w")); V = S.set_index("rid").loc[ids]
for k in range(8): json.dump([{"rid": int(i), "text": row.text} for i, row in V.iloc[k * 50:(k + 1) * 50].iterrows()], open(f"val/val_{k}.json", "w"), ensure_ascii=False)
print("batches", nb)
