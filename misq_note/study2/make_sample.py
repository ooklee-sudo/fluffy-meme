"""Draw study sample from the Amazon Reviews 2023 Appliances file. Usage: python make_sample.py Appliances.jsonl"""
import sys, json, pandas as pd, numpy as np
rows = []
with open(sys.argv[1]) as f:
    for i, l in enumerate(f):
        r = json.loads(l); rows.append((i, r["parent_asin"], r["timestamp"], r["rating"], r["helpful_vote"], r["verified_purchase"], r["text"]))
d = pd.DataFrame(rows, columns=["row", "pa", "ts", "rating", "hv", "vp", "text"]); d["t"] = pd.to_datetime(d.ts, unit="ms")
g = d.groupby("pa").agg(n=("row", "size"), first=("t", "min"), last=("t", "max"))
ok = g[(g.n.between(150, 400)) & (g["first"] >= "2013-01-01") & ((g["last"] - g["first"]).dt.days >= 36 * 30.4)]
pick = ok.sample(100, random_state=20261014).index.tolist()
s = d[d.pa.isin(pick)].sort_values(["pa", "ts"]).reset_index(drop=True); s["rid"] = np.arange(len(s))
print(len(ok), "eligible;", len(pick), "products;", len(s), "reviews")
s[["rid", "row", "pa", "ts", "rating", "hv", "vp"]].to_csv("sample_meta.csv", index=False)       # contains ratings: keep out of coder-visible dir
s[["rid", "text"]].assign(text=s.text.str.slice(0, 1500)).to_json("sample_text.jsonl", orient="records", lines=True, force_ascii=False)
