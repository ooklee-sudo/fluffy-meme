"""Detection rate vs. number of attempts (pass@k style) with a bootstrap over instances.
A(K) in the paper's sense needs the human baseline for the same instances; this gives the tool side only."""
import sys
import numpy as np, pandas as pd
df = pd.read_csv(sys.argv[1])
ok = df[~df.reason.fillna("").str.startswith("harness_error")]
print(f"{len(df)} runs, {len(df)-len(ok)} harness errors excluded, {ok.instance_id.nunique()} instances")
print(ok.groupby("model").agg(runs=("detected", "size"), det=("detected", "mean"), cost=("cost_usd", "sum")).round(3))
rng = np.random.default_rng(0)
for m, g in ok.groupby("model"):
    piv = g.pivot_table(index="instance_id", columns="rep", values="detected", aggfunc="max").fillna(0).values.astype(bool)
    n, R = piv.shape
    print(f"\n{m}: share of instances detected within k attempts")
    for k in range(1, R + 1):
        cur = piv[:, :k].any(axis=1)
        bs = [cur[rng.integers(0, n, n)].mean() for _ in range(2000)]
        print(f"  k={k}: {cur.mean():.2f}  (95% CI {np.percentile(bs,2.5):.2f}-{np.percentile(bs,97.5):.2f}, n={n})")
