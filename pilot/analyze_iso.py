"""Classic vs isomorphic/platform twin effects from run_iso.py output.
Usage: python3 analyze_iso.py <raw.jsonl> <out_csv> [bootstrap_reps]"""
import sys, re, json
import numpy as np, pandas as pd
RAW, OUTCSV = sys.argv[1], sys.argv[2]; B = int(sys.argv[3]) if len(sys.argv) > 3 else 300
CLASSIC = {'framing': ['frame_classic'], 'anchoring': ['anch_africa', 'anch_redwood'], 'defaults': ['default_organ'], 'fairness': ['ult_classic']}
ISO = {'framing': ['frame_iso'], 'anchoring': ['anch_unesco', 'anch_danube'], 'defaults': ['default_savings'], 'fairness': ['ult_roommate'], 'decoys': ['decoy_earbuds', 'decoy_course']}
PLAT = {'defaults': ['default_platform'], 'fairness': ['ult_platform'], 'decoys': ['decoy_cloud']}
TARGET = {'decoy_earbuds': 'Pulse 3', 'decoy_cloud': 'Plus', 'decoy_course': 'Python Bootcamp'}
DECOY = {'decoy_earbuds': 'Pulse 2', 'decoy_cloud': 'Plus Lite', 'decoy_course': 'Python Basics Plus'}
rows, bad = [], 0
for l in open(RAW):
    x = json.loads(l); m = re.search(r'\{.*\}', x['content'] or '', re.S)
    try: p = json.loads(m.group(0))
    except Exception: bad += 1; continue
    for n, q in enumerate(x['qs'], 1):
        a = (p.get(f'Q{n}') or {}).get('Answers') or {}
        if q['opts']:
            pos = a.get('SelectedByPosition')
            try: pos = int(pos)
            except Exception: continue
            if not 1 <= pos <= len(q['opts']): continue
            rows.append(dict(pid=x['pid'], src=f"{x['model']}|{x['arch']}", item=q['item'], qi=q['qi'], cond=x['conds'][q['item']], pos=pos, txt=q['opts'][pos - 1], num=np.nan))
        else:
            try: v = float(str(a.get('Value')).replace(',', ''))
            except Exception: continue
            rows.append(dict(pid=x['pid'], src=f"{x['model']}|{x['arch']}", item=q['item'], qi=q['qi'], cond=x['conds'][q['item']], pos=np.nan, txt=None, num=v))
df = pd.DataFrame(rows); print('unparsed', bad, 'answers', len(df))

def d_of(a, b):
    a, b = a.dropna(), b.dropna()
    if len(a) < 5 or len(b) < 5: return np.nan
    sd = np.sqrt(((len(a) - 1) * a.var() + (len(b) - 1) * b.var()) / (len(a) + len(b) - 2)); return (a.mean() - b.mean()) / sd if sd > 0 else 0.0
def effect(g, item):
    c = g[g.item == item]
    if item.startswith('frame'): return d_of(c[c.cond == 'loss'].pos, c[c.cond == 'gain'].pos)
    if item.startswith('anch'):
        c = c[c.qi == 1]; return d_of(np.log10(c[c.cond == 'high'].num.clip(lower=1)), np.log10(c[c.cond == 'low'].num.clip(lower=1)))
    if item.startswith('default'):
        o = c[c.cond == 'optout']; i = c[c.cond == 'optin']
        if len(o) < 5 or len(i) < 5: return np.nan
        return 100 * ((o.pos == 1).mean() - (i.pos == 2).mean())
    if item.startswith('ult'):
        lo, fa = c[c.cond == 'low'], c[c.cond == 'fair']
        if len(lo) < 5 or len(fa) < 5: return np.nan
        return 100 * ((lo.pos == 2).mean() - (fa.pos == 2).mean())
    if item.startswith('decoy'):
        t = TARGET[item]; b = c[c.cond == 'binary'].txt; a = c[c.cond == 'attraction'].txt; a = a[a != DECOY[item]]
        if len(a) < 5 or len(b) < 5: return np.nan
        pa, pb = (a == t).mean(), (b == t).mean(); pa, pb = min(max(pa, .01), .99), min(max(pb, .01), .99)
        return np.log(pa / (1 - pa)) - np.log(pb / (1 - pb))
def pooled(g, items): return np.nanmean([effect(g, i) for i in items])
UNIT = {'framing': 'd', 'anchoring': 'd(log)', 'defaults': 'pp', 'fairness': 'pp reject', 'decoys': 'logOR'}
out = []
for src, g in df.groupby('src'):
    pids = g.pid.unique(); byp = {k: v for k, v in g.groupby('pid')}; rng = np.random.default_rng(3)
    for ph in ['framing', 'anchoring', 'defaults', 'fairness', 'decoys']:
        cl = pooled(g, CLASSIC.get(ph, [])) if ph in CLASSIC else np.nan; io = pooled(g, ISO[ph]); pl = pooled(g, PLAT[ph]) if ph in PLAT else np.nan
        diffs = []
        if ph in CLASSIC:
            for _ in range(B):
                s = pd.concat([byp[k] for k in rng.choice(pids, len(pids))]); diffs.append(pooled(s, ISO[ph]) - pooled(s, CLASSIC[ph]))
            lo, hi = np.nanpercentile(diffs, [2.5, 97.5])
        else: lo = hi = np.nan
        out.append(dict(src=src, phenomenon=ph, unit=UNIT[ph], classic=cl, iso=io, platform=pl, iso_minus_classic=io - cl if ph in CLASSIC else np.nan, ci_lo=lo, ci_hi=hi, n_pid=len(pids)))
res = pd.DataFrame(out); res.to_csv(OUTCSV, index=False)
pd.set_option('display.width', 250, 'display.max_columns', 20, 'display.max_rows', 200)
print(res.round(2).to_string(index=False))
