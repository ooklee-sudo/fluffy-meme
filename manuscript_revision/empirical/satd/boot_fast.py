import numpy as np, pandas as pd, scipy.sparse as sp
rng = np.random.default_rng(5)
a = pd.read_parquet("/tmp/satd/agent_rows.parquet"); h = pd.read_parquet("/tmp/satd/human_rows.parquet")
h["lang"] = h.lang.str.lower(); a = a[a.pr_user != "tamnd"]; a["repo"] = a.repo_url
for d in (a, h): d["smell"] = d.long + d.dup + d.broad + d.suppress
L = sorted(set(a.lang) & set(h.lang)); a, h = a[a.lang.isin(L)].copy(), h[h.lang.isin(L)].copy()
bins = [0, 5, 20, 50, 150, 500, 10**9]; lab = ["1-5", "6-20", "21-50", "51-150", "151-500", ">500"]
for d in (a, h): d["cell"] = d.lang + "|" + pd.cut(d.added, bins, labels=lab).astype(str)
MET = ["added", "strict", "wide", "long", "dup", "broad", "suppress", "smell"]
cells = sorted(set(a.cell) & set(h.cell)); cidx = {c: i for i, c in enumerate(cells)}; nc, nm = len(cells), len(MET)
def mat(d):
    d = d[d.cell.isin(cidx)]; repos = pd.factorize(d.repo)[0]; r = repos.max() + 1
    M = [sp.csr_matrix((d[m].values.astype(float), (repos, d.cell.map(cidx).values)), shape=(r, nc)) for m in MET]
    return sp.hstack(M).tocsr(), r        # columns: metric-major, then cell
Ma, ra = mat(a); Mh, rh = mat(h)
# weights: agent added-line share per cell (fixed to the point-estimate sample, as in the stratified estimate)
tot_a = np.asarray(Ma.sum(axis=0)).ravel().reshape(nm, nc); w = tot_a[0] / tot_a[0].sum()
def est(Ma_t, Mh_t):
    ta, th = Ma_t.reshape(nm, nc), Mh_t.reshape(nm, nc)
    out = {}
    for k, m in enumerate(MET[1:], start=1):
        ra_ = 1000 * np.divide(ta[k], ta[0], out=np.zeros(nc), where=ta[0] > 0); rh_ = 1000 * np.divide(th[k], th[0], out=np.zeros(nc), where=th[0] > 0)
        out[m] = ((ra_ * w).sum(), (rh_ * w).sum())
    return out
def stat(o): 
    return dict(marker=o["strict"][0] / o["strict"][1], smell=o["smell"][0] / o["smell"][1], per_smell=(o["strict"][0] / o["smell"][0]) / (o["strict"][1] / o["smell"][1]),
                smell_nodup=((o["long"][0]+o["broad"][0]+o["suppress"][0]) / (o["long"][1]+o["broad"][1]+o["suppress"][1])))
pt = stat(est(np.asarray(Ma.sum(axis=0)).ravel(), np.asarray(Mh.sum(axis=0)).ravel()))
B = []
for _ in range(1000):
    ca = np.bincount(rng.integers(0, ra, ra), minlength=ra); ch = np.bincount(rng.integers(0, rh, rh), minlength=rh)
    B.append(stat(est(np.asarray(Ma.T @ ca).ravel(), np.asarray(Mh.T @ ch).ravel())))
B = pd.DataFrame(B); lo, hi = B.quantile(.025), B.quantile(.975)
print(f"cells {nc}; agent repos {ra:,}; human repos {rh:,}; 1000 repository-level bootstrap draws")
print("ratio agent/human, language x patch-size standardised:")
for k in pt: print(f"  {k:10s} {pt[k]:.2f}  [95% CI {lo[k]:.2f}, {hi[k]:.2f}]")
