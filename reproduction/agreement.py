"""Agreement between two LLM scorers on the same O*NET task statements (0-2 rubrics).
Usage: python agreement.py SCORES_A SCORES_B OUT_JSON"""
import sys, json, numpy as np, pandas as pd
A = pd.DataFrame([json.loads(l) for l in open(sys.argv[1])]).drop_duplicates('task').set_index('task')
B = pd.DataFrame([json.loads(l) for l in open(sys.argv[2])]).drop_duplicates('task').set_index('task')
idx = A.index.intersection(B.index); out = {'n_tasks': int(len(idx)), 'scorer_a': A.model.iloc[0], 'scorer_b': B.model.iloc[0]}
def stats(a, b, cats):
    a, b = np.asarray(a), np.asarray(b); K = len(cats)
    M = np.zeros((K, K))
    for i, c1 in enumerate(cats):
        for j, c2 in enumerate(cats): M[i, j] = ((a == c1) & (b == c2)).sum()
    n = M.sum(); po = np.trace(M) / n
    pa, pb = M.sum(1) / n, M.sum(0) / n
    pe = (pa * pb).sum(); kappa = (po - pe) / (1 - pe)
    w = 1 - ((np.arange(K)[:, None] - np.arange(K)[None, :]) ** 2) / (K - 1) ** 2
    pw = (w * M).sum() / n; pwe = (w * np.outer(pa, pb)).sum(); wk = (pw - pwe) / (1 - pwe)
    pi = (pa + pb) / 2; ac1 = (po - (pi * (1 - pi)).sum() / (K - 1)) / (1 - (pi * (1 - pi)).sum() / (K - 1))
    return {'raw_agreement': po, 'cohen_kappa': kappa, 'weighted_kappa_quadratic': wk, 'gwet_ac1': ac1}
for rub in ('visual', 'text'):
    a, b = A.loc[idx, rub], B.loc[idx, rub]
    r = stats(a, b, [0, 1, 2]); r['share_nonzero_a'] = float((a > 0).mean()); r['share_nonzero_b'] = float((b > 0).mean())
    r['share_score2_a'] = float((a == 2).mean()); r['share_score2_b'] = float((b == 2).mean())
    rb = stats((a > 0).astype(int), (b > 0).astype(int), [0, 1]); r['binary_any'] = rb
    out[rub] = r
json.dump(out, open(sys.argv[3], 'w'), indent=1, default=float); print(json.dumps(out, indent=1, default=float))
