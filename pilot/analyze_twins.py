"""Twin vs human effects for the three mega-study experiments from run_full.py output.
Usage: python3 analyze_twins.py <data_dir> <raw.jsonl> <out_csv>
Conditions and outcomes are coded from the displayed survey text, never from EmbeddedData tags."""
import sys, re, json
import numpy as np, pandas as pd
from scipy import stats

D, RAW, OUTCSV = sys.argv[1:4]
TARGET = {'TV': 'HD-558', 'Printer': '1000AX', 'Cell': 'X-3A'}
DECOY = {'Hal-B', 'L22', '5C-S'}

def blocks(text):
    parts = re.split(r'\nQ(\d+):\s*', '\n' + text)
    return {int(parts[i]): parts[i + 1] for i in range(1, len(parts) - 1, 2)}

def opts(b):
    m = re.search(r'Options:\n((?:\s+\d+ - .*\n?)+)', b)
    return {int(a): t.strip() for a, t in re.findall(r'\s+(\d+) - (.*)', m.group(1))} if m else {}

def classify(study, b, full=''):
    """Return (item, condition) for a question block."""
    o = opts(b); ot = list(o.values())
    if study == 'default_eric':
        if 'electric' in b: return 'green', ('optout' if ot[0].startswith('Stay with GreenGrid') else 'optin')
        if 'organ donor' in b: return 'organ', ('optout' if 'is considered to be an organ donor' in b else 'optin')
    if study == 'context_effects':
        for k, w in [('TV', 'Scenario: Television'), ('Printer', 'Scenario: Printer'), ('Cell', 'Scenario: Cellphone')]:
            if w in b:
                if len(ot) == 2: return k, 'binary'
                return k, ('attraction' if set(ot) & DECOY else 'compromise')
    if study == 'targeting_fairness' and 'How fair is this advertising plan' in b:
        return 'fair', ('targeted' if 'advertise the snacks to women directly' in (full or b) else 'broad')
    return None, None

def outcome(item, b, sel_pos, sel_text):
    o = opts(b)
    txt = o.get(sel_pos) if sel_pos in o else sel_text
    if txt is None: return np.nan
    if item == 'organ': return float(txt.startswith('You are therefore currently a potential donor') or (txt.startswith('If you wish to change') and 'not to be an organ donor' in b))
    if item == 'green': return float(txt.startswith('Stay with GreenGrid') or txt.startswith('Switch to GreenGrid'))
    if item == 'fair': m = re.match(r'(\d)', txt.strip()); return float(m.group(1)) if m else np.nan
    return txt   # choice sets: the chosen product name

# human data (same coding)
H = []
for st in ['default_eric', 'context_effects', 'targeting_fairness']:
    d = pd.read_parquet(f'{D}/{st}-00000-of-00001.parquet')
    for _, r in d.iterrows():
        bl = blocks(r['survey_text']); j = json.loads(r['survey_json_with_human_response'])
        ans = []
        def walk(o):
            if isinstance(o, dict):
                if 'QuestionID' in o:
                    if o.get('Answers') and not o.get('is_descriptive'): ans.append(o['Answers'])
                    return
                for v in o.values(): walk(v)
            elif isinstance(o, list):
                for v in o: walk(v)
        walk(j['Elements'])
        for (k, b), a in zip(sorted(bl.items()), ans):
            item, cond = classify(st, b, r['survey_text'])
            if item: H.append(dict(source='human', study=st, pid=r['PID'], item=item, cond=cond, y=outcome(item, b, a.get('SelectedByPosition'), a.get('SelectedText'))))
human = pd.DataFrame(H)

T = []
texts = {}
for st in ['default_eric', 'context_effects', 'targeting_fairness']:
    d = pd.read_parquet(f'{D}/{st}-00000-of-00001.parquet'); texts[(st)] = dict(zip(d.PID, d.survey_text))
bad = 0
for l in open(RAW):
    x = json.loads(l); m = re.search(r'\{.*\}', x['content'] or '', re.S)
    try: p = json.loads(m.group(0))
    except Exception: bad += 1; continue
    bl = blocks(texts[x['study']][x['pid']])
    for k, b in bl.items():
        item, cond = classify(x['study'], b, texts[x['study']][x['pid']]); a = (p.get(f'Q{k}') or {}).get('Answers', {})
        if item and a: T.append(dict(source=f"{x['model']}|{x['arch']}", study=x['study'], pid=x['pid'], rep=x['rep'], item=item, cond=cond,
                                    y=outcome(item, b, a.get('SelectedByPosition'), a.get('SelectedText'))))
twin = pd.DataFrame(T); print('unparsed responses', bad, 'twin rows', len(twin), 'human rows', len(human))

def eff(df):
    """Return dict of effect measures for one source."""
    out = {}
    for item, hi, lo in [('green', 'optout', 'optin'), ('organ', 'optout', 'optin')]:
        a, b = df[(df.item == item) & (df.cond == hi)].y.dropna(), df[(df.item == item) & (df.cond == lo)].y.dropna()
        if len(a) > 5 and len(b) > 5:
            p1, p0 = a.mean(), b.mean(); out[f'default_{item}_pp'] = 100 * (p1 - p0)
    ests = []
    for k, tgt in TARGET.items():
        b = df[(df.item == k) & (df.cond == 'binary')].y.dropna()
        a = df[(df.item == k) & (df.cond == 'attraction')].y.dropna(); a = a[~a.isin(DECOY)]
        if len(a) > 5 and len(b) > 5:
            pa, pb = (a == tgt).mean(), (b == tgt).mean()
            if 0 < pa < 1 and 0 < pb < 1: ests.append(np.log(pa / (1 - pa)) - np.log(pb / (1 - pb)))
    if ests: out['attraction_logOR'] = float(np.mean(ests))
    a, b = df[(df.item == 'fair') & (df.cond == 'targeted')].y.dropna(), df[(df.item == 'fair') & (df.cond == 'broad')].y.dropna()
    if len(a) > 5 and len(b) > 5:
        sd = np.sqrt(((len(a) - 1) * a.var() + (len(b) - 1) * b.var()) / (len(a) + len(b) - 2)); out['fair_d'] = (a.mean() - b.mean()) / sd if sd > 0 else np.nan
    return out

rows = [dict(source='human', **eff(human))]
for s, g in twin.groupby('source'): rows.append(dict(source=s, n_rows=len(g), **eff(g)))
res = pd.DataFrame(rows); res.to_csv(OUTCSV, index=False)
pd.set_option('display.width', 220, 'display.max_columns', 20)
print(res.round(2).to_string(index=False))
