"""Extract restaurant reviews with regex flags (pre-registered patterns). Usage: python prep_yelp.py YELPDIR OUT.csv.gz"""
import sys, re
import numpy as np, pandas as pd, pyarrow.parquet as pq
D, OUT = sys.argv[1], sys.argv[2]
b = pq.read_table(f"{D}/business.parquet", columns=["business_id", "state", "city", "categories"]).to_pandas()
b = b[b.categories.fillna("").str.contains("Restaurants")]
TK = re.compile(r"\b(take[- ]?out|to[- ]?go|carry[- ]?out|delivery|deliver(ed|s)?|drive[- ]?thr(u|ough)|pick[- ]?up)\b", re.I)
CV = re.compile(r"covid|corona|pandemic|\bmask|social distanc|sanitiz|curbside|contactless", re.I)
known = set(b.business_id); parts = []
f = pq.ParquetFile(f"{D}/review.parquet")
for batch in f.iter_batches(batch_size=250000, columns=["business_id", "date", "stars", "text"]):
    d = batch.to_pandas(); d = d[d.business_id.isin(known)]
    t = d.text.fillna("")
    parts.append(pd.DataFrame({"business_id": d.business_id.values, "date": pd.to_datetime(d.date).dt.strftime("%Y-%m-%d").values,
                               "stars": d.stars.values.astype("int8"), "tk": t.str.contains(TK).values.astype("int8"),
                               "cv": t.str.contains(CV).values.astype("int8"), "len": t.str.len().values.astype("int32")}))
r = pd.concat(parts); r.to_csv(OUT, index=False); b.drop(columns="categories").assign(cat=b.categories).to_csv(OUT.replace("reviews", "business"), index=False)
print(len(r), r.business_id.nunique())
