"""Compare LLM silicon respondents with human Gallup data (Wang et al. 2014, Table 1)."""
import sys, numpy as np, pandas as pd
from scipy.stats import chi2_contingency, norm, pearsonr
sys.path.insert(0, 'src')
from qq_human_replication import HUMAN, ITEMS
d = pd.read_pickle('/home/user/data/qq_human_rep.pkl')
N_HUMAN = 500   # ~1,000 respondents per poll split across two orders (Wang et al. report ~1,000 per poll)
CELLS = [(1, 1), (1, 0), (0, 1), (0, 0)]
def cells(g): return np.array([((g['first'] == a) & (g['second'] == b)).sum() for a, b in CELLS], float)
def qstat(pAB, pBA, nA, nB):
    dA, dB = pAB[1] + pAB[2], pBA[1] + pBA[2]; q = dA - dB
    se = np.sqrt(dA * (1 - dA) / nA + dB * (1 - dB) / nB); return q, se, 2 * norm.sf(abs(q) / se) if se > 0 else np.nan
rows = []
for (m, item), g in d.groupby(['model', 'item']):
    cA, cB = cells(g[g.order == 'AB']), cells(g[g.order == 'BA']); nA, nB = cA.sum(), cB.sum()
    pA, pB = cA / nA, cB / nB
    try: p_order = chi2_contingency(np.vstack([cA, cB]) + 0.5)[1]
    except Exception: p_order = np.nan
    q, se, pq = qstat(pA, pB, nA, nB)
    r = dict(model=m, item=item, n=int(nA + nB), P_A_yes_first=round(pA[0] + pA[1], 3), P_B_yes_first=round(pB[0] + pB[1], 3),
             order_p=float(f'{p_order:.2g}'), q=round(q, 3), q_se=round(se, 3), q_p=float(f'{pq:.2g}'), QQ_holds=bool(pq > 0.05 and abs(q) < 0.05))
    if item in HUMAN:
        hA, hB = np.array(HUMAN[item]['AB']), np.array(HUMAN[item]['BA'])
        hq, hse, hp = qstat(hA, hB, N_HUMAN, N_HUMAN)
        ce_h, ce_l = hA - hB, pA - pB
        r.update(human_PA=round(hA[0] + hA[1], 3), human_PB=round(hB[0] + hB[1], 3), human_q=round(hq, 3),
                 TV_AB=round(0.5 * np.abs(pA - hA).sum(), 3), TV_BA=round(0.5 * np.abs(pB - hB).sum(), 3),
                 context_corr=round(np.corrcoef(ce_h, ce_l)[0, 1], 2) if ce_l.std() > 0 else np.nan,
                 context_sign_match=f'{int((np.sign(ce_h) == np.sign(ce_l)).sum())}/4')
    rows.append(r)
R = pd.DataFrame(rows); pd.set_option('display.width', 260); pd.set_option('display.max_columns', 30)
print('HUMAN benchmark (Wang et al. 2014, Table 1):')
for it in HUMAN:
    hA, hB = np.array(HUMAN[it]['AB']), np.array(HUMAN[it]['BA']); print(f'  {it:13s} P(A yes, A first)={hA[0]+hA[1]:.3f}  P(B yes, B first)={hB[0]+hB[1]:.3f}  q={qstat(hA, hB, N_HUMAN, N_HUMAN)[0]:+.3f}')
print(R.to_string(index=False))
R.to_csv('/home/user/fluffy-meme/arena-strategic/results/qq_human_replication.csv', index=False)
