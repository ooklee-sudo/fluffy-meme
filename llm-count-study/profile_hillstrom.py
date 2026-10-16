"""Hillstrom randomized email test: binary outcomes per arm, risk ratios with bootstrap CIs."""
import sys
import numpy as np, pandas as pd

df = pd.read_csv(sys.argv[1])
rng = np.random.default_rng(0)
print(len(df), "customers; arms:", df.segment.value_counts().to_dict())
ctrl = df[df.segment == "No E-Mail"]
rows = []
for arm in ["Mens E-Mail", "Womens E-Mail"]:
    t = df[df.segment == arm]
    for y in ["visit", "conversion"]:
        pt, pc = t[y].mean(), ctrl[y].mean()
        bs = [rng.choice(t[y].values, len(t)).mean() / rng.choice(ctrl[y].values, len(ctrl)).mean() for _ in range(2000)]
        rows.append(dict(arm=arm, outcome=y, rate_treat=pt, rate_ctrl=pc, rr=pt / pc,
                         lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5)))
print(pd.DataFrame(rows).round(4).to_string(index=False))
print("\nspend (all customers): mean by arm"); print(df.groupby("segment").spend.mean().round(3))
print("\nspend among converters: mean by arm"); print(df[df.conversion == 1].groupby("segment").spend.agg(["count", "mean"]).round(2))
