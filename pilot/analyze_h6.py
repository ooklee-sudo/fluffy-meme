"""H6 analysis: bias magnitude and hallucination by model x reasoning effort x temperature.
Usage: python3 analyze_h6.py <data_dir> <h6/raw.jsonl> <out_prefix>"""
import sys, re, json
import numpy as np, pandas as pd
from scipy import stats
D, RAW, PRE = sys.argv[1:4]
ABST = 'I am not sure, or I cannot verify this'
TARGET = {'TV': 'HD-558', 'Printer': '1000AX', 'Cell': 'X-3A'}; DECOY = {'Hal-B', 'L22', '5C-S'}
HUMAN = dict(green_pp=24.7, attraction=0.37, fair_d=-0.54)   # from compute_human_benchmarks.py

def blocks(text):
    parts = re.split(r'\nQ(\d+):\s*', '\n' + text); return {int(parts[i]): parts[i + 1] for i in range(1, len(parts) - 1, 2)}
def opts(b):
    m = re.search(r'Options:\n((?:\s+\d+ - .*\n?)+)', b)
    return {int(a): t.strip() for a, t in re.findall(r'\s+(\d+) - (.*)', m.group(1))} if m else {}
def classify(study, b, full=''):
    ot = list(opts(b).values())
    if study == 'default_eric':
        if 'electric' in b: return 'green', ('optout' if ot[0].startswith('Stay with GreenGrid') else 'optin')
        if 'organ donor' in b: return 'organ', ('optout' if 'is considered to be an organ donor' in b else 'optin')
    if study == 'context_effects':
        for k, w in [('TV', 'Scenario: Television'), ('Printer', 'Scenario: Printer'), ('Cell', 'Scenario: Cellphone')]:
            if w in b: return k, ('binary' if len(ot) == 2 else ('attraction' if set(ot) & DECOY else 'compromise'))
    if study == 'targeting_fairness' and 'How fair is this advertising plan' in b:
        return 'fair', ('targeted' if 'advertise the snacks to women directly' in (full or b) else 'broad')
    return None, None
def outcome(item, b, pos):
    txt = opts(b).get(pos)
    if txt is None: return np.nan
    if item == 'organ': return float(txt.startswith('You are therefore currently a potential donor') or (txt.startswith('If you wish to change') and 'not to be an organ donor' in b))
    if item == 'green': return float(txt.startswith('Stay with GreenGrid') or txt.startswith('Switch to GreenGrid'))
    if item == 'fair': m = re.match(r'(\d)', txt.strip()); return float(m.group(1)) if m else np.nan
    return txt

texts = {st: dict(zip(*(lambda d: (d.PID, d.survey_text))(pd.read_parquet(f'{D}/{st}-00000-of-00001.parquet')))) for st in ['default_eric', 'context_effects', 'targeting_fairness']}
bias, hall, tok = [], [], []
for l in open(RAW):
    x = json.loads(l); m = re.search(r'\{.*\}', x['content'] or '', re.S)
    cell = (x['model'], x['effort'], x['temp'])
    tok.append(dict(model=x['model'], effort=x['effort'], temp=x['temp'], rtok=x.get('rtok') or 0, cost=x['cost']))
    try: p = json.loads(m.group(0))
    except Exception: continue
    if x['task'] == 'battery':
        wrong = fab = ans = inv = n = 0; ok = True
        for k, q in enumerate(x['qs'], 1):
            try: pos = int((p.get(f'Q{k}') or {}).get('Answers', {}).get('SelectedByPosition'))
            except Exception: continue
            if not 1 <= pos <= len(q['opts']): continue
            n += 1; txt = q['opts'][pos - 1]
            if q['kind'] == 'invented': inv += 1; fab += int(txt != ABST)
            else: ans += 1; wrong += int(txt != ABST and txt != q['key'])
        if n >= 20: hall.append(dict(cell=cell, pid=x['pid'], err=wrong / 16, fab=fab / 10, hall=(wrong + fab) / 26))
    else:
        bl = blocks(texts[x['task']][x['pid']])
        for k, b in bl.items():
            item, cond = classify(x['task'], b, texts[x['task']][x['pid']])
            try: pos = int((p.get(f'Q{k}') or {}).get('Answers', {}).get('SelectedByPosition'))
            except Exception: continue
            if item: bias.append(dict(cell=cell, pid=x['pid'], item=item, cond=cond, y=outcome(item, b, pos)))
B = pd.DataFrame(bias); H = pd.DataFrame(hall); T = pd.DataFrame(tok)
rows = []
for cell, g in B.groupby('cell'):
    r = dict(model=cell[0], effort=cell[1], temp=cell[2])
    gr = g[g.item == 'green']; a, b = gr[gr.cond == 'optout'].y.dropna(), gr[gr.cond == 'optin'].y.dropna()
    r['green_pp'] = 100 * (a.mean() - b.mean()) if len(a) > 5 and len(b) > 5 else np.nan
    ests = []
    for k, t in TARGET.items():
        bn = g[(g.item == k) & (g.cond == 'binary')].y.dropna(); at = g[(g.item == k) & (g.cond == 'attraction')].y.dropna(); at = at[~at.isin(DECOY)]
        if len(at) > 5 and len(bn) > 5:
            pa, pb = min(max((at == t).mean(), .02), .98), min(max((bn == t).mean(), .02), .98); ests.append(np.log(pa / (1 - pa)) - np.log(pb / (1 - pb)))
    r['attraction'] = np.mean(ests) if ests else np.nan
    f = g[g.item == 'fair']; a, b = f[f.cond == 'targeted'].y.dropna(), f[f.cond == 'broad'].y.dropna()
    if len(a) > 5 and len(b) > 5:
        sd = np.sqrt(((len(a) - 1) * a.var() + (len(b) - 1) * b.var()) / (len(a) + len(b) - 2)); r['fair_d'] = (a.mean() - b.mean()) / sd if sd > 0 else 0.0
    rows.append(r)
C = pd.DataFrame(rows)
hh = H.groupby(H.cell.map(lambda c: c)).agg(err=('err', 'mean'), fab=('fab', 'mean'), hall=('hall', 'mean'), n_batt=('hall', 'size')).reset_index()
hh[['model', 'effort', 'temp']] = pd.DataFrame(hh['cell'].tolist(), index=hh.index); hh = hh.drop(columns='cell')
C = C.merge(hh, on=['model', 'effort', 'temp'], how='outer')
C = C.merge(T.groupby(['model', 'effort', 'temp']).agg(rtok=('rtok', 'mean'), cost=('cost', 'sum')).reset_index(), on=['model', 'effort', 'temp'], how='left')
lvl = {'none': 0, 'low': 1, 'medium': 1, 'high': 2}; C['level'] = C.effort.map(lambda e: lvl[e])
C.loc[(C.model == 'google/gemini-3.7-flash') & (C.effort == 'low'), 'level'] = 0
C.loc[(C.model == 'google/gemini-3.7-flash') & (C.effort == 'medium'), 'level'] = 1
for c in ['green_pp', 'attraction', 'fair_d']:
    if c not in C: C[c] = np.nan
# composite bias index: mean twin/human ratio over the three phenomena
C['bias_idx'] = C[['green_pp', 'attraction', 'fair_d']].apply(lambda r: np.nanmean([r.green_pp / HUMAN['green_pp'], r.attraction / HUMAN['attraction'], r.fair_d / HUMAN['fair_d']]), axis=1)
C.to_csv(f'{PRE}_cells.csv', index=False)
pd.set_option('display.width', 250, 'display.max_columns', 30, 'display.max_rows', 100)
print(C.sort_values(['model', 'level', 'temp']).round(2).to_string(index=False))
def ols(df, y, xs):
    d = df.dropna(subset=[y] + xs + ['model']); X = pd.concat([d[xs], pd.get_dummies(d.model, drop_first=True).astype(float)], axis=1); X.insert(0, 'c', 1.0)
    Xv = X.values.astype(float); yv = d[y].values.astype(float); b = np.linalg.lstsq(Xv, yv, rcond=None)[0]; e = yv - Xv @ b
    XtXi = np.linalg.pinv(Xv.T @ Xv); V = XtXi @ (Xv.T * e ** 2) @ Xv @ XtXi * len(yv) / max(len(yv) - Xv.shape[1], 1)
    return {x: (b[1 + i], np.sqrt(V[1 + i, 1 + i])) for i, x in enumerate(xs)}, len(yv)
print('\nOLS with model fixed effects (HC1 SEs), cells as units')
for y in ['bias_idx', 'green_pp', 'attraction', 'fair_d', 'hall', 'fab', 'err']:
    res, n = ols(C, y, ['level', 'temp'])
    print(f'{y:10s} n={n} ' + '  '.join(f'{k}: {b:+.3f} (se {s:.3f})' for k, (b, s) in res.items()))
d = C.dropna(subset=['bias_idx', 'hall']).copy()
for c in ['bias_idx', 'hall']: d[c + '_w'] = d[c] - d.groupby('model')[c].transform('mean')
print('\nCell-level Spearman, bias_idx vs hallucination: pooled rho=%.2f (n=%d); within-model rho=%.2f' % (stats.spearmanr(d.bias_idx, d.hall)[0], len(d), stats.spearmanr(d.bias_idx_w, d.hall_w)[0]))
