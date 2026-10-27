"""Stability study (exploratory, not part of the registrations): same respondents, two prompt templates, several generations per model family.
Usage: python3 run_gen.py <data_dir> <out_dir> [n_respondents] [stop_usd]
Respondents: Twin-2K-500 participants outside every mega-study file, the C1 sample, and the H6 confirmatory sample (seed 2026 draw from the remainder).
Persona architecture: persona summary. Template B = C1 format; template A = original survey-text format with a different system prompt."""
import sys, os, json, time, random, threading, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd, requests
HDR = {'Authorization': 'Bearer ' + os.environ['OPENROUTER_API_KEY']} if os.environ.get('OPENROUTER_API_KEY') else {}   # set OPENROUTER_API_KEY to run; added after the studies for replication
D, OUT = sys.argv[1], sys.argv[2]; NR = int(sys.argv[3]) if len(sys.argv) > 3 else 300; STOP = float(sys.argv[4]) if len(sys.argv) > 4 else 120.0
os.environ['C1_DRY'] = '1'; sys.argv = ['run_c1', D, os.path.join(OUT, '_c1unused'), '600']
ns = {'__name__': 'c1lib', '__file__': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'run_c1.py')}
exec(open(ns['__file__']).read(), ns); booklet, render_B, system_B, pool, c1pids, summ = ns['booklet'], ns['render'], ns['system'], ns['pool'], ns['pids'], ns['summ']
MODELS = {'gemini-flash': ['google/gemini-3.5-flash', 'google/gemini-3.6-flash', 'google/gemini-3.7-flash'], 'grok': ['x-ai/grok-4.3', 'x-ai/grok-4.5', 'x-ai/grok-4.7'],
          'claude-haiku': ['anthropic/claude-haiku-4.5', 'anthropic/claude-haiku-5.5'], 'claude-sonnet': ['anthropic/claude-sonnet-5', 'anthropic/claude-sonnet-5.5'],
          'gpt': ['openai/gpt-5.2', 'openai/gpt-5.4', 'openai/gpt-5.5']}
ALL = [m for v in MODELS.values() for m in v]; RAW = f'{OUT}/raw.jsonl'
h6used = set()   # H6 confirmatory respondents (same draw as run_h6c)
rest = sorted(set(pool) - set(c1pids)); h6used = set(random.Random(2026).sample(rest, min(100, len(rest))))
rest = sorted(set(rest) - h6used); pids = random.Random(2027).sample(rest, min(NR, len(rest))); print('respondents', len(pids), flush=True)
HEAD_A = ('You are simulating one specific US survey respondent, described below. Answer every question exactly as this person would, using their own judgment and typical behavior. '
          'Do not answer as an AI assistant and do not refuse. Follow the output format instructions exactly.\n\nRespondent profile (US adult panel, 2025):\n')
def render_A(qs):
    out, tmpl = [], {}
    for n, q in enumerate(qs, 1):
        if q['opts']:
            out.append(f'Q{n}:\n{q["text"]}\nQuestion Type: Single Choice\nOptions:\n' + '\n'.join(f'  {i} - {o}' for i, o in enumerate(q['opts'], 1)) + '\nAnswer: [Masked]')
            tmpl[f'Q{n}'] = {'Question Type': 'Single Choice', 'Answers': {'SelectedByPosition': 'Masked', 'SelectedText': 'Masked'}}
        else:
            out.append(f'Q{n}:\n{q["text"]}\nQuestion Type: Numeric Entry\nAnswer: [Masked]'); tmpl[f'Q{n}'] = {'Question Type': 'Numeric Entry', 'Answers': {'Value': 'Masked'}}
    return '\n\n'.join(out) + '\n\n### Format Instructions:\nGenerate a JSON object filling in the Masked values for %d questions. For single-choice questions give the option position and text; for numeric questions give one number.\n\n' % len(qs) + json.dumps(tmpl, indent=2)
done = set()
if os.path.exists(RAW):
    for l in open(RAW):
        try: x = json.loads(l); done.add((x['pid'], x['model'], x['template']))
        except Exception: pass
jobs = [(p, m, t) for p in pids for m in ALL for t in ('A', 'B') if (p, m, t) not in done]; random.Random(5).shuffle(jobs); print('jobs', len(jobs), flush=True)
lock = threading.Lock(); spent = [0.0]; halt = threading.Event(); cnt = [0]
def call(job):
    if halt.is_set(): return
    pid, m, t = job; conds, qs = booklet(pid)
    sysm = system_B(pid, 'summary') if t == 'B' else HEAD_A + summ[pid]; user = render_B(qs) if t == 'B' else render_A(qs)
    body = dict(model=m, temperature=0.7, max_tokens=3000, usage={'include': True}, reasoning={'effort': 'low'}, messages=[{'role': 'system', 'content': sysm}, {'role': 'user', 'content': user}])
    err = None
    for k in range(5):
        try:
            r = requests.post('https://openrouter.ai/api/v1/chat/completions', headers=HDR, json=body, timeout=300)
            if r.status_code == 200:
                x = r.json(); u = x.get('usage', {})
                rec = dict(pid=pid, model=m, template=t, content=x['choices'][0]['message'].get('content'), cost=u.get('cost') or 0, conds=conds, qs=qs)
                with lock:
                    open(RAW, 'a').write(json.dumps(rec) + '\n'); spent[0] += rec['cost']; cnt[0] += 1
                    if cnt[0] % 500 == 0: print(f'done {cnt[0]} spent ${spent[0]:.2f}', flush=True)
                    if spent[0] >= STOP: halt.set(); print('HALT', spent[0], flush=True)
                return
            err = f'{r.status_code} {r.text[:150]}'
        except Exception as e: err = str(e)
        time.sleep(2 ** (k + 1))
    with lock: open(f'{OUT}/errors.jsonl', 'a').write(json.dumps(dict(key=list(job), err=err)) + '\n')
if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    with cf.ThreadPoolExecutor(48) as ex: list(ex.map(call, jobs))
    print(f'FINISHED spent ${spent[0]:.2f} calls {cnt[0]}', flush=True)
