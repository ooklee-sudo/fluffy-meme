"""H6: vary reasoning effort and temperature within model families; measure bias magnitude and hallucination on the same respondents.
Usage: python3 run_h6.py <data_dir> <out_dir> [n_per_study] [n_battery] [stop_usd]
Cells per model: 3 reasoning levels x 3 temperatures (0, 0.7, 1.2). Bias tasks reuse the mega-study survey_text; the battery is a separate call."""
import sys, os, json, time, random, threading, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd, requests
from h6_battery import ANSWERABLE, INVENTED, ABSTAIN
D, OUT = sys.argv[1], sys.argv[2]
NS = int(sys.argv[3]) if len(sys.argv) > 3 else 100
NB = int(sys.argv[4]) if len(sys.argv) > 4 else 100
STOP = float(sys.argv[5]) if len(sys.argv) > 5 else 80.0
LEVELS = {'anthropic/claude-haiku-5.5': ['none', 'low', 'high'], 'openai/gpt-5.6-luna': ['none', 'low', 'high'],
          'x-ai/grok-4.3': ['none', 'low', 'high'], 'google/gemini-3.7-flash': ['low', 'medium', 'high']}
TEMPS = [0.0, 0.7, 1.2]
os.makedirs(OUT, exist_ok=True); RAW = f'{OUT}/raw.jsonl'
demo = pd.read_csv(f'{D}/wave1_3_response_label.csv', low_memory=False, usecols=['pid'] + [f'QID{i}' for i in range(11, 25)])
LAB = ['Region', 'Sex assigned at birth', 'Age group', 'Education', 'Race or origin', 'US citizen', 'Marital status', 'Religion', 'Religious service attendance', 'Party identification', 'Family income', 'Political views', 'Household size', 'Employment']
demo['PID'] = 'pid_' + demo['pid'].astype(str); demo = demo.set_index('PID')
HEAD = ('You are simulating one specific US survey respondent, described below. Answer every question exactly as this person would, using their own judgment and typical behavior. Do not answer as an AI assistant and do not refuse. Follow the output format instructions exactly.\n\nRespondent profile (US adult panel, 2025):\n')
def system(pid):
    r = demo.loc[pid]; return HEAD + '\n'.join(f'- {l}: {r[f"QID{11+i}"]}' for i, l in enumerate(LAB))

def battery(pid):
    rng = random.Random(f'{pid}-battery'); items = [(q, o, k, 'answerable') for q, o, k in ANSWERABLE] + [(q, o, None, 'invented') for q, o in INVENTED]
    rng.shuffle(items); qs, text = [], []; tmpl = {}
    for n, (q, o, k, kind) in enumerate(items, 1):
        o = list(o); rng.shuffle(o); o.append(ABSTAIN)
        qs.append(dict(q=q, opts=o, key=k, kind=kind))
        text.append(f'Q{n}:\n{q}\nQuestion Type: Single Choice\nOptions:\n' + '\n'.join(f'  {i} - {x}' for i, x in enumerate(o, 1)) + '\nAnswer: [Masked]')
        tmpl[f'Q{n}'] = {'Answers': {'SelectedByPosition': 'Masked'}}
    prompt = 'Please answer the following general-knowledge questions as this person would. If you are not sure, or cannot verify that something exists, choose the last option.\n\n' + '\n\n'.join(text) + \
             '\n\n### Format Instructions:\nGenerate a JSON object filling in the Masked values for %d questions, with the option position as a number.\n\n' % len(qs) + json.dumps(tmpl, indent=2)
    return qs, prompt

pool = {}
for st in ['default_eric', 'context_effects', 'targeting_fairness']:
    d = pd.read_parquet(f'{D}/{st}-00000-of-00001.parquet').sample(NS, random_state=21)
    pool[st] = list(zip(d.PID, d.survey_text))
bpids = sorted(demo.index[:0].tolist() or {p for v in pool.values() for p, _ in v}); random.Random(4).shuffle(bpids); bpids = bpids[:NB]

done = set()
if os.path.exists(RAW):
    for l in open(RAW):
        try: x = json.loads(l); done.add((x['task'], x['pid'], x['model'], x['effort'], x['temp']))
        except Exception: pass
jobs = []
for m, levels in LEVELS.items():
    for e in levels:
        for t in TEMPS:
            for st, rows in pool.items():
                for pid, text in rows:
                    if (st, pid, m, e, t) not in done: jobs.append(dict(task=st, pid=pid, model=m, effort=e, temp=t, prompt=text))
            for pid in bpids:
                if ('battery', pid, m, e, t) not in done: jobs.append(dict(task='battery', pid=pid, model=m, effort=e, temp=t, prompt=None))
random.Random(9).shuffle(jobs); print('jobs', len(jobs), flush=True)
lock = threading.Lock(); spent = [0.0]; halt = threading.Event(); cnt = [0]
def call(j):
    if halt.is_set(): return
    qs = None; prompt = j['prompt']
    if j['task'] == 'battery': qs, prompt = battery(j['pid'])
    body = dict(model=j['model'], temperature=j['temp'], max_tokens=6000, usage={'include': True}, reasoning={'effort': j['effort']},
                messages=[{'role': 'system', 'content': system(j['pid'])}, {'role': 'user', 'content': prompt}])
    err = None
    for k in range(5):
        try:
            r = requests.post('https://openrouter.ai/api/v1/chat/completions', json=body, timeout=300)
            if r.status_code == 200:
                x = r.json(); u = x.get('usage', {})
                rec = dict(task=j['task'], pid=j['pid'], model=j['model'], effort=j['effort'], temp=j['temp'], content=x['choices'][0]['message'].get('content'),
                           cost=u.get('cost') or 0, rtok=(u.get('completion_tokens_details') or {}).get('reasoning_tokens'), ctok=u.get('completion_tokens'), qs=qs)
                with lock:
                    open(RAW, 'a').write(json.dumps(rec) + '\n'); spent[0] += rec['cost']; cnt[0] += 1
                    if cnt[0] % 500 == 0: print(f'done {cnt[0]} spent ${spent[0]:.2f}', flush=True)
                    if spent[0] >= STOP: halt.set(); print('HALT', spent[0], flush=True)
                return
            err = f'{r.status_code} {r.text[:150]}'
        except Exception as e: err = str(e)
        time.sleep(2 ** (k + 1))
    with lock: open(f'{OUT}/errors.jsonl', 'a').write(json.dumps(dict(key=[j['task'], j['pid'], j['model'], j['effort'], j['temp']], err=err)) + '\n')
with cf.ThreadPoolExecutor(64) as ex: list(ex.map(call, jobs))
print(f'FINISHED spent ${spent[0]:.2f} calls {cnt[0]}', flush=True)
