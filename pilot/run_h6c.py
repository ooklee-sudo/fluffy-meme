"""Confirmatory H6 grid (AsPredicted #320110, P4-P5): new respondents, C1 booklet, two factual batteries.
Usage: python3 run_h6c.py <data_dir> <out_dir> [n_respondents] [stop_usd]
Respondents: Twin-2K-500 participants outside every mega-study file and outside the C1 sample (seed 2026). Cells: model x effort x temperature (36 cells).
Per respondent per cell: C1 booklet (cue-based effects), battery A (16 answerable + 10 invented, abstain nudge), battery B (10 new invented items, no nudge)."""
import sys, os, json, time, random, threading, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd, requests
HDR = {'Authorization': 'Bearer ' + os.environ['OPENROUTER_API_KEY']} if os.environ.get('OPENROUTER_API_KEY') else {}   # set OPENROUTER_API_KEY to run; added after the studies for replication
from h6_battery import ANSWERABLE, INVENTED, INVENTED2, ABSTAIN
D, OUT = sys.argv[1], sys.argv[2]; NR = int(sys.argv[3]) if len(sys.argv) > 3 else 100; STOP = float(sys.argv[4]) if len(sys.argv) > 4 else 60.0
os.environ['C1_DRY'] = '1'; sys.argv = ['run_c1', D, os.path.join(OUT, '_c1unused'), '600']
ns = {'__name__': 'c1lib', '__file__': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'run_c1.py')}
exec(open(ns['__file__']).read(), ns); booklet, render, system, pool, c1pids = ns['booklet'], ns['render'], ns['system'], ns['pool'], ns['pids']
LEVELS = {'anthropic/claude-haiku-5.5': ['none', 'low', 'high'], 'openai/gpt-5.6-luna': ['none', 'low', 'high'], 'x-ai/grok-4.3': ['none', 'low', 'high'], 'google/gemini-3.7-flash': ['low', 'medium', 'high']}
TEMPS = [0.0, 0.7, 1.2]; RAW = f'{OUT}/raw.jsonl'
rest = sorted(set(pool) - set(c1pids)); pids = random.Random(2026).sample(rest, min(NR, len(rest))); print('respondents', len(pids), 'of unused', len(rest), flush=True)

def battery(pid, which):
    rng = random.Random(f'{pid}-{which}-battery')
    items = ([(q, o, k, 'answerable') for q, o, k in ANSWERABLE] + [(q, o, None, 'invented') for q, o in INVENTED]) if which == 'A' else [(q, o, None, 'invented') for q, o in INVENTED2]
    rng.shuffle(items); qs, text, tmpl = [], [], {}
    for n, (q, o, k, kind) in enumerate(items, 1):
        o = list(o); rng.shuffle(o); o.append(ABSTAIN); qs.append(dict(q=q, opts=o, key=k, kind=kind))
        text.append(f'Q{n}:\n{q}\nQuestion Type: Single Choice\nOptions:\n' + '\n'.join(f'  {i} - {x}' for i, x in enumerate(o, 1)) + '\nAnswer: [Masked]'); tmpl[f'Q{n}'] = {'Answers': {'SelectedByPosition': 'Masked'}}
    lead = ('Please answer the following general-knowledge questions as this person would. If you are not sure, or cannot verify that something exists, choose the last option.\n\n' if which == 'A'
            else 'Please answer the following general-knowledge questions as this person would.\n\n')
    return qs, lead + '\n\n'.join(text) + '\n\n### Format Instructions:\nGenerate a JSON object filling in the Masked values for %d questions, with the option position as a number.\n\n' % len(qs) + json.dumps(tmpl, indent=2)

done = set()
if os.path.exists(RAW):
    for l in open(RAW):
        try: x = json.loads(l); done.add((x['task'], x['pid'], x['model'], x['effort'], x['temp']))
        except Exception: pass
jobs = [dict(task=t, pid=p, model=m, effort=e, temp=tp) for m, lv in LEVELS.items() for e in lv for tp in TEMPS for p in pids for t in ('booklet', 'battA', 'battB') if (t, p, m, e, tp) not in done]
random.Random(9).shuffle(jobs); print('jobs', len(jobs), flush=True)
lock = threading.Lock(); spent = [0.0]; halt = threading.Event(); cnt = [0]
def call(j):
    if halt.is_set(): return
    qs = conds = None
    if j['task'] == 'booklet': conds, qs = booklet(j['pid']); prompt = render(qs); sysm = system(j['pid'], 'demo')
    else: qs, prompt = battery(j['pid'], j['task'][-1]); sysm = system(j['pid'], 'demo')
    body = dict(model=j['model'], temperature=j['temp'], max_tokens=6000, usage={'include': True}, reasoning={'effort': j['effort']}, messages=[{'role': 'system', 'content': sysm}, {'role': 'user', 'content': prompt}])
    err = None
    for k in range(5):
        try:
            r = requests.post('https://openrouter.ai/api/v1/chat/completions', headers=HDR, json=body, timeout=300)
            if r.status_code == 200:
                x = r.json(); u = x.get('usage', {})
                rec = dict(task=j['task'], pid=j['pid'], model=j['model'], effort=j['effort'], temp=j['temp'], content=x['choices'][0]['message'].get('content'), cost=u.get('cost') or 0, qs=qs, conds=conds)
                with lock:
                    open(RAW, 'a').write(json.dumps(rec) + '\n'); spent[0] += rec['cost']; cnt[0] += 1
                    if cnt[0] % 500 == 0: print(f'done {cnt[0]} spent ${spent[0]:.2f}', flush=True)
                    if spent[0] >= STOP: halt.set(); print('HALT', spent[0], flush=True)
                return
            err = f'{r.status_code} {r.text[:150]}'
        except Exception as e: err = str(e)
        time.sleep(2 ** (k + 1))
    with lock: open(f'{OUT}/errors.jsonl', 'a').write(json.dumps(dict(key=[j['task'], j['pid'], j['model'], j['effort'], j['temp']], err=err)) + '\n')
if __name__ == '__main__': 
    os.makedirs(OUT, exist_ok=True)
    with cf.ThreadPoolExecutor(64) as ex: list(ex.map(call, jobs))
    print(f'FINISHED spent ${spent[0]:.2f} calls {cnt[0]}', flush=True)
