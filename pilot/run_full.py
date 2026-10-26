"""Full twin simulation of the three mega-study experiments via OpenRouter, with checkpointing and a cost guard.
Usage: python3 run_full.py <data_dir> <out_dir> [stop_usd]
Architectures: demo (demographics only, 2 draws), summary (Twin-2K-500 persona summary, 2 draws),
theory (demographics plus the phenomenon named, 1 draw). Appends to <out_dir>/raw.jsonl; rerun resumes."""
import sys, os, json, time, threading, concurrent.futures as cf
import pandas as pd, requests

D, OUT = sys.argv[1], sys.argv[2]
STOP = float(sys.argv[3]) if len(sys.argv) > 3 else 300.0
MODELS = ['anthropic/claude-haiku-5.5', 'openai/gpt-5.6-luna', 'google/gemini-3.7-flash', 'x-ai/grok-4.3', 'meta-llama/llama-4-maverick']
STUDIES = {'default_eric': 'how people respond to default options (opt-in versus opt-out enrollment)',
           'context_effects': 'how adding a third option to a choice set changes choices (attraction and compromise effects)',
           'targeting_fairness': 'how fair people judge demographically targeted versus broad advertising'}
ARCH = [('demo', 2), ('theory', 1), ('summary', 2)]
os.makedirs(OUT, exist_ok=True); RAW = f'{OUT}/raw.jsonl'

demo = pd.read_csv(f'{D}/wave1_3_response_label.csv', low_memory=False, usecols=['pid'] + [f'QID{i}' for i in range(11, 25)])
LAB = ['Region', 'Sex assigned at birth', 'Age group', 'Education', 'Race or origin', 'US citizen', 'Marital status', 'Religion',
       'Religious service attendance', 'Party identification', 'Family income', 'Political views', 'Household size', 'Employment']
demo['PID'] = 'pid_' + demo['pid'].astype(str); demo = demo.set_index('PID')
summ = pd.read_parquet(f'{D}/persona_summary.parquet').set_index('PID')['persona_summary']

def profile(pid, arch):
    if arch == 'summary': return summ[pid]
    r = demo.loc[pid]; return '\n'.join(f'- {l}: {r[f"QID{11+i}"]}' for i, l in enumerate(LAB))

HEAD = ('You are simulating one specific US survey respondent, described below. Answer every question exactly as this person '
        'would, using their own judgment and typical behavior. Do not answer as an AI assistant and do not refuse. '
        'Follow the output format instructions exactly.\n\n')

def system(pid, arch, study):
    s = HEAD + 'Respondent profile (US adult panel, 2025):\n' + profile(pid, arch)
    if arch == 'theory': s += f'\n\nResearch note: this survey studies {STUDIES[study]}. Respond as the real person would.'
    return s

done = set()
if os.path.exists(RAW):
    for l in open(RAW):
        try: x = json.loads(l); done.add((x['study'], x['pid'], x['model'], x['arch'], x['rep']))
        except Exception: pass
jobs = []
for st in STUDIES:
    d = pd.read_parquet(f'{D}/{st}-00000-of-00001.parquet')
    for arch, reps in ARCH:
        for _, r in d.iterrows():
            for m in MODELS:
                for rep in range(reps):
                    k = (st, r['PID'], m, arch, rep)
                    if k not in done: jobs.append((k, r['survey_text']))
import random; random.Random(7).shuffle(jobs)   # any prefix is a random sample across models, architectures, studies
print('jobs to run', len(jobs), 'already done', len(done), flush=True)

lock = threading.Lock(); spent = [0.0]; halt = threading.Event(); n_done = [0]
def call(job):
    if halt.is_set(): return
    (st, pid, m, arch, rep), text = job
    body = dict(model=m, temperature=0.7, max_tokens=1500, usage={'include': True}, reasoning={'effort': 'low'},
                messages=[{'role': 'system', 'content': system(pid, arch, st)}, {'role': 'user', 'content': text}])
    err = None
    for k in range(5):
        try:
            r = requests.post('https://openrouter.ai/api/v1/chat/completions', json=body, timeout=240)
            if r.status_code == 200:
                x = r.json(); u = x.get('usage', {})
                rec = dict(study=st, pid=pid, model=m, arch=arch, rep=rep, content=x['choices'][0]['message'].get('content'),
                           cost=u.get('cost') or 0, ptok=u.get('prompt_tokens'), ctok=u.get('completion_tokens'))
                with lock:
                    open(RAW, 'a').write(json.dumps(rec) + '\n'); spent[0] += rec['cost']; n_done[0] += 1
                    if n_done[0] % 500 == 0: print(f'done {n_done[0]} spent ${spent[0]:.2f}', flush=True)
                    if spent[0] >= STOP: halt.set(); print(f'HALT: spent ${spent[0]:.2f} >= ${STOP}', flush=True)
                return
            err = f'{r.status_code} {r.text[:150]}'
        except Exception as e: err = str(e)
        time.sleep(2 ** (k + 1))
    with lock: open(f'{OUT}/errors.jsonl', 'a').write(json.dumps(dict(key=list(job[0]), err=err)) + '\n')

with cf.ThreadPoolExecutor(128) as ex: list(ex.map(call, jobs))
print(f'FINISHED spent ${spent[0]:.2f} calls {n_done[0]} halted={halt.is_set()}', flush=True)
