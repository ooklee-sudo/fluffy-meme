"""Study 3: flag, eligibility, matching, review sampling, coder-visible batches.
Usage: python build_sample.py Appliances.jsonl     (seed fixed; uses only pre-policy data for matching)"""
import sys, json, random
import numpy as np, pandas as pd
from incentive import disclosed
PRE0, POL, POST1 = pd.Timestamp("2014-01-01"), pd.Timestamp("2016-10-01"), pd.Timestamp("2017-10-01")
rows = []
with open(sys.argv[1]) as f:
    for i, l in enumerate(f):
        r = json.loads(l); rows.append((i, r["parent_asin"], r["timestamp"], r["rating"], r["helpful_vote"], r["verified_purchase"], disclosed(r["text"]), len(r["text"])))
d = pd.DataFrame(rows, columns=["row", "pa", "ts", "rating", "hv", "vp", "inc", "len"]); d["t"] = pd.to_datetime(d.ts, unit="ms")
d.drop(columns="t").to_csv("all_reviews_meta.csv.gz", index=False)         # full-category metadata for volume analyses (no text)
pre = d[(d.t >= PRE0) & (d.t < POL)]
g = pre.groupby("pa").agg(n=("inc", "size"), k=("inc", "sum"), first=("t", "min"), r=("rating", "mean"))
el = g[(g.n >= 20) & (g["first"] < pd.Timestamp("2016-07-01"))].copy()
el["ln"] = np.log(el.n); el["fy"] = el["first"].dt.year + el["first"].dt.dayofyear / 366
treated = el[el.k >= 2]; pool = el[el.k == 0]
X = ["ln", "r", "fy"]; icov = np.linalg.inv(np.cov(pool[X].values.T))
order = list(treated.index); random.Random(20261016).shuffle(order); used = set(); pairs = {}
for pa in order:
    c = pool[~pool.index.isin(used)]; diff = c[X].values - treated.loc[pa, X].values.astype(float)
    dist = np.einsum("ij,jk,ik->i", diff, icov, diff); j = int(np.argmin(dist)); pairs[pa] = c.index[j]; used.add(c.index[j])
bal = pd.DataFrame({"treated": treated.loc[list(pairs), X].mean(), "matched_control": pool.loc[list(pairs.values()), X].mean(), "pool_all": pool[X].mean()})
print(bal.round(3)); bal.to_csv("balance_table.csv")
sel = [(pa, 1) for pa in pairs] + [(c, 0) for c in pairs.values()]; rng = np.random.RandomState(20261017); pick = []
w = d[(d.t >= pd.Timestamp("2016-01-01")) & (d.t < POST1) & (~d.inc)]
for pa, tr in sel:
    x = w[w.pa == pa]
    for post, part in ((0, x[x.t < POL]), (1, x[x.t >= POL])):
        if len(part): pick.append(part.iloc[rng.permutation(len(part))[:40]].assign(treated=tr, post=post))
s = pd.concat(pick).sort_values(["pa", "ts"]).reset_index(drop=True); s["rid"] = np.arange(len(s))
pair_of = {**{a: a for a in pairs}, **{c: a for a, c in pairs.items()}}; s["pair"] = s.pa.map(pair_of)
print(len(s), "reviews;", s.pa.nunique(), "products;", s.groupby("treated").size().to_dict(), s.groupby(["treated", "post"]).size().to_dict())
s[["rid", "row", "pa", "pair", "treated", "post", "ts", "rating", "hv", "vp", "len"]].to_csv("sample_meta.csv", index=False)
need = set(s.row); txt = {}
with open(sys.argv[1]) as f:
    for i, l in enumerate(f):
        if i in need: txt[i] = json.loads(l)["text"][:1500]
t = pd.DataFrame({"rid": s.rid, "text": s.row.map(txt)}); t.to_json("sample_text.jsonl", orient="records", lines=True, force_ascii=False)
import os; os.makedirs("batches", exist_ok=True); os.makedirs("val", exist_ok=True); os.makedirs("out", exist_ok=True)
N = 150; nb = (len(t) + N - 1) // N
for b in range(nb): json.dump([{"rid": int(r.rid), "text": r.text} for r in t.iloc[b * N:(b + 1) * N].itertuples()], open(f"batches/batch_{b:03d}.json", "w"), ensure_ascii=False)
ids = sorted(random.Random(20261018).sample(range(len(t)), 400)); json.dump(ids, open("val_ids.json", "w")); v = t.set_index("rid").loc[ids]
for b in range(8): json.dump([{"rid": int(i), "text": r.text} for i, r in v.iloc[b * 50:(b + 1) * 50].iterrows()], open(f"val/val_{b}.json", "w"), ensure_ascii=False)
print("batches", nb)
