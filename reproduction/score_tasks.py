"""Score O*NET task statements with an LLM on two 0-2 rubrics (visual content creation; text/language work).
Usage: python score_tasks.py DATA_DIR OUT_JSONL [limit]
Rubric text follows Appendix A of the manuscript (narrow visual rubric); the text rubric is our own analogue
for the language-model exposure control (the manuscript does not specify it)."""
import sys, json, re, time, os, threading, concurrent.futures as cf
import pandas as pd, requests

DATA, OUT = sys.argv[1], sys.argv[2]
LIMIT = int(sys.argv[3]) if len(sys.argv) > 3 else None
MODEL = os.environ.get('SCORE_MODEL', 'anthropic/claude-haiku-5.5')
BATCH, WORKERS = 20, 12

SYSTEM = """You code O*NET task statements on two rubrics. Score each task independently.

VISUAL (visual content creation): Score 2 if producing or editing visual content is central to the task; 1 if visual content is a partial or supporting product; 0 otherwise. Reading, inspecting, writing, and audio production do not count. Technical drawings count only when the task is about producing them as drawings or graphics.

TEXT (language work): Score 2 if reading, writing, summarizing, translating, or otherwise producing or editing text is central to the task; 1 if text is a partial or supporting product; 0 otherwise. Spoken conversation, numeric calculation, and purely physical work do not count.

Return ONLY a JSON array, one object per task, in the form {"id": <id>, "visual": 0|1|2, "text": 0|1|2}. No commentary."""

def load_tasks():
    if os.environ.get('TASK_TEXTS'):          # alternative input: JSON list of statements (e.g. NOC main duties)
        return sorted(set(json.load(open(os.environ['TASK_TEXTS']))))
    cw = pd.read_excel(os.path.join(DATA, 'esco_onet.xlsx'), header=3)
    cw.columns = ['esco', 'esco_title', 'soc', 'soc_title']
    cw['isco3'] = cw.esco.astype(str).str.extract(r'^(\d{3})')[0]
    oja = pd.read_pickle(os.path.join(DATA, 'oja.pkl'))
    o = oja[(oja.indic_em == 'OJA') & (oja.geo.str.len() == 2) & (oja.isco08.str.len() == 5) & oja.isco08.str.startswith('OC')].copy()
    o['occ'] = o.isco08.str[2:]
    p = o.pivot_table(index=['geo', 'occ'], columns='time', values='v')
    occs = set(p[p['2022'] >= 1.0].index.get_level_values(1))
    soc = set(cw[cw.isco3.isin(occs)].soc)
    ts = pd.read_csv(os.path.join(DATA, 'onet/db_29_1_text/Task Statements.txt'), sep='\t')
    ts = ts[ts['O*NET-SOC Code'].isin(soc)]
    texts = sorted(ts.Task.unique())
    return texts

def call(batch):
    payload = {'model': MODEL, 'temperature': 0, 'max_tokens': 2000,
               'messages': [{'role': 'system', 'content': SYSTEM},
                            {'role': 'user', 'content': json.dumps([{'id': i, 'task': t} for i, t in batch])}]}
    for attempt in range(6):
        try:
            r = requests.post('https://openrouter.ai/api/v1/chat/completions', json=payload,
                              headers={'Authorization': 'Bearer dummy'}, timeout=120)
            if r.status_code != 200:
                time.sleep(2 ** attempt); continue
            txt = r.json()['choices'][0]['message']['content']
            m = re.search(r'\[.*\]', txt, re.S)
            arr = json.loads(m.group(0))
            got = {int(a['id']): a for a in arr}
            if all(i in got and got[i]['visual'] in (0, 1, 2) and got[i]['text'] in (0, 1, 2) for i, _ in batch):
                return [(i, t, got[i]['visual'], got[i]['text']) for i, t in batch]
        except Exception:
            time.sleep(2 ** attempt)
    return None

def main():
    texts = load_tasks()
    if LIMIT: texts = texts[:LIMIT]
    done = {}
    if os.path.exists(OUT):
        for line in open(OUT):
            d = json.loads(line); done[d['task']] = d
    todo = [(i, t) for i, t in enumerate(texts) if t not in done]
    batches = [todo[k:k + BATCH] for k in range(0, len(todo), BATCH)]
    print(f'{len(texts)} tasks, {len(done)} done, {len(batches)} batches', flush=True)
    lock = threading.Lock(); n = 0; failed = []
    with open(OUT, 'a') as f, cf.ThreadPoolExecutor(WORKERS) as ex:
        for res in ex.map(call, batches):
            if res is None: failed.append(1); continue
            with lock:
                for i, t, v, x in res:
                    f.write(json.dumps({'task': t, 'visual': v, 'text': x, 'model': MODEL}) + '\n')
                f.flush(); n += 1
                if n % 50 == 0: print(n, 'batches', flush=True)
    print('finished; failed batches:', len(failed), flush=True)

if __name__ == '__main__': main()
