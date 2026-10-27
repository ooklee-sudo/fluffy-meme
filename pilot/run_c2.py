"""Field test C2: twin-predicted click propensity for Upworthy headline variants.
Usage: python3 run_c2.py <data_dir> <upworthy_csv> <out_dir> <n_tests> <seed> [personas_per_test] [stop_usd]
Test selection: >= 2 arms (at most 6), all headlines distinct, every arm >= 1,000 impressions, test created outside 2013-06-25..2014-01-10
(the archive's documented randomization-problem window). Personas: demographics only, drawn at random from Twin-2K-500 (seeded)."""
import sys, os, json, time, random, threading, concurrent.futures as cf
import pandas as pd, requests
HDR = {'Authorization': 'Bearer ' + os.environ['OPENROUTER_API_KEY']} if os.environ.get('OPENROUTER_API_KEY') else {}   # set OPENROUTER_API_KEY to run; added after the studies for replication
D, CSV, OUT, NT, SEED = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
K = int(sys.argv[6]) if len(sys.argv) > 6 else 5
STOP = float(sys.argv[7]) if len(sys.argv) > 7 else 40.0
ARMS = (sys.argv[8] if len(sys.argv) > 8 else 'persona,nopersona').split(',')
MODELS = ['anthropic/claude-haiku-5.5', 'openai/gpt-5.6-luna', 'google/gemini-3.7-flash', 'x-ai/grok-4.3', 'meta-llama/llama-4-maverick']
os.makedirs(OUT, exist_ok=True); RAW = f'{OUT}/raw.jsonl'

def select_tests(csv, n, seed):
    d = pd.read_csv(csv, usecols=['created_at', 'clickability_test_id', 'headline', 'excerpt', 'impressions', 'clicks'])
    d['created_at'] = pd.to_datetime(d.created_at, errors='coerce'); d = d.dropna(subset=['created_at', 'headline'])
    d = d[~((d.created_at >= '2013-06-25') & (d.created_at <= '2014-01-10'))]
    keep = []
    for tid, g in d.groupby('clickability_test_id'):
        if 2 <= len(g) <= 6 and g.headline.nunique() == len(g) and (g.impressions >= 1000).all(): keep.append(tid)
    random.Random(seed).shuffle(keep); keep = keep[:n]
    return {t: d[d.clickability_test_id == t][['headline', 'excerpt', 'impressions', 'clicks']].reset_index(drop=True) for t in keep}
tests = select_tests(CSV, NT, SEED); print('tests', len(tests), flush=True)
json.dump({t: g.to_dict('records') for t, g in tests.items()}, open(f'{OUT}/tests.json', 'w'))

demo = pd.read_csv(f'{D}/wave1_3_response_label.csv', low_memory=False, usecols=['pid'] + [f'QID{i}' for i in range(11, 25)])
LAB = ['Region', 'Sex assigned at birth', 'Age group', 'Education', 'Race or origin', 'US citizen', 'Marital status', 'Religion', 'Religious service attendance', 'Party identification', 'Family income', 'Political views', 'Household size', 'Employment']
demo['PID'] = 'pid_' + demo['pid'].astype(str); demo = demo.set_index('PID'); allp = sorted(demo.index)
HEAD = 'Role-play the real person described below and stay in character. Respond the way this individual realistically would, without commenting as an AI.\n\nPerson:\n'
NOPERSONA = 'You are a typical adult in the United States who uses social media.'
def system(pid, arm): 
    if arm == 'nopersona': return NOPERSONA
    r = demo.loc[pid]; return HEAD + '\n'.join(f'- {l}: {r[f"QID{11+i}"]}' for i, l in enumerate(LAB))
def prompt(g, rng):
    order = list(range(len(g))); rng.shuffle(order); labels = 'ABCDEF'[:len(g)]
    items = '\n'.join(f'{labels[k]}. {g.headline[i]}' + (f'\n   ({g.excerpt[i]})' if isinstance(g.excerpt[i], str) and g.excerpt[i].strip() else '') for k, i in enumerate(order))
    return order, ('You are scrolling through your social media news feed and see the following versions of the same article promoted by a media site. Each version would be shown to different readers. '
        'For each version, estimate the probability (0 to 100) that YOU would click on it if it appeared in your feed. Reply with only a JSON object mapping each letter to a number, for example {"A": 12, "B": 30}.\n\n' + items)

done = set()
if os.path.exists(RAW):
    for l in open(RAW):
        try: x = json.loads(l); done.add((x['test'], x['model'], x['k'], x.get('arm', 'persona')))
        except Exception: pass
jobs = [(t, m, k, a) for t in tests for m in MODELS for k in range(K) for a in ARMS if (t, m, k, a) not in done]
random.Random(3).shuffle(jobs); print('jobs', len(jobs), flush=True)
lock = threading.Lock(); spent = [0.0]; halt = threading.Event(); cnt = [0]
def call(job):
    if halt.is_set(): return
    t, m, k, arm = job; g = tests[t]; rng = random.Random(f'{SEED}-{t}-{k}'); pid = rng.choice(allp); order, p = prompt(g, rng)
    body = dict(model=m, temperature=0.7, max_tokens=1500, usage={'include': True}, reasoning={'effort': 'low'}, messages=[{'role': 'system', 'content': system(pid, arm)}, {'role': 'user', 'content': p}])
    err = None
    for a in range(5):
        try:
            r = requests.post('https://openrouter.ai/api/v1/chat/completions', headers=HDR, json=body, timeout=240)
            if r.status_code == 200:
                x = r.json(); u = x.get('usage', {})
                rec = dict(test=t, model=m, k=k, arm=arm, pid=pid, order=order, content=x['choices'][0]['message'].get('content'), cost=u.get('cost') or 0)
                with lock:
                    open(RAW, 'a').write(json.dumps(rec) + '\n'); spent[0] += rec['cost']; cnt[0] += 1
                    if cnt[0] % 500 == 0: print(f'done {cnt[0]} spent ${spent[0]:.2f}', flush=True)
                    if spent[0] >= STOP: halt.set(); print('HALT', spent[0], flush=True)
                return
            err = f'{r.status_code} {r.text[:150]}'
        except Exception as e: err = str(e)
        time.sleep(2 ** (a + 1))
    with lock: open(f'{OUT}/errors.jsonl', 'a').write(json.dumps(dict(key=list(job), err=err)) + '\n')
with cf.ThreadPoolExecutor(48) as ex: list(ex.map(call, jobs))
print(f'FINISHED spent ${spent[0]:.2f} calls {cnt[0]}', flush=True)
