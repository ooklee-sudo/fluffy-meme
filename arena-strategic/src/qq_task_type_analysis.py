"""Analysis exactly as preregistered in arena-strategic/prereg/qq_task_type_prereg.md."""
import numpy as np, pandas as pd, statsmodels.formula.api as smf
from scipy.stats import norm, chi2_contingency, fisher_exact, mannwhitneyu
d = pd.read_pickle('/home/user/data/qq_task_type.pkl')
CELLS = [(1, 1), (1, 0), (0, 1), (0, 0)]
rows = []
for (it, m), g in d.groupby(['item', 'model']):
    A, B = g[g.order == 'AB'], g[g.order == 'BA']
    cA = np.array([((A['first'] == a) & (A['second'] == b)).sum() for a, b in CELLS], float)
    cB = np.array([((B['first'] == a) & (B['second'] == b)).sum() for a, b in CELLS], float)
    nA, nB = cA.sum(), cB.sum()
    dA, dB = (cA[1] + cA[2]) / nA, (cB[1] + cB[2]) / nB
    q = dA - dB; se = np.sqrt(dA * (1 - dA) / nA + dB * (1 - dB) / nB)
    z = q / se if se > 0 else 0.0; p = 2 * norm.sf(abs(z)) if se > 0 else 1.0
    pa, pb = A['first'].mean(), B['first'].mean()      # yes-share of each question when asked first
    degen = bool(min(pa, pb) < 0.05 or max(pa, pb) > 0.95)
    # order effect: answers to question A (first in AB, second in BA) and B, as a 2x4 table of (A,B) patterns
    cB_ab = np.array([cB[0], cB[2], cB[1], cB[3]])       # reorder BA cells to (A,B) pattern order
    try: p_order = chi2_contingency(np.vstack([cA, cB_ab]) + 0.5)[1]
    except Exception: p_order = np.nan
    rows.append(dict(item=it, type=g.type.iloc[0], model=m, nA=int(nA), nB=int(nB), yesA_first=round(pa, 3), yesB_first=round(pb, 3),
                     q=round(q, 3), z=round(z, 2), p=float(f'{p:.3g}'), violation=int(p < 0.05), degenerate=degen, order_effect=int(p_order < 0.05)))
R = pd.DataFrame(rows)
pd.set_option('display.width', 220); print(R.to_string(index=False))
print('\nDegenerate cells excluded:', R.groupby('type').degenerate.sum().to_dict(), 'of', R.groupby('type').size().to_dict())
U = R[~R.degenerate].copy(); U['K'] = (U.type == 'K').astype(int)
print('Non-degenerate cells:', U.groupby('type').size().to_dict())
print('Violation rate:', U.groupby('type').violation.mean().round(3).to_dict(), '| order-effect rate:', U.groupby('type').order_effect.mean().round(3).to_dict())
# PRIMARY: logit violation ~ K + evaluator FE, cluster by item, one-sided K > S
try:
    m = smf.logit('violation ~ K + C(model)', U).fit(disp=0, cov_type='cluster', cov_kwds={'groups': pd.factorize(U['item'])[0]})
    b, se = m.params['K'], m.bse['K']; print(f'PRIMARY logit: b_K = {b:.3f} (se {se:.3f}), one-sided p = {norm.sf(b / se):.4f}')
except Exception as e:
    print('PRIMARY logit failed:', e)
t = pd.crosstab(U.type, U.violation).reindex(index=['K', 'S'], columns=[1, 0], fill_value=0)
print('Fisher exact (K vs S, violation), one-sided greater:', round(fisher_exact(t.values, alternative='greater')[1], 4), t.values.tolist())
z2 = U.assign(z2=U.z ** 2).groupby('type').z2
print('Mean z^2 by type:', z2.mean().round(2).to_dict(), '| Mann-Whitney K > S one-sided p =',
      round(mannwhitneyu(U[U.type == 'K'].z ** 2, U[U.type == 'S'].z ** 2, alternative='greater').pvalue, 4))
print('By evaluator (violation rate, non-degenerate):'); print(U.pivot_table(index='model', columns='type', values='violation', aggfunc=['mean', 'count']).round(2))
R.to_csv('/home/user/fluffy-meme/arena-strategic/results/qq_task_type_cells.csv', index=False)
