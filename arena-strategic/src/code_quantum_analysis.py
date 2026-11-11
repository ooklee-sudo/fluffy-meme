"""Analysis as preregistered in prereg/code_quantum_prereg.md."""
import numpy as np, pandas as pd
d = pd.read_pickle('/home/user/data/code_quantum.pkl'); rng = np.random.default_rng(0); NB = 2000
def boot(df, stat):
    items = df.item.unique(); g = {k: v for k, v in df.groupby('item')}
    return np.array([stat(pd.concat([g[k] for k in rng.choice(items, len(items))])) for _ in range(NB)])
def pooled_mean(df, col):   # equal-weight mean over label mappings
    return np.mean([g[col].mean() for _, g in df.groupby('map')]) if 'map' in df and df['map'].notna().any() else df[col].mean()
E1, E2, E3 = d[d.exp == 'E1'], d[d.exp == 'E2'], d[d.exp == 'E3']
print('E1 SURE-THING / TOTAL PROBABILITY: P(approve) by condition (pooled over label mappings)')
for (m, lab), g in [((m, 'all'), g) for m, g in E1.groupby('model')] + [((m, l), g) for (m, l), g in E1.groupby(['model', 'label'])]:
    P = {c: pooled_mean(g[g.cond == c], 'approve') for c in 'PFU'}
    lo_, hi_ = min(P['P'], P['F']), max(P['P'], P['F'])
    bs = boot(g, lambda x: pooled_mean(x[x.cond == 'U'], 'approve') - min(pooled_mean(x[x.cond == 'P'], 'approve'), pooled_mean(x[x.cond == 'F'], 'approve')))
    bs2 = boot(g, lambda x: pooled_mean(x[x.cond == 'U'], 'approve') - max(pooled_mean(x[x.cond == 'P'], 'approve'), pooled_mean(x[x.cond == 'F'], 'approve')))
    below = np.percentile(bs, 97.5) < 0; above = np.percentile(bs2, 2.5) > 0
    by_map = {mp: {c: round(float(gm[gm.cond == c].approve.mean()), 3) for c in 'PFU'} for mp, gm in g.groupby('map')}
    degenerate = all(v < .05 or v > .95 for v in P.values())
    # item-level sure-thing violations: approve (majority over reps and mappings) under P and F but not under U
    it = g.pivot_table(index='item', columns='cond', values='approve', aggfunc='mean')
    stv = ((it.get('P', 0) > .5) & (it.get('F', 0) > .5) & (it.get('U', 1) < .5)).mean()
    print(f"  {m:8s} {lab:7s} P={P['P']:.3f} F={P['F']:.3f} U={P['U']:.3f}  U-min 95%CI [{np.percentile(bs,2.5):+.3f},{np.percentile(bs,97.5):+.3f}]  "
          f"VIOLATION={'below' if below else 'above' if above else 'none'}  degenerate={degenerate}  item-level STP violations={stv:.3f}  by map={by_map}")
print('\nE2 INTERFERENCE: P_direct(approve) - P_indirect(approve) (pooled over mappings)')
for key, g in [((m, 'all'), g) for m, g in E2.groupby('model')] + [((m, l), g) for (m, l), g in E2.groupby(['model', 'label'])]:
    f = lambda x: pooled_mean(x[x.cond == 'direct'], 'approve') - pooled_mean(x[x.cond == 'indirect'], 'approve')
    v = f(g); bs = boot(g, f); lo, hi = np.percentile(bs, [2.5, 97.5])
    by_map = {mp: round(float(gm[gm.cond == 'direct'].approve.mean() - gm[gm.cond == 'indirect'].approve.mean()), 3) for mp, gm in g.groupby('map')}
    pd_, pi_ = pooled_mean(g[g.cond == 'direct'], 'approve'), pooled_mean(g[g.cond == 'indirect'], 'approve')
    print(f"  {key[0]:8s} {key[1]:7s} direct={pd_:.3f} indirect={pi_:.3f} interference={v:+.3f} 95%CI [{lo:+.3f},{hi:+.3f}] {'NONZERO' if (lo > 0 or hi < 0) else 'n.s.'}  by map={by_map}")
print('\nE3 CONJUNCTION FALLACY: share choosing the conjunction (pooled over option orders)')
for key, g in [((m, 'all'), g) for m, g in E3.groupby('model')] + [((m, l), g) for (m, l), g in E3.groupby(['model', 'label'])]:
    f = lambda x: np.mean([gg.conj.mean() for _, gg in x.groupby('order')]); v = f(g); bs = boot(g, f); lo, hi = np.percentile(bs, [2.5, 97.5])
    by_ord = g.groupby('order').conj.mean().round(3).to_dict()
    print(f"  {key[0]:8s} {key[1]:7s} conjunction rate={v:.3f} 95%CI [{lo:.3f},{hi:.3f}]  by option order={by_ord}  n={len(g)}")
