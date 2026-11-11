import numpy as np, pandas as pd
from scipy.optimize import minimize
D = '/home/user/data'
d = pd.read_pickle(f'{D}/qq_llm.pkl')
rng = np.random.default_rng(0)
def stats(g):
    qb, bq = g[g.order == 'QB'], g[g.order == 'BQ']
    CQ = qb.Q.mean() - bq.Q.mean(); CB = qb.B.mean() - bq.B.mean()
    q = (qb.Q != qb.B).mean() - (bq.Q != bq.B).mean()
    return CQ, CB, q
def boot(g, B=1000):
    items = g.item.unique(); gi = {k: v for k, v in g.groupby('item')}
    res = []
    for _ in range(B):
        s = pd.concat([gi[k] for k in rng.choice(items, len(items))]); res.append(stats(s))
    return np.array(res)
def fit_models(g):
    """2D real Hilbert space quantum model vs classical joint (no order effect), pooled cell counts."""
    cnt = {o: np.array([((g.order == o) & (g.Q == a) & (g.B == b)).sum() for a in (1, 0) for b in (1, 0)]) for o in ('QB', 'BQ')}
    def qprobs(p):
        th, a, b = p
        pQ = lambda s: np.cos(s - a) ** 2  # P(Q yes) from state angle s
        PQ = [np.cos(th - a) ** 2, np.sin(th - a) ** 2]; PB_Q = [np.cos(a - b) ** 2, np.sin(a - b) ** 2]
        qb = np.array([PQ[0] * PB_Q[0], PQ[0] * PB_Q[1], PQ[1] * PB_Q[1], PQ[1] * PB_Q[0]])  # (Qy,By),(Qy,Bn),(Qn,By),(Qn,Bn)
        PB = [np.cos(th - b) ** 2, np.sin(th - b) ** 2]
        bq = np.array([PB[0] * PB_Q[0], PB[1] * PB_Q[1], PB[0] * PB_Q[1], PB[1] * PB_Q[0]])  # same (Q,B) cell order
        return qb, bq
    def ll(pr, c): pr = np.clip(pr, 1e-9, 1); return (c * np.log(pr)).sum()
    nq = lambda p: -sum(ll(x, cnt[o]) for x, o in zip(qprobs(p), ('QB', 'BQ')))
    best = min((minimize(nq, x0, method='Nelder-Mead') for x0 in rng.uniform(0, np.pi, (20, 3))), key=lambda r: r.fun)
    pooled = cnt['QB'] + cnt['BQ']; pc = pooled / pooled.sum()
    llc = ll(pc, cnt['QB']) + ll(pc, cnt['BQ'])
    lls = sum(ll(cnt[o] / cnt[o].sum(), cnt[o]) for o in ('QB', 'BQ'))
    n = pooled.sum()
    return {'BIC_quantum(3)': 2 * best.fun + 3 * np.log(n), 'BIC_classical(3)': -2 * llc + 3 * np.log(n), 'BIC_saturated(6)': -2 * lls + 6 * np.log(n)}
rows = []
for (m, disc), g in d.groupby(['model', 'disc']):
    CQ, CB, q = stats(g); bs = boot(g)
    lo, hi = np.percentile(bs, [5, 95], axis=0)       # 90% CI -> TOST at 5%
    se = bs.std(0)
    f = fit_models(g)
    rows.append(dict(model=m, disclosure=['none', 'brand'][disc], n=len(g), C_Q=CQ, C_Q_se=se[0], C_B=CB, C_B_se=se[1],
                     QQ_q=q, QQ_90ci=f'[{lo[2]:+.3f}, {hi[2]:+.3f}]', QQ_equiv_0p05=bool(lo[2] > -0.05 and hi[2] < 0.05), **{k: round(v, 1) for k, v in f.items()}))
R = pd.DataFrame(rows); pd.set_option('display.width', 250); pd.set_option('display.max_columns', 30)
print(R.round(3).to_string(index=False))
# disclosure penalty, quality question asked first (no contamination by the brand question)
print('\nDisclosure penalty: P(focal judged better), quality asked first')
qb = d[d.order == 'QB']
for m, g in qb.groupby('model'):
    base = g[g.disc == 0].groupby('item').Q.mean(); dis = g[g.disc == 1].groupby('item').Q.mean()
    j = pd.concat([base, dis], axis=1, keys=['b', 'd']).dropna(); diff = j.d - j.b
    br = g[g.disc == 1].merge(g[g.disc == 0][['item', 'Q']], on='item', suffixes=('', '0'))
    by = br.assign(dlt=br.Q - br.Q0).groupby('brand').dlt.agg(['mean', 'count'])
    print(f'  {m:6s} none={j.b.mean():.3f} brand={j.d.mean():.3f}  penalty={diff.mean():+.3f} (se {diff.std() / np.sqrt(len(diff)):.3f})  by brand: ' + ', '.join(f'{k} {v["mean"]:+.2f}(n={int(v["count"])})' for k, v in by.iterrows()))
R.to_csv('/home/user/fluffy-meme/arena-strategic/results/qq_llm_summary.csv', index=False)
