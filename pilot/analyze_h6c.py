"""Confirmatory H6 grid analysis (P4, P5). Written before any run_h6c output was analyzed.
Usage: python3 analyze_h6c.py <h6c/raw.jsonl> <out_prefix>
Cell = model x effort x temperature (36 cells; 100 respondents per cell for the booklet and for each battery).
Bias index = mean of twin/human ratios for loss framing, attraction, and anchoring (human values fixed in the registration).
Error = share of answerable items answered wrongly (abstain not counted as wrong); fabrication A / B = share of invented items answered non-abstain (nudged / un-nudged).
P4 (registered direction: negative): coefficient of reasoning level on bias index and on error, OLS with model fixed effects and HC1 SEs, plus per-model coefficients.
  'Supported' if the pooled coefficient is negative with 95% CI below zero and negative in >= 3 of 4 models; 'partly supported' if negative in >= 3 of 4 models only; otherwise 'not supported'.
P5 (registered direction: positive): within-model Spearman correlation between bias index and error over the 9 cells per model, pooled by averaging; same verdict rule with a permutation CI."""
import sys, re, json
import numpy as np, pandas as pd
from scipy import stats
RAW, PRE = sys.argv[1], sys.argv[2]
ABST = 'I am not sure, or I cannot verify this'
HUMAN = dict(default_green=24.67, default_organ=4.39, attraction=0.37, fair=-0.54, frame=0.76, anch_africa=0.78, anch_redwood=1.69)
TARGET = {'attr_TV': 'HD-558', 'attr_Printer': '1000AX', 'attr_Cell': 'X-3A'}; DECOY = {'attr_TV': 'Hal-B', 'attr_Printer': 'L22', 'attr_Cell': '5C-S'}
ITEMS = ['frame', 'anch_africa', 'anch_redwood']
src = open(__file__.replace('analyze_h6c.py', 'analyze_c1.py')).read(); a = src.index('def eff(item'); b = src.index('def boot(')
ns = dict(np=np, pd=pd, TARGET=TARGET, DECOY=DECOY, ITEMS=['default_green', 'default_organ', 'fair', 'frame', 'anch_africa', 'anch_redwood']); exec(src[a:b], ns); effects = ns['effects']

book, batt = {}, []
for l in open(RAW):
    x = json.loads(l); cell = (x['model'], x['effort'], x['temp']); m = re.search(r'\{.*\}', x['content'] or '', re.S)
    try: p = json.loads(m.group(0))
    except Exception: continue
    if x['task'] == 'booklet':
        rec = dict(pid=x['pid'])
        for n, q in enumerate(x['qs'], 1):
            try: v = float(p.get(f'Q{n}'))
            except Exception: continue
            it, cond = q['item'], x['conds'][q['item']]
            if q['opts']:
                pos = int(v)
                if not 1 <= pos <= len(q['opts']): continue
                txt = q['opts'][pos - 1]
                if it in TARGET: rec[it] = (cond, txt)
                elif it == 'frame': rec[it] = (cond, float(pos))
            elif it.startswith('anch'): rec[it] = (cond, np.log10(max(v, 1.0)))
        book.setdefault(cell, []).append(rec)
    else:
        wrong = fab = n_a = n_i = 0
        for k, q in enumerate(x['qs'], 1):
            try: pos = int((p.get(f'Q{k}') or {}).get('Answers', {}).get('SelectedByPosition'))
            except Exception: continue
            if not 1 <= pos <= len(q['opts']): continue
            txt = q['opts'][pos - 1]
            if q['kind'] == 'invented': n_i += 1; fab += int(txt != ABST)
            else: n_a += 1; wrong += int(txt != ABST and txt != q['key'])
        batt.append(dict(cell=cell, which=x['task'], err=wrong / n_a if n_a else np.nan, fab=fab / n_i if n_i else np.nan, ok=(n_a + n_i) >= (0.8 * len(x['qs']))))
rows = []
for cell, recs in book.items():
    e = effects(pd.DataFrame(recs)); r = dict(model=cell[0], effort=cell[1], temp=cell[2], n_book=len(recs), **{k: e.get(k, np.nan) for k in ['frame', 'attraction', 'anch_africa', 'anch_redwood']})
    r['bias_idx'] = np.nanmean([r['frame'] / HUMAN['frame'], r['attraction'] / HUMAN['attraction'], np.nanmean([r['anch_africa'] / HUMAN['anch_africa'], r['anch_redwood'] / HUMAN['anch_redwood']])]); rows.append(r)
C = pd.DataFrame(rows); Bt = pd.DataFrame(batt); Bt = Bt[Bt.ok]
for which, col in [('battA', 'err'), ('battA', 'fabA'), ('battB', 'fabB')]:
    src_col = 'err' if col == 'err' else 'fab'; g = Bt[Bt.which == which].groupby('cell')[src_col].mean().rename(col)
    C = C.merge(g.reset_index().assign(model=lambda d: d.cell.map(lambda c: c[0]), effort=lambda d: d.cell.map(lambda c: c[1]), temp=lambda d: d.cell.map(lambda c: c[2])).drop(columns='cell'), on=['model', 'effort', 'temp'], how='left')
lv = {'none': 0, 'low': 1, 'medium': 1, 'high': 2}; C['level'] = C.effort.map(lv)
C.loc[(C.model == 'google/gemini-3.7-flash') & (C.effort == 'low'), 'level'] = 0; C.loc[(C.model == 'google/gemini-3.7-flash') & (C.effort == 'medium'), 'level'] = 1
C.to_csv(f'{PRE}_cells.csv', index=False)
pd.set_option('display.width', 230, 'display.max_columns', 30, 'display.max_rows', 100); print(C.sort_values(['model', 'level', 'temp']).round(2).to_string(index=False))

def ols(df, y):
    d = df.dropna(subset=[y, 'level', 'temp']); X = pd.concat([d[['level', 'temp']], pd.get_dummies(d.model, drop_first=True).astype(float)], axis=1); X.insert(0, 'c', 1.0)
    Xv = X.values.astype(float); yv = d[y].values.astype(float); bb = np.linalg.lstsq(Xv, yv, rcond=None)[0]; e = yv - Xv @ bb
    XtXi = np.linalg.pinv(Xv.T @ Xv); V = XtXi @ (Xv.T * e ** 2) @ Xv @ XtXi * len(yv) / max(len(yv) - Xv.shape[1], 1)
    return bb[1], np.sqrt(V[1, 1]), len(yv)
out = []
for y in ['bias_idx', 'frame', 'attraction', 'err', 'fabA', 'fabB']:
    b0, se, n = ols(C, y); per = [np.polyfit(g.level, g[y], 1)[0] for _, g in C.dropna(subset=[y]).groupby('model') if g.level.nunique() > 1]
    k = sum(v < 0 for v in per); ci = (b0 - 1.96 * se, b0 + 1.96 * se)
    v = 'supported' if (b0 < 0 and ci[1] < 0 and k >= 3) else ('partly supported' if k >= 3 else 'not supported')
    out.append(dict(test=f'P4 level -> {y} (predicted negative)', coef=b0, ci_lo=ci[0], ci_hi=ci[1], models_negative=f'{k}/{len(per)}', verdict=v))
d = C.dropna(subset=['bias_idx', 'err']).copy(); rng = np.random.default_rng(2026)
def within(df): return np.nanmean([stats.spearmanr(g.bias_idx, g.err)[0] for _, g in df.groupby('model') if len(g) > 3])
obs = within(d); perm = [within(d.assign(err=d.groupby('model').err.transform(lambda s: rng.permutation(s.values)))) for _ in range(2000)]
per_m = [stats.spearmanr(g.bias_idx, g.err)[0] for _, g in d.groupby('model') if len(g) > 3]; k = sum(v > 0 for v in per_m)
v = 'supported' if (obs > 0 and np.mean(np.array(perm) >= obs) < .025 and k >= 3) else ('partly supported' if k >= 3 else 'not supported')
out.append(dict(test='P5 within-model Spearman(bias_idx, error) (predicted positive)', coef=obs, ci_lo=np.percentile(perm, 2.5), ci_hi=np.percentile(perm, 97.5), models_negative=f'{k}/{len(per_m)} positive', verdict=v))
R = pd.DataFrame(out); R.to_csv(f'{PRE}_propositions.csv', index=False); print('\n' + R.round(3).to_string(index=False))
