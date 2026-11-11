"""Analysis for prereg/qq_large_models_prereg.md, plus human-benchmark comparison (pooled over label mappings)."""
import sys, numpy as np, pandas as pd
from scipy.stats import norm
sys.path.insert(0, 'src')
from qq_human_replication import HUMAN
CELLS = [(1, 1), (1, 0), (0, 1), (0, 0)]
def cellp(g): return np.array([((g['first'] == a) & (g['second'] == b)).mean() for a, b in CELLS])
def qstat(g):
    a, b = g[g.order == 'AB'], g[g.order == 'BA']; dA, dB = (a['first'] != a['second']).mean(), (b['first'] != b['second']).mean()
    return dA - dB, np.sqrt(dA * (1 - dA) / len(a) + dB * (1 - dB) / len(b))
def run(path, label):
    D = pd.read_pickle(path); rows = []
    for (m, it), g in D.groupby(['model', 'item']):
        r = dict(set=label, model=m, item=it, n=len(g)); qs = []
        for mp, gm in g.groupby('map'):
            q, se = qstat(gm); qs.append((q, se)); r[f'q_{mp}'] = round(q, 3); r[f'p_{mp}'] = float(f'{2 * norm.sf(abs(q) / se):.2g}') if se > 0 else 1.0
        qp = (qs[0][0] + qs[1][0]) / 2; sep = 0.5 * np.sqrt(qs[0][1] ** 2 + qs[1][1] ** 2)
        pp = 2 * norm.sf(abs(qp) / sep) if sep > 0 else 1.0
        r['q_pooled'] = round(qp, 3); r['p_pooled'] = float(f'{pp:.2g}')
        both_hold = all((se == 0) or (2 * norm.sf(abs(q) / se) >= 0.05) for q, se in qs)
        r['QQ_holds_both_mappings'] = bool(both_hold)
        a = np.mean([cellp(gm[gm.order == 'AB']) for _, gm in g.groupby('map')], axis=0); b = np.mean([cellp(gm[gm.order == 'BA']) for _, gm in g.groupby('map')], axis=0)
        r['yesA_first'] = round(a[0] + a[1], 3); r['yesB_first'] = round(b[0] + b[1], 3)
        if it in HUMAN:
            hA, hB = np.array(HUMAN[it]['AB']), np.array(HUMAN[it]['BA'])
            r['TV_vs_human'] = round(0.25 * (np.abs(a - hA).sum() + np.abs(b - hB).sum()), 3)
            r['sign_match'] = int((np.sign(hA - hB) == np.sign(a - b)).sum())
            r['human_QQ'] = 'holds' if it != 'rose_jackson' else 'violated'
        rows.append(r)
    return pd.DataFrame(rows)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 30)
R = pd.concat([run('/home/user/data/cb_study2.pkl', 'small'), run('/home/user/data/cb_study2_large.pkl', 'large')])
print(R.to_string(index=False))
H = R[R['item'].isin(['clinton_gore', 'white_black'])]
print('\nCells on items where QQ holds for humans, holding in BOTH mappings:', H[H.QQ_holds_both_mappings][['set', 'model', 'item']].values.tolist())
print('Mean TV distance to human by model:', R.dropna(subset=['TV_vs_human']).groupby('model').TV_vs_human.mean().round(3).to_dict())
R.to_csv('/home/user/fluffy-meme/arena-strategic/results/qq_human_benchmark_all_models.csv', index=False)
