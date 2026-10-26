"""Confirmatory analysis of C1 (AsPredicted #320110). Written and committed before any C1 output was analyzed.
Usage: python3 analyze_c1.py <c1/raw.jsonl> <out_prefix> [bootstrap_reps]
Decisions fixed here (clarifications made before looking at C1 output):
 - Primary architecture for P1-P3 is the persona summary; demographics-only is reported as robustness.
 - P1 is evaluated on the canonical cue-based paradigms (loss framing, anchoring); attraction has no canonical paradigm in C1.
 - P2: D_organ > 0 and D_green <= 0. P3: defaults only (no canonical fairness paradigm in C1): D_green - D_organ < 0.
 - P6: theory-explicit minus demographics-only effect, averaged over canonical paradigms (organ default pp/100, framing d, anchoring d).
 - A proposition is 'supported' if its sign holds in >= 4 of 5 models and the pooled CI excludes zero, 'partly supported' if the sign holds in >= 4 of 5 but the pooled CI
   includes zero, else 'not supported'. Pooled = unweighted mean of per-model values; CIs by respondent bootstrap within model.
 - Benjamini-Hochberg across the pooled tests is applied to the percentile-bootstrap two-sided p-values reported."""
import sys, re, json
import numpy as np, pandas as pd
RAW, PRE = sys.argv[1], sys.argv[2]; B = int(sys.argv[3]) if len(sys.argv) > 3 else 2000
HUMAN = dict(default_green=24.67, default_organ=4.39, attraction=0.37, fair=-0.54, frame=0.76, anch_africa=0.78, anch_redwood=1.69)   # pp, logOR, d, d, d(log), d(log)
TARGET = {'attr_TV': 'HD-558', 'attr_Printer': '1000AX', 'attr_Cell': 'X-3A'}; DECOY = {'attr_TV': 'Hal-B', 'attr_Printer': 'L22', 'attr_Cell': '5C-S'}
rows = []; excl = {}
for l in open(RAW):
    x = json.loads(l); key = (x['model'], x['arch']); excl.setdefault(key, [0, 0]); excl[key][1] += 1
    m = re.search(r'\{.*\}', x['content'] or '', re.S)
    try: p = json.loads(m.group(0))
    except Exception: excl[key][0] += 1; continue
    rec = dict(model=x['model'], arch=x['arch'], pid=x['pid'])
    for n, q in enumerate(x['qs'], 1):
        v = p.get(f'Q{n}')
        try: v = float(v)
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
            else: continue   # anchoring comparative question not analyzed
            rec[it] = (cond, y)
        elif it.startswith('anch'): rec[it] = (cond, np.log10(max(v, 1.0)))
    rows.append(rec)
D = pd.DataFrame(rows); print('respondent-rows', len(D)); print({k: f'{a}/{b} excluded' for k, (a, b) in excl.items()})

def eff(item, conds, ys):
    """Effect for one item from aligned arrays."""
    if item.startswith('default'):
        o, i = ys[conds == 'optout'], ys[conds == 'optin']
        return 100 * (o.mean() - i.mean()) if len(o) > 5 and len(i) > 5 else np.nan
    if item in ('fair', 'frame') or item.startswith('anch'):
        hi = {'fair': 'targeted', 'frame': 'loss'}.get(item, 'high'); lo = {'fair': 'broad', 'frame': 'gain'}.get(item, 'low')
        a, b = ys[conds == hi].astype(float), ys[conds == lo].astype(float)
        if len(a) < 5 or len(b) < 5: return np.nan
        sd = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2)); return (a.mean() - b.mean()) / sd if sd > 0 else 0.0
def eff_attr(conds_by, ys_by):
    es = []
    for it, t in TARGET.items():
        c, y = conds_by[it], ys_by[it]; b = y[c == 'binary']; a = y[c == 'attraction']; a = a[a != DECOY[it]]
        if len(a) < 5 or len(b) < 5: continue
        pa, pb = min(max((a == t).mean(), .02), .98), min(max((b == t).mean(), .02), .98); es.append(np.log(pa / (1 - pa)) - np.log(pb / (1 - pb)))
    return np.mean(es) if es else np.nan
ITEMS = ['default_green', 'default_organ', 'fair', 'frame', 'anch_africa', 'anch_redwood']
def effects(sub):
    out = {}
    for it in ITEMS:
        v = sub[it].dropna() if it in sub else pd.Series(dtype=object)
        if len(v): out[it] = eff(it, np.array([c for c, _ in v]), np.array([y for _, y in v]))
    cb, yb = {}, {}
    for it in TARGET:
        v = sub[it].dropna() if it in sub else pd.Series(dtype=object)
        cb[it], yb[it] = (np.array([c for c, _ in v]), np.array([y for _, y in v], dtype=object)) if len(v) else (np.array([]), np.array([], dtype=object))
    out['attraction'] = eff_attr(cb, yb) if all(len(cb[i]) for i in TARGET) else np.nan
    return out
def boot(sub, rng):
    n = len(sub); res = []
    for _ in range(B):
        idx = rng.integers(0, n, n); res.append(effects(sub.iloc[idx]))
    return pd.DataFrame(res)

rng = np.random.default_rng(2026); point, bs = {}, {}
for (m, a), sub in D.groupby(['model', 'arch']):
    sub = sub.reset_index(drop=True); point[(m, a)] = effects(sub); bs[(m, a)] = boot(sub, rng)
models = sorted({m for m, _ in point})
tab = []
for (m, a), e in point.items():
    for it, v in e.items():
        h = HUMAN['attraction' if it == 'attraction' else it]; lo, hi = np.nanpercentile(bs[(m, a)][it], [2.5, 97.5])
        tab.append(dict(model=m, arch=a, item=it, twin=v, human=h, D=v - h, D_lo=lo - h, D_hi=hi - h))
T = pd.DataFrame(tab); T.to_csv(f'{PRE}_effects.csv', index=False)
pd.set_option('display.width', 220, 'display.max_rows', 400); print(T.round(2).to_string(index=False))

def pooled(fun, arch_list):
    """fun(effects_dict_for_model) -> scalar; returns (per-model point, pooled point, ci, p)."""
    pts = []; bsd = []
    for m in models:
        e = [point[(m, a)] for a in arch_list if (m, a) in point]
        if len(e) != len(arch_list): continue
        pts.append(fun(*e)); bsd.append(np.array([fun(*[bs[(m, a)].iloc[i].to_dict() for a in arch_list]) for i in range(B)]))
    if not pts: return None
    bm = np.nanmean(np.vstack(bsd), axis=0); pm = float(np.nanmean(pts)); lo, hi = np.nanpercentile(bm, [2.5, 97.5])
    p = 2 * min((bm <= 0).mean(), (bm >= 0).mean()); return pts, pm, (lo, hi), max(p, 1 / B)
def verdict(pts, ci, positive=True):
    k = sum((v > 0) if positive else (v < 0) for v in pts if not np.isnan(v)); sign_ok = k >= 4; excl = (ci[0] > 0) if positive else (ci[1] < 0)
    return 'supported' if sign_ok and excl else ('partly supported' if sign_ok else 'not supported'), k
H = HUMAN; S = ['summary']; DM = ['demo']
tests = {
 'P1 framing D>0 (summary)': (lambda e: e['frame'] - H['frame'], S, True),
 'P1 anchoring D>0 (summary)': (lambda e: np.nanmean([e['anch_africa'] - H['anch_africa'], e['anch_redwood'] - H['anch_redwood']]), S, True),
 'P2a organ default D>0 (summary)': (lambda e: e['default_organ'] - H['default_organ'], S, True),
 'P2b green default D<=0 (summary)': (lambda e: e['default_green'] - H['default_green'], S, False),
 'P3 defaults D_green-D_organ<0 (summary)': (lambda e: (e['default_green'] - H['default_green']) - (e['default_organ'] - H['default_organ']), S, False),
 'P1 framing D>0 (demo, robustness)': (lambda e: e['frame'] - H['frame'], DM, True),
 'P1 anchoring D>0 (demo, robustness)': (lambda e: np.nanmean([e['anch_africa'] - H['anch_africa'], e['anch_redwood'] - H['anch_redwood']]), DM, True),
 'P2a organ default D>0 (demo, robustness)': (lambda e: e['default_organ'] - H['default_organ'], DM, True),
 'P2b green default D<=0 (demo, robustness)': (lambda e: e['default_green'] - H['default_green'], DM, False),
 'P3 defaults (demo, robustness)': (lambda e: (e['default_green'] - H['default_green']) - (e['default_organ'] - H['default_organ']), DM, False),
 'P6 theory minus demo, canonical paradigms': (lambda t, d: np.nanmean([(t['default_organ'] - d['default_organ']) / 100, t['frame'] - d['frame'], np.nanmean([t['anch_africa'], t['anch_redwood']]) - np.nanmean([d['anch_africa'], d['anch_redwood']])]), ['theory', 'demo'], True)}
out = []
for name, (fun, archs, pos) in tests.items():
    r = pooled(fun, archs)
    if r is None: continue
    pts, pm, ci, p = r; v, k = verdict(pts, ci, pos)
    out.append(dict(test=name, pooled=pm, ci_lo=ci[0], ci_hi=ci[1], models_in_predicted_direction=k, p_boot=p, verdict_unadjusted=v))
R = pd.DataFrame(out)
# Benjamini-Hochberg over the registered (non-robustness) tests
m_ = ~R.test.str.contains('robustness'); pv = R.loc[m_, 'p_boot'].values; o = np.argsort(pv); q = np.empty(len(pv)); prev = 1.0
for rank, i in reversed(list(enumerate(o, 1))): prev = min(prev, pv[i - 1] * len(pv) / rank); q[i - 1] = prev
R.loc[m_, 'q_BH'] = q; R.to_csv(f'{PRE}_propositions.csv', index=False); print('\n' + R.round(3).to_string(index=False))
