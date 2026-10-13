"""Write all reviews as blind batches of 150 (text only, truncated to 1500 chars). rid = row index in the CSV."""
import sys, json, pandas as pd
d = pd.read_csv(sys.argv[1], usecols=["reviews.text"], low_memory=False)
t = d["reviews.text"].fillna("").astype(str).str.slice(0, 1500)
N = 150; nb = (len(t) + N - 1) // N
for b in range(nb):
    json.dump([{"rid": int(i), "text": t.iloc[i]} for i in range(b * N, min((b + 1) * N, len(t)))], open(f"full/batch_{b:03d}.json", "w"), ensure_ascii=False)
print(len(t), nb)
