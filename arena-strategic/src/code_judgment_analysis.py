"""Analysis as preregistered in arena-strategic/prereg/code_judgment_prereg.md."""
import numpy as np, pandas as pd
from scipy.stats import norm, chi2_contingency
A = pd.read_pickle('/home/user/data/code_A.pkl'); B = pd.read_pickle('/home/user/data/code_B.pkl')
rng = np.random.default_rng(0); NB = 2000
def sdt(g):
    bug, cor = g[g.label == 'buggy'].wrong, g[g.label == 'correct'].wrong
    H = (bug.sum() + 0.5) / (len(bug) + 1); FA = (cor.sum() + 0.5) / (len(cor) + 1)
    return -(norm.ppf(H) + norm.ppf(FA)) / 2, norm.ppf(H) - norm.ppf(FA), FA, 1 - H
print('STUDY A: signal detection (signal = bug present; c < 0 = leans toward "wrong")')
rows = []
for (m, f), g in A.groupby(['model', 'frame']):
    c, dp, fa, miss = sdt(g); items = g.item.unique(); gi = {k: v for k, v in g.groupby('item')}
    bs = np.array([sdt(pd.concat([gi[k] for k in rng.choice(items, len(items))]))[0] for _ in range(NB)])
    lo, hi = np.percentile(bs, [2.5, 97.5])
    rows.append(dict(model=m, frame=f, n=len(g), false_alarm=round(fa, 3), miss=round(miss, 3), d_prime=round(dp, 2), c=round(c, 2), c_95ci=f'[{lo:.2f}, {hi:.2f}]', H1_c_below_0=bool(hi < 0)))
print(pd.DataFrame(rows).to_string(index=False))
print('\nSTUDY A: framing (share judged wrong, F2 "contains a bug?" minus F1 "is it correct?"), one-sided bootstrap')
for (m, lab), g in A.groupby(['model', 'label']):
    w = g.pivot_table(index='item', columns='frame', values='wrong', aggfunc='mean').dropna()
    diff = (w.F2 - w.F1).values; bs = np.array([rng.choice(diff, len(diff)).mean() for _ in range(NB)])
    print(f'  {m:6s} {lab:8s} F1={w.F1.mean():.3f} F2={w.F2.mean():.3f} diff={diff.mean():+.3f}  one-sided p(F2>F1)={(bs <= 0).mean():.4f}')
print('\nSTUDY B: order effects and QQ (Q = correct?, R = well written?)')
CELLS = [(1, 1), (1, 0), (0, 1), (0, 0)]
def qq(g):
    a, b = g[g.order == 'QR'], g[g.order == 'RQ']
    dA, dB = (a.Q != a.R).mean(), (b.Q != b.R).mean(); return dA - dB, dA, dB, len(a), len(b)
for key, g in list(B.groupby('model')) + [((m, l), x) for (m, l), x in B.groupby(['model', 'label'])]:
    q, dA, dB, nA, nB = qq(g); se = np.sqrt(dA * (1 - dA) / nA + dB * (1 - dB) / nB); p = 2 * norm.sf(abs(q) / se) if se > 0 else 1
    items = g.item.unique(); gi = {k: v for k, v in g.groupby('item')}
    bs = np.array([qq(pd.concat([gi[k] for k in rng.choice(items, len(items))]))[0] for _ in range(NB)]); lo, hi = np.percentile(bs, [5, 95])
    cA = np.array([((g.order == 'QR') & (g.Q == x) & (g.R == y)).sum() for x, y in CELLS]); cB = np.array([((g.order == 'RQ') & (g.Q == x) & (g.R == y)).sum() for x, y in CELLS])
    p_ord = chi2_contingency(np.vstack([cA, cB]) + 0.5)[1]
    pq_first = g[g.order == 'QR'].Q.mean(); pq_second = g[g.order == 'RQ'].Q.mean()
    print(f'  {str(key):22s} n={len(g):4d}  P(correct=yes) Q first {pq_first:.3f} / Q second {pq_second:.3f}  order p={p_ord:.2g}  q={q:+.3f} (p={p:.2g}) 90%CI[{lo:+.3f},{hi:+.3f}] equiv0.05={lo > -0.05 and hi < 0.05}')
