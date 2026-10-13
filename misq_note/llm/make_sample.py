"""Draw the validation sample (seed 20261013) and write blind batches (text only; no rating or product)."""
import sys, json, pandas as pd
d = pd.read_csv(sys.argv[1], usecols=["id", "name", "reviews.date", "reviews.rating", "reviews.text"], low_memory=False)
d = d[d["reviews.text"].fillna("").str.len().between(20, 1500)].reset_index(drop=True)
s = d.sample(400, random_state=20261013).reset_index(drop=True); s["rid"] = ["R%03d" % i for i in range(400)]
s[["rid", "id", "reviews.date", "reviews.rating", "reviews.text"]].to_csv("sample_full.csv", index=False)
for b in range(8):
    chunk = s.iloc[b * 50:(b + 1) * 50]
    json.dump([{"rid": r.rid, "text": r["reviews.text"]} for _, r in chunk.iterrows()], open(f"batch_{b}.json", "w"), ensure_ascii=False, indent=0)
print(s["reviews.rating"].value_counts().sort_index().to_dict(), len(s))
