"""Coder-visible batches: text only. batches/ = all reviews (150 each); val/ = random 400 (50 each) for the second coder."""
import json, random, pandas as pd
t = pd.read_json("sample_text.jsonl", lines=True)
N = 150; nb = (len(t) + N - 1) // N
for b in range(nb):
    c = t.iloc[b * N:(b + 1) * N]; json.dump([{"rid": int(r.rid), "text": r.text} for r in c.itertuples()], open(f"batches/batch_{b:03d}.json", "w"), ensure_ascii=False)
ids = sorted(random.Random(20261015).sample(range(len(t)), 400)); json.dump(ids, open("val_ids.json", "w"))
v = t.set_index("rid").loc[ids]
for b in range(8):
    c = v.iloc[b * 50:(b + 1) * 50]; json.dump([{"rid": int(i), "text": r.text} for i, r in c.iterrows()], open(f"val/val_{b}.json", "w"), ensure_ascii=False)
print(nb, len(ids))
