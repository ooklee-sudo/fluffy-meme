"""Stability analysis across prompt template and model generation (exploratory). Usage: python3 analyze_gen.py <gen/raw.jsonl> <out_prefix> [bootstrap_reps]
Validity levels per (effect, configuration): 2 = twin point estimate inside the human 95% CI (magnitude-valid); 1 = same sign as the human effect and twin CI excludes zero
(direction-valid; only defined where the human CI excludes zero); 0 = invalid. Stability: template agreement, generation agreement, and a balanced ANOVA variance decomposition of z-scored discrepancies."""
import sys, re, json, itertools
import numpy as np, pandas as pd
RAW, PRE = sys.argv[1], sys.argv[2]; B = int(sys.argv[3]) if len(sys.argv) > 3 else 400
HUMAN = dict(default_green=(24.67, 16.9, 32.4), default_organ=(4.39, -3.5, 12.3), attraction=(0.37, 0.11, 0.62), fair=(-0.54, -0.75, -0.33), frame=(0.76, 0.67, 0.85), anch_africa=(0.78, 0.69, 0.87), anch_redwood=(1.69, 1.59, 1.79))
TARGET = {'attr_TV': 'HD-558', 'attr_Printer': '1000AX', 'attr_Cell': 'X-3A'}; DECOY = {'attr_TV': 'Hal-B', 'attr_Printer': 'L22', 'attr_Cell': '5C-S'}
src = open(__file__.replace('analyze_gen.py', 'analyze_c1.py')).read(); a = src.index('def eff(item'); b = src.index('def boot(')
ns = dict(np=np, pd=pd, TARGET=TARGET, DECOY=DECOY, ITEMS=['default_green', 'default_organ', 'fair', 'frame', 'anch_africa', 'anch_redwood']); exec(src[a:b], ns); effects = ns['effects']
rows, excl = {}, {}
def get(p, n, tpl):
    v = p.get(f'Q{n}')
    if tpl == 'B': return v
    a_ = (v or {}).get('Answers', {}) if isinstance(v, dict) else {}
    return a_.get('SelectedByPosition', a_.get('Value'))
for l in open(RAW):
    x = json.loads(l); key = (x['model'], x['template']); excl.setdefault(key, [0, 0]); excl[key][1] += 1
    m = re.search(r'\{.*\}', x['content'] or '', re.S)
    try: p = json.loads(m.group(0))
    except Exception: excl[key][0] += 1; continue
    rec = dict(pid=x['pid'])
    for n, q in enumerate(x['qs'], 1):
        try: v = float(get(p, n, x['template']))
        except Exception: continue
        it, cond = q['item'], x['conds'][q['item']]
        if q['opts']:
            pos = int(v)
            if not 1 <= pos <= len(q['opts']): continue
            txt = q['opts'][pos - 1]
            if it == 'default_organ': y = float(txt.startswith('You are therefore currently a potential donor') or (txt.startswith('If you wish to change') and 'not to be an organ donor' in q['text']))
            elif it == 'default_green': y = float(txt.startswith('Stay with GreenGrid') or txt.startswith('Switch to GreenGrid'))
            elif it in TARGET: y = txt
            elif it in ('fair', 'frame'): y = float(pos)
            else: continue
            rec[it] = (cond, y)
        elif it.startswith('anch'): rec[it] = (cond, np.log10(max(v, 1.0)))
    rows.setdefault(key, []).append(rec)
print({k: f'{a_}/{b_} excl' for k, (a_, b_) in excl.items() if a_}); rng = np.random.default_rng(2026); out = []
for (m, t), recs in rows.items():
    D = pd.DataFrame(recs); pt = effects(D); bs = []
    for _ in range(B): bs.append(effects(D.iloc[rng.integers(0, len(D), len(D))]))
    bs = pd.DataFrame(bs)
    for it, (h, hl, hh) in HUMAN.items():
        v = pt.get(it, np.nan); lo, hi = np.nanpercentile(bs[it], [2.5, 97.5]) if it in bs else (np.nan, np.nan)
        if np.isnan(v): lev = np.nan
        elif hl <= v <= hh: lev = 2
        elif hl > 0 or hh < 0: lev = 1 if (np.sign(v) == np.sign(h) and (lo > 0 or hi < 0)) else 0
        else: lev = 0
        out.append(dict(model=m, template=t, item=it, twin=v, lo=lo, hi=hi, human=h, D=v - h, level=lev, n=len(D)))
R = pd.DataFrame(out); R['family'] = R.model.map(lambda s: s.split('/')[1].rsplit('-', 1)[0] if 'claude' not in s else '-'.join(s.split('/')[1].split('-')[:2]))
R.to_csv(f'{PRE}_cells.csv', index=False)
pd.set_option('display.width', 220, 'display.max_rows', 400)
print('\nValidity level by effect and template (share of models at level 2 / 1 / 0):')
for (it, t), g in R.groupby(['item', 'template']): print(f'{it:14s} {t}: ' + ' / '.join(f'{(g.level == k).mean():.2f}' for k in (2, 1, 0)) + f'  (n models {g.model.nunique()})')
P = R.pivot_table(index=['model', 'item'], columns='template', values='level'); P = P.dropna()
agree = (P['A'] == P['B']).mean(); n = len(P); cats = [0, 1, 2]
po = agree; pe = sum((P['A'] == c).mean() * (P['B'] == c).mean() for c in cats); kappa = (po - pe) / (1 - pe) if pe < 1 else np.nan
Z = R.copy(); Z['z'] = Z.groupby('item').D.transform(lambda s: (s - s.mean()) / s.std(ddof=0) if s.std(ddof=0) > 0 else 0.0)
PZ = Z.pivot_table(index=['model', 'item'], columns='template', values='z').dropna()
print(f'\nTemplate stability: classification agreement A vs B = {po:.2f} (kappa {kappa:.2f}); correlation of z-scored discrepancies = {np.corrcoef(PZ.A, PZ.B)[0, 1]:.2f} (n = {n} model-effect pairs)')
gens = {'gemini-flash': ['google/gemini-3.5-flash', 'google/gemini-3.6-flash', 'google/gemini-3.7-flash'], 'grok': ['x-ai/grok-4.3', 'x-ai/grok-4.5', 'x-ai/grok-4.7'], 'claude-haiku': ['anthropic/claude-haiku-4.5', 'anthropic/claude-haiku-5.5'],
        'claude-sonnet': ['anthropic/claude-sonnet-5', 'anthropic/claude-sonnet-5.5'], 'gpt': ['openai/gpt-5.2', 'openai/gpt-5.4', 'openai/gpt-5.5']}
print('Generation stability (same template; share of effects with identical level and correlation of z-scored D across consecutive generations):')
for f, ms in gens.items():
    for t in ('A', 'B'):
        for m1, m2 in zip(ms[:-1], ms[1:]):
            g1 = Z[(Z.model == m1) & (Z.template == t)].set_index('item'); g2 = Z[(Z.model == m2) & (Z.template == t)].set_index('item'); ix = g1.index.intersection(g2.index)
            if len(ix) > 2: print(f'  {f:14s} {t} {m1.split("/")[1]} -> {m2.split("/")[1]}: level agreement {(g1.level[ix] == g2.level[ix]).mean():.2f}, corr(z) {np.corrcoef(g1.z[ix], g2.z[ix])[0, 1]:.2f}')
W = Z.pivot_table(index='model', columns=['item', 'template'], values='z').dropna(axis=0); M = list(W.index); E = sorted({c[0] for c in W.columns}); T = ['A', 'B']
Y = np.array([[[W.loc[m, (e, t)] for t in T] for e in E] for m in M]); gm = Y.mean(); ss = {}
mm, ee, tt = Y.mean(axis=(1, 2)), Y.mean(axis=(0, 2)), Y.mean(axis=(0, 1))
ss['model'] = len(E) * len(T) * ((mm - gm) ** 2).sum(); ss['effect'] = len(M) * len(T) * ((ee - gm) ** 2).sum(); ss['template'] = len(M) * len(E) * ((tt - gm) ** 2).sum()
me, mt, et = Y.mean(axis=2), Y.mean(axis=1), Y.mean(axis=0)
ss['model x effect'] = len(T) * ((me - mm[:, None] - ee[None, :] + gm) ** 2).sum(); ss['model x template'] = len(E) * ((mt - mm[:, None] - tt[None, :] + gm) ** 2).sum(); ss['effect x template'] = len(M) * ((et - ee[:, None] - tt[None, :] + gm) ** 2).sum()
tot = ((Y - gm) ** 2).sum(); ss['residual (3-way)'] = tot - sum(ss.values())
print('\nVariance decomposition of z-scored discrepancies (share of total sum of squares):'); [print(f'  {k:20s} {v / tot:.2f}') for k, v in ss.items()]
fam = {m: f for f, ms in gens.items() for m in ms}; bf = pd.Series(mm, index=M); fm = bf.groupby(bf.index.map(fam)).transform('mean')
print(f'  model main effect splits into family {((fm - gm) ** 2).sum() / ((bf - gm) ** 2).sum():.2f} and generation-within-family {((bf - fm) ** 2).sum() / ((bf - gm) ** 2).sum():.2f}')
