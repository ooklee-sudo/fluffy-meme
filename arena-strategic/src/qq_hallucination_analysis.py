"""Analysis as preregistered in arena-strategic/prereg/qq_hallucination_prereg.md."""
import numpy as np, pandas as pd, statsmodels.formula.api as smf
from scipy.stats import norm, fisher_exact, mannwhitneyu, chi2_contingency
T = pd.read_pickle('/home/user/data/qq_halluc.pkl'); K = pd.read_pickle('/home/user/data/qq_halluc_known.pkl')
print('Answer (hallucination) rate, both questions answered Yes/No:'); print(T.pivot_table(index='model', columns='type', values='answered').round(3))
print('Says it knows the entity:'); print(K.pivot_table(index='model', columns='type', values='says_known').round(3))
A = T[T.answered == 1]
CELLS = [(1, 1), (1, 0), (0, 1), (0, 0)]
rows = []
for (it, m), g in A.groupby(['item', 'model']):
    a, b = g[g.order == 'AB'], g[g.order == 'BA']; nA, nB = len(a), len(b)
    if min(nA, nB) == 0:
        rows.append(dict(item=it, type=g.type.iloc[0], model=m, nA=nA, nB=nB, excluded='too few')); continue
    dA, dB = (a['first'] != a['second']).mean(), (b['first'] != b['second']).mean(); q = dA - dB
    se = np.sqrt(dA * (1 - dA) / nA + dB * (1 - dB) / nB); z = q / se if se > 0 else 0.0; p = 2 * norm.sf(abs(z)) if se > 0 else 1.0
    pa, pb = a['first'].mean(), b['first'].mean()
    cA = np.array([((a['first'] == x) & (a['second'] == y)).sum() for x, y in CELLS]); cB = np.array([((b['second'] == x) & (b['first'] == y)).sum() for x, y in CELLS])
    p_ord = chi2_contingency(np.vstack([cA, cB]) + 0.5)[1]
    exc = 'too few' if min(nA, nB) < 30 else ('degenerate' if (min(pa, pb) < 0.05 or max(pa, pb) > 0.95) else '')
    rows.append(dict(item=it, type=g.type.iloc[0], model=m, nA=nA, nB=nB, yesA_first=round(pa, 3), yesB_first=round(pb, 3), q=round(q, 3), z=round(z, 2),
                     p=float(f'{p:.3g}'), violation=int(p < 0.05), order_effect=int(p_ord < 0.05), excluded=exc))
R = pd.DataFrame(rows); pd.set_option('display.width', 220); print(R.to_string(index=False))
# items with no answered trials at all
miss = [(it, m) for it in T.item.unique() for m in T.model.unique() if not ((R['item'] == it) & (R.model == m)).any()]
print('cells with no answered trials:', len(miss), miss[:12])
print('Exclusions by type:', R.groupby(['type', 'excluded']).size().to_dict())
U = R[R.excluded == ''].copy()
print('Analyzed cells:', U.groupby('type').size().to_dict(), '| violation rate:', U.groupby('type').violation.mean().round(3).to_dict(), '| order-effect rate:', U.groupby('type').order_effect.mean().round(3).to_dict())
t = [[int(U[(U.type == 'R')].violation.sum()), int((U.type == 'R').sum() - U[(U.type == 'R')].violation.sum())],
     [int(U[(U.type == 'F')].violation.sum()), int((U.type == 'F').sum() - U[(U.type == 'F')].violation.sum())]]
print('PRIMARY Fisher exact, one-sided (R violates more than F):', round(fisher_exact(t, alternative='greater')[1], 4), t)
if (U.type == 'F').any() and (U.type == 'R').any():
    print('Mean z^2 by type:', (U.z ** 2).groupby(U.type).mean().round(2).to_dict(), '| Mann-Whitney R > F one-sided p =',
          round(mannwhitneyu(U[U.type == 'R'].z ** 2, U[U.type == 'F'].z ** 2, alternative='greater').pvalue, 4))
    try:
        U['Rr'] = (U.type == 'R').astype(int); mm = smf.logit('violation ~ Rr + C(model)', U).fit(disp=0)
        print(f'Logit b_R = {mm.params.Rr:.3f} (se {mm.bse.Rr:.3f})')
    except Exception as e: print('logit not estimable:', type(e).__name__)
R.to_csv('/home/user/fluffy-meme/arena-strategic/results/qq_hallucination_cells.csv', index=False)
