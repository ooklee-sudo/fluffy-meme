"""Analysis as preregistered in prereg/code_quantum_prereg.md (vectorized item bootstrap, 2,000 resamples)."""
import numpy as np, pandas as pd
d = pd.read_pickle('/home/user/data/code_quantum.pkl'); NB = 2000; rng = np.random.default_rng(0)
def tables(g, keys, col):
    """per-item sums and counts for each key combination -> arrays [items x keys]"""
    items = np.sort(g.item.unique()); idx = {k: i for i, k in enumerate(items)}
    S = {}; N = {}
    for key, gg in g.groupby(keys):
        s = np.zeros(len(items)); n = np.zeros(len(items))
        agg = gg.groupby('item')[col].agg(['sum', 'count'])
        for it, row in agg.iterrows(): s[idx[it]] = row['sum']; n[idx[it]] = row['count']
        key = key[0] if isinstance(key, tuple) and len(key) == 1 else key
        S[key] = s; N[key] = n
    return items, S, N
def boot_idx(n): return rng.integers(0, n, size=(NB, n))
def pooled(S, N, cond, maps, B=None):
    """equal-weight mean over label mappings of the approve rate in `cond`; B = bootstrap index matrix or None"""
    vals = []
    for mp in maps:
        s, n = S[(cond, mp)], N[(cond, mp)]
        vals.append(s.sum() / n.sum() if B is None else s[B].sum(1) / n[B].sum(1))
    return np.mean(vals, axis=0)
def ci(x): return np.percentile(x, [2.5, 97.5])
groups = lambda E: [((m, 'all'), g) for m, g in E.groupby('model')] + [((m, l), g) for (m, l), g in E.groupby(['model', 'label'])]
E1, E2, E3 = d[d.exp == 'E1'], d[d.exp == 'E2'], d[d.exp == 'E3']
print('E1 SURE-THING / TOTAL PROBABILITY: P(approve) by condition, pooled over label mappings')
for (m, lab), g in groups(E1):
    items, S, N = tables(g, ['cond', 'map'], 'approve'); maps = sorted(g['map'].unique()); B = boot_idx(len(items))
    P = {c: pooled(S, N, c, maps) for c in 'PFU'}; Pb = {c: pooled(S, N, c, maps, B) for c in 'PFU'}
    lo_b, hi_b = np.minimum(Pb['P'], Pb['F']), np.maximum(Pb['P'], Pb['F'])
    below = ci(Pb['U'] - lo_b)[1] < 0; above = ci(Pb['U'] - hi_b)[0] > 0
    by_map = {mp: {c: round(float(S[(c, mp)].sum() / N[(c, mp)].sum()), 3) for c in 'PFU'} for mp in maps}
    degenerate = all(v < .05 or v > .95 for v in P.values())
    it = g.pivot_table(index='item', columns='cond', values='approve', aggfunc='mean')
    stv = float(((it['P'] > .5) & (it['F'] > .5) & (it['U'] < .5)).mean())
    lo, hi = ci(Pb['U'] - lo_b)
    print(f"  {m:8s} {lab:7s} P={P['P']:.3f} F={P['F']:.3f} U={P['U']:.3f} | U-min(P,F) 95%CI [{lo:+.3f},{hi:+.3f}] | VIOLATION={'below' if below else 'above' if above else 'none'} | degenerate={degenerate} | item-level STP violations={stv:.3f} | {by_map}")
print('\nE2 INTERFERENCE: P_direct(approve) - P_indirect(approve), pooled over mappings')
for (m, lab), g in groups(E2):
    items, S, N = tables(g, ['cond', 'map'], 'approve'); maps = sorted(g['map'].unique()); B = boot_idx(len(items))
    v = pooled(S, N, 'direct', maps) - pooled(S, N, 'indirect', maps); vb = pooled(S, N, 'direct', maps, B) - pooled(S, N, 'indirect', maps, B); lo, hi = ci(vb)
    by_map = {mp: round(float(S[('direct', mp)].sum() / N[('direct', mp)].sum() - S[('indirect', mp)].sum() / N[('indirect', mp)].sum()), 3) for mp in maps}
    print(f"  {m:8s} {lab:7s} direct={pooled(S, N, 'direct', maps):.3f} indirect={pooled(S, N, 'indirect', maps):.3f} interference={v:+.3f} 95%CI [{lo:+.3f},{hi:+.3f}] {'NONZERO' if (lo > 0 or hi < 0) else 'n.s.'} | by map {by_map}")
print('\nE3 CONJUNCTION FALLACY: share choosing the conjunction, pooled over option orders')
for (m, lab), g in groups(E3):
    items, S, N = tables(g, ['order'], 'conj'); orders = sorted(g['order'].unique()); B = boot_idx(len(items))
    v = np.mean([S[o].sum() / N[o].sum() for o in orders]); vb = np.mean([S[o][B].sum(1) / N[o][B].sum(1) for o in orders], axis=0); lo, hi = ci(vb)
    by_ord = {o: round(float(S[o].sum() / N[o].sum()), 3) for o in orders}
    print(f"  {m:8s} {lab:7s} conjunction rate={v:.3f} 95%CI [{lo:.3f},{hi:.3f}] | by option order {by_ord} | n={len(g)}")
