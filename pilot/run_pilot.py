"""Pilot: simulate mega-study participants with demographics-only personas through OpenRouter.
Usage: python3 run_pilot.py <data_dir> <out_dir> [n_per_study] [models comma-separated]
data_dir holds the three mega-study parquet files and wave1_3_response_label.csv.
Outputs raw.jsonl (one line per call, with token usage and cost) and prints parse and cost summaries."""
import sys, os, json, re, time, random, concurrent.futures as cf
import pandas as pd, requests
HDR = {'Authorization': 'Bearer ' + os.environ['OPENROUTER_API_KEY']} if os.environ.get('OPENROUTER_API_KEY') else {}   # set OPENROUTER_API_KEY to run; added after the studies for replication

D, OUT = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 20
MODELS = (sys.argv[4] if len(sys.argv) > 4 else 'anthropic/claude-haiku-5.5,openai/gpt-5.6-luna,google/gemini-3.7-flash').split(',')
STUDIES = ['default_eric', 'context_effects', 'targeting_fairness']
os.makedirs(OUT, exist_ok=True)

demo = pd.read_csv(f'{D}/wave1_3_response_label.csv', low_memory=False, usecols=['pid'] + [f'QID{i}' for i in range(11, 25)])
LAB = ['Region', 'Sex assigned at birth', 'Age group', 'Education', 'Race or origin', 'US citizen', 'Marital status', 'Religion',
       'Religious service attendance', 'Party identification', 'Family income', 'Political views', 'Household size', 'Employment']
demo['PID'] = 'pid_' + demo['pid'].astype(str); demo = demo.set_index('PID')

def persona(pid):
    r = demo.loc[pid]
    return '\n'.join(f'- {l}: {r[f"QID{11+i}"]}' for i, l in enumerate(LAB))

SYSTEM = ('You are simulating one specific US survey respondent, described below. Answer every question exactly as this person '
          'would, using their own judgment and typical behavior. Do not answer as an AI assistant and do not refuse. '
          'Follow the output format instructions exactly.\n\nRespondent profile (US adult panel, 2025):\n')

def qs(o, out):
    if isinstance(o, dict):
        if 'QuestionID' in o: out.append(o); return
        for v in o.values(): qs(v, out)
    elif isinstance(o, list):
        for v in o: qs(v, out)

def human_order(row):
    out = []; qs(json.loads(row['survey_json_with_human_response'])['Elements'], out)
    return [(q.get('QuestionName'), (q.get('Answers') or {}).get('SelectedByPosition')) for q in out if q.get('Answers')]

jobs = []
random.seed(7)
for st in STUDIES:
    d = pd.read_parquet(f'{D}/{st}-00000-of-00001.parquet')
    for _, r in d.sample(N, random_state=7).iterrows():
        if r['PID'] not in demo.index: continue
        ho = human_order(r)
        for m in MODELS: jobs.append(dict(study=st, pid=r['PID'], model=m, text=r['survey_text'], human=ho))

def call(j):
    body = dict(model=j['model'], temperature=0.7, max_tokens=1500, usage={'include': True},
                messages=[{'role': 'system', 'content': SYSTEM + persona(j['pid'])}, {'role': 'user', 'content': j['text']}])
    for k in range(3):
        try:
            r = requests.post('https://openrouter.ai/api/v1/chat/completions', headers=HDR, json=body, timeout=180)
            if r.status_code == 200:
                x = r.json(); u = x.get('usage', {})
                return dict(study=j['study'], pid=j['pid'], model=j['model'], content=x['choices'][0]['message'].get('content'),
                            cost=u.get('cost'), ptok=u.get('prompt_tokens'), ctok=u.get('completion_tokens'), human=j['human'])
            err = f'{r.status_code} {r.text[:200]}'
        except Exception as e: err = str(e)
        time.sleep(2 ** k)
    return dict(study=j['study'], pid=j['pid'], model=j['model'], content=None, error=err, cost=0, human=j['human'])

with cf.ThreadPoolExecutor(8) as ex: res = list(ex.map(call, jobs))
with open(f'{OUT}/raw.jsonl', 'w') as f:
    for r in res: f.write(json.dumps(r) + '\n')

def parse(c):
    if not c: return None
    m = re.search(r'\{.*\}', c, re.S)
    try: return json.loads(m.group(0)) if m else None
    except Exception: return None

rows = []
for r in res:
    p = parse(r['content']); ok = p is not None
    agree = n = 0
    if ok:
        for k, (qn, hpos) in enumerate(r['human'], 1):
            a = (p.get(f'Q{k}') or {}).get('Answers', {}); pos = a.get('SelectedByPosition')
            if hpos is not None and pos is not None: n += 1; agree += int(pos == hpos)
    rows.append(dict(study=r['study'], model=r['model'], ok=ok, cost=r.get('cost') or 0, ptok=r.get('ptok'), ctok=r.get('ctok'), agree=agree, n=n))
s = pd.DataFrame(rows)
print(s.groupby(['study', 'model']).agg(calls=('ok', 'size'), parsed=('ok', 'mean'), cost=('cost', 'sum'), ptok=('ptok', 'mean'), ctok=('ctok', 'mean'), agree=('agree', 'sum'), n=('n', 'sum')).round(4).to_string())
print('TOTAL cost', round(s.cost.sum(), 4), 'calls', len(s))
