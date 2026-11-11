"""Analysis as preregistered in prereg/qq_counterbalanced_prereg.md."""
import numpy as np, pandas as pd
from scipy.stats import norm
A = pd.read_pickle('/home/user/data/cb_study1.pkl'); B = pd.read_pickle('/home/user/data/cb_study2.pkl')
def qstat(g, o1, o2):
    a, b = g[g.order == o1], g[g.order == o2]
    if len(a) == 0 or len(b) == 0: return np.nan, np.nan, 0, 0
    dA, dB = (a['first'] != a['second']).mean(), (b['first'] != b['second']).mean()
    return dA - dB, np.sqrt(dA * (1 - dA) / len(a) + dB * (1 - dB) / len(b)), len(a), len(b)
def verdict(q, se): return 'n/a' if not np.isfinite(q) else ('holds' if (se == 0 or 2 * norm.sf(abs(q) / se) >= 0.05) else 'VIOLATED')
def analyze(D, keys, o1, o2, yes_first_cols):
    rows = []
    for key, g in D.groupby(keys):
        r = dict(zip(keys, key if isinstance(key, tuple) else (key,)))
        qs = {}
        for mp, gm in g.groupby('map'):
            q, se, na, nb = qstat(gm, o1, o2); qs[mp] = (q, se)
            r[f'q_{mp}'] = round(q, 3); r[f'p_{mp}'] = float(f'{2 * norm.sf(abs(q) / se):.2g}') if se > 0 else 1.0
            r[f'yes1_{mp}'] = round(gm[gm.order == o1]['first'].mean(), 3); r[f'yes2_{mp}'] = round(gm[gm.order == o2]['first'].mean(), 3)
        if len(qs) == 2:
            qp = (qs['M1'][0] + qs['M2'][0]) / 2; sep = 0.5 * np.sqrt(qs['M1'][1] ** 2 + qs['M2'][1] ** 2)
            r['q_pooled'] = round(qp, 3); r['p_pooled'] = float(f'{2 * norm.sf(abs(qp) / sep):.2g}') if sep > 0 else 1.0
            r['verdict_pooled'] = verdict(qp, sep); r['label_robust'] = verdict(*qs['M1']) == verdict(*qs['M2'])
            ya, yb = (r['yes1_M1'] + r['yes1_M2']) / 2, (r['yes2_M1'] + r['yes2_M2']) / 2
            r['yes1_pooled'], r['yes2_pooled'] = round(ya, 3), round(yb, 3); r['degenerate'] = bool(min(ya, yb) < 0.05 or max(ya, yb) > 0.95)
        r['n'] = len(g); rows.append(r)
    return pd.DataFrame(rows)
pd.set_option('display.width', 260); pd.set_option('display.max_columns', 40)
print('STUDY 1R (pooled over items). Question A = quality, B = developer; order QB = quality first.')
R1 = analyze(A, ['model', 'disc'], 'QB', 'BQ', None)
ORIG1 = {('haiku', 0): 'holds', ('haiku', 1): 'VIOLATED', ('llama', 0): 'holds', ('llama', 1): 'VIOLATED', ('qwen', 0): 'holds', ('qwen', 1): 'holds'}
R1['original_verdict'] = [ORIG1[(m, d)] for m, d in zip(R1.model, R1.disc)]; R1['replicates'] = R1.verdict_pooled == R1.original_verdict
print(R1.to_string(index=False))
# quality judgment share (quality asked first), by mapping: the "no" tendency and the disclosure penalty
print('\nShare judging the focal response better (quality asked first):')
qf = A[A.order == 'QB']; print(qf.pivot_table(index='model', columns=['disc', 'map'], values='Q').round(3))
pen = qf.groupby(['model', 'map', 'disc']).Q.mean().unstack('disc'); pen['penalty'] = pen[1] - pen[0]; print('Disclosure penalty by mapping:'); print(pen.round(3))
print('\nSTUDY 2R (per item). Order AB = first-listed question first.')
R2 = analyze(B, ['model', 'item'], 'AB', 'BA', None)
ORIG2 = {('haiku', 'clinton_gore'): 'holds', ('llama', 'clinton_gore'): 'VIOLATED', ('qwen', 'clinton_gore'): 'VIOLATED',
         ('haiku', 'white_black'): 'holds', ('llama', 'white_black'): 'VIOLATED', ('qwen', 'white_black'): 'holds',
         ('haiku', 'rose_jackson'): 'VIOLATED', ('llama', 'rose_jackson'): 'VIOLATED', ('qwen', 'rose_jackson'): 'VIOLATED',
         ('haiku', 'bonds_clemens'): 'VIOLATED', ('llama', 'bonds_clemens'): 'holds', ('qwen', 'bonds_clemens'): 'VIOLATED',
         ('haiku', 'urban_rural'): 'VIOLATED', ('llama', 'urban_rural'): 'VIOLATED', ('qwen', 'urban_rural'): 'VIOLATED'}
R2['original_verdict'] = [ORIG2[(m, i)] for m, i in zip(R2.model, R2['item'])]; R2['replicates'] = R2.verdict_pooled == R2.original_verdict
print(R2.to_string(index=False))
for name, R in (('1R', R1), ('2R', R2)):
    print(f'{name}: verdict replicates {int(R.replicates.sum())}/{len(R)} | label-robust {int(R.label_robust.sum())}/{len(R)}')
R1.to_csv('/home/user/fluffy-meme/arena-strategic/results/qq_counterbalanced_study1.csv', index=False); R2.to_csv('/home/user/fluffy-meme/arena-strategic/results/qq_counterbalanced_study2.csv', index=False)
