"""Confirmatory study C1 (AsPredicted #320110): new simulated respondents, prompt template B, random condition assignment.
Usage: python3 run_c1.py <data_dir> <out_dir> [n_respondents] [stop_usd]
Respondents: Twin-2K-500 participants not in the three mega-study files, drawn with seed 2026.
Architectures: demo, summary, theory (demographics plus phenomena named; needed for P6). One draw each, temperature 0.7, reasoning effort low."""
import sys, os, re, json, time, random, threading, concurrent.futures as cf
import pandas as pd, requests
D, OUT = sys.argv[1], sys.argv[2]
NR = int(sys.argv[3]) if len(sys.argv) > 3 else 600
STOP = float(sys.argv[4]) if len(sys.argv) > 4 else 120.0
MODELS = ['anthropic/claude-haiku-5.5', 'openai/gpt-5.6-luna', 'google/gemini-3.7-flash', 'x-ai/grok-4.3', 'meta-llama/llama-4-maverick']
os.makedirs(OUT, exist_ok=True); RAW = f'{OUT}/raw.jsonl'

def blocks(text):
    parts = re.split(r'\nQ(\d+):\s*', '\n' + text); return {int(parts[i]): parts[i + 1] for i in range(1, len(parts) - 1, 2)}
def opts(b):
    m = re.search(r'Options:\n((?:\s+\d+ - .*\n?)+)', b); return [t.strip() for _, t in re.findall(r'\s+(\d+) - (.*)', m.group(1))] if m else []
DECOY = {'Hal-B', 'L22', '5C-S'}
def classify(study, b):
    ot = opts(b)
    if study == 'default_eric':
        if 'electric' in b: return 'default_green', ('optout' if ot[0].startswith('Stay with GreenGrid') else 'optin')
        if 'organ donor' in b: return 'default_organ', ('optout' if 'is considered to be an organ donor' in b else 'optin')
    if study == 'context_effects':
        for k, w in [('attr_TV', 'Scenario: Television'), ('attr_Printer', 'Scenario: Printer'), ('attr_Cell', 'Scenario: Cellphone')]:
            if w in b:
                if len(ot) == 2: return k, 'binary'
                if set(ot) & DECOY: return k, 'attraction'
    return None, None
STIM = {}   # (item, cond) -> list of (text, options or None)
for st in ['default_eric', 'context_effects']:
    d = pd.read_parquet(f'{D}/{st}-00000-of-00001.parquet')
    for _, r in d.iterrows():
        for k, b in blocks(r['survey_text']).items():
            item, cond = classify(st, b)
            if item and (item, cond) not in STIM: STIM[(item, cond)] = [(b.split('\nQuestion Type:')[0].strip(), opts(b))]
SC = 'A snack foods company has developed a new line of snacks. Initial testing showed that, due to the taste and texture profile of the snacks, the snacks are better suited to the preferences of their female customers. The company is developing a marketing plan to promote the snacks. '
FAIR = ['1: Not at all fair', '2', '3', '4', '5', '6', '7', '8', '9: Very fair']
STIM[('fair', 'broad')] = [(SC + 'Even though they believe the snacks are best suited to their female customers, they will advertise the snacks broadly to the general public. How fair is this advertising plan?', FAIR)]
STIM[('fair', 'targeted')] = [(SC + 'Because they believe the snacks are best suited to their female customers, they will advertise the snacks to women directly. How fair is this advertising plan?', FAIR)]
LIK = ['I strongly favor program A', 'I favor program A', 'I slightly favor program A', 'I slightly favor program B', 'I favor program B', 'I strongly favor program B']
INTRO = 'Imagine that the U.S. is preparing for the outbreak of an unusual disease, which is expected to kill 600 people. Two alternative programs to combat the disease have been proposed. Assume that the exact scientific estimate of the consequences of the programs are as follows: '
STIM[('frame', 'gain')] = [(INTRO + 'If Program A is adopted, 200 people will be saved. If Program B is adopted, there is 1/3 probability that 600 people will be saved, and 2/3 probability that no people will be saved. Which of the two programs would you favor?', LIK)]
STIM[('frame', 'loss')] = [(INTRO + 'If Program A is adopted, 400 people will die. If Program B is adopted, there is 1/3 probability that nobody will die, and 2/3 probability that 600 people will die. Which of the two programs would you favor?', LIK)]
for item, q1, q2, hi, lo in [('anch_africa', 'Do you think there are more or fewer than {} African countries in the United Nations?', 'How many African countries do you think are in the United Nations?', 65, 12),
                             ('anch_redwood', 'Is the tallest redwood tree in the world more or less than {} feet tall?', 'How tall do you think the tallest redwood tree in the world is? Enter a number of feet.', 1000, 85)]:
    w = ['more', 'fewer'] if 'African' in q1 else ['more', 'less']
    STIM[(item, 'high')] = [(q1.format(hi), w), (q2, None)]; STIM[(item, 'low')] = [(q1.format(lo), w), (q2, None)]
ITEMS = sorted({i for i, _ in STIM})
assert len(ITEMS) == 9 and len(STIM) == 18, (ITEMS, len(STIM))

def booklet(pid):
    rng = random.Random(f'2026-{pid}'); its = ITEMS[:]; rng.shuffle(its); conds, qs = {}, []
    for it in its:
        c = rng.choice(sorted(c for i, c in STIM if i == it)); conds[it] = c
        for qi, (t, o) in enumerate(STIM[(it, c)]): qs.append(dict(item=it, qi=qi, text=t, opts=o))
    return conds, qs
def render(qs):
    lines = []
    for n, q in enumerate(qs, 1):
        lines.append(f'Q{n}. {q["text"]}' + ('\n' + '\n'.join(f'  ({i}) {o}' for i, o in enumerate(q['opts'], 1)) if q['opts'] else '\n  (enter a number)'))
    return ('Please complete the following short survey as the person described. For every question reply with the number of the option you would choose, '
            'or with the number you would enter for numeric questions. Reply with only a JSON object whose keys are the question labels, for example {"Q1": 2, "Q2": 35}.\n\n' + '\n\n'.join(lines))

demo = pd.read_csv(f'{D}/wave1_3_response_label.csv', low_memory=False, usecols=['pid'] + [f'QID{i}' for i in range(11, 25)])
LAB = ['Region', 'Sex assigned at birth', 'Age group', 'Education', 'Race or origin', 'US citizen', 'Marital status', 'Religion', 'Religious service attendance', 'Party identification', 'Family income', 'Political views', 'Household size', 'Employment']
demo['PID'] = 'pid_' + demo['pid'].astype(str); demo = demo.set_index('PID')
summ = pd.read_parquet(f'{D}/persona_summary.parquet').set_index('PID')['persona_summary']
HEAD = 'Role-play the real person described below and stay in character. Respond the way this individual realistically would, without commenting as an AI.\n\nPerson:\n'
NOTE = '\n\nResearch note: the survey examines default options, the framing of gains versus losses, numerical anchoring, the attraction effect of adding an inferior option, and fairness judgments. Respond as the real person would.'
def system(pid, arch):
    if arch == 'summary': return HEAD + summ[pid]
    r = demo.loc[pid]; s = HEAD + '\n'.join(f'- {l}: {r[f"QID{11+i}"]}' for i, l in enumerate(LAB))
    return s + (NOTE if arch == 'theory' else '')

mega = set()
for st in ['default_eric', 'context_effects', 'targeting_fairness']: mega |= set(pd.read_parquet(f'{D}/{st}-00000-of-00001.parquet').PID)
pool = sorted((set(summ.index) & set(demo.index)) - mega); print('unused respondents', len(pool), flush=True)
pids = random.Random(2026).sample(pool, min(NR, len(pool)))
done = set()
if os.path.exists(RAW):
    for l in open(RAW):
        try: x = json.loads(l); done.add((x['pid'], x['model'], x['arch']))
        except Exception: pass
jobs = [(p, m, a) for p in pids for m in MODELS for a in ('demo', 'summary', 'theory') if (p, m, a) not in done]
random.Random(1).shuffle(jobs); print('jobs', len(jobs), flush=True)
lock = threading.Lock(); spent = [0.0]; halt = threading.Event(); cnt = [0]
def call(job):
    if halt.is_set(): return
    pid, m, a = job; conds, qs = booklet(pid)
    body = dict(model=m, temperature=0.7, max_tokens=2000, usage={'include': True}, reasoning={'effort': 'low'},
                messages=[{'role': 'system', 'content': system(pid, a)}, {'role': 'user', 'content': render(qs)}])
    err = None
    for k in range(5):
        try:
            r = requests.post('https://openrouter.ai/api/v1/chat/completions', json=body, timeout=240)
            if r.status_code == 200:
                x = r.json(); u = x.get('usage', {})
                rec = dict(pid=pid, model=m, arch=a, content=x['choices'][0]['message'].get('content'), cost=u.get('cost') or 0, conds=conds, qs=qs)
                with lock:
                    open(RAW, 'a').write(json.dumps(rec) + '\n'); spent[0] += rec['cost']; cnt[0] += 1
                    if cnt[0] % 500 == 0: print(f'done {cnt[0]} spent ${spent[0]:.2f}', flush=True)
                    if spent[0] >= STOP: halt.set(); print('HALT', spent[0], flush=True)
                return
            err = f'{r.status_code} {r.text[:150]}'
        except Exception as e: err = str(e)
        time.sleep(2 ** (k + 1))
    with lock: open(f'{OUT}/errors.jsonl', 'a').write(json.dumps(dict(key=list(job), err=err)) + '\n')
if __name__ == '__main__' and os.environ.get('C1_DRY') != '1':
    with cf.ThreadPoolExecutor(64) as ex: list(ex.map(call, jobs))
    print(f'FINISHED spent ${spent[0]:.2f} calls {cnt[0]}', flush=True)
