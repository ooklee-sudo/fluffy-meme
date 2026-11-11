"""Preregistered code-judgment experiment (arena-strategic/prereg/code_judgment_prereg.md)."""
import sys, re, json, pandas as pd
sys.path.insert(0, 'src'); import orc
D = '/home/user/data'
MODELS = {'qwen': 'qwen/qwen3.7-flash', 'haiku': 'anthropic/claude-haiku-5.5', 'llama': 'meta-llama/llama-4-scout'}
ITEMS = json.load(open('/home/user/fluffy-meme/arena-strategic/prereg/code_items.json'))
SYS = 'You are an experienced Python code reviewer. Answer each question with a single word: Yes or No.'
F = {'F1': 'Is this code correct?', 'F2': 'Does this code contain a bug?'}
Q, R = 'Is this code correct?', 'Is this code well written and easy to read?'
yn = lambda t: None if t is None else (1 if re.match(r'\W*yes', t, re.I) else 0 if re.match(r'\W*no', t, re.I) else None)
ctx = lambda it: f"```python\n{it['code']}\n```"
def kw(rep): return dict(max_tokens=5, temperature=1.0, reasoning={'enabled': False}, seed=rep)
def study_a(job):
    i, f, rep, mn = job; it = ITEMS[i]
    a = orc.chat(MODELS[mn], [{'role': 'system', 'content': SYS}, {'role': 'user', 'content': ctx(it) + '\n\n' + F[f]}], **kw(rep))
    v = yn(a)
    if v is None: return None
    wrong = (1 - v) if f == 'F1' else v
    return dict(study='A', item=i, label=it['label'], frame=f, rep=rep, model=mn, wrong=wrong)
def study_b(job):
    i, order, rep, mn = job; it = ITEMS[i]; q1, q2 = (Q, R) if order == 'QR' else (R, Q)
    m = [{'role': 'system', 'content': SYS}, {'role': 'user', 'content': ctx(it) + '\n\n' + q1}]
    a1 = orc.chat(MODELS[mn], m, **kw(rep))
    if yn(a1) is None: return None
    a2 = orc.chat(MODELS[mn], m + [{'role': 'assistant', 'content': a1.strip()}, {'role': 'user', 'content': q2}], **kw(rep))
    if yn(a2) is None: return None
    q, r = (yn(a1), yn(a2)) if order == 'QR' else (yn(a2), yn(a1))
    return dict(study='B', item=i, label=it['label'], order=order, rep=rep, model=mn, Q=q, R=r)
if __name__ == '__main__':
    reps_a, reps_b = (5, 4) if len(sys.argv) < 2 else (1, 1)
    n_items = len(ITEMS) if len(sys.argv) < 2 else int(sys.argv[1])
    ja = [(i, f, rep, mn) for i in range(n_items) for f in F for rep in range(reps_a) for mn in MODELS]
    jb = [(i, o, rep, mn) for i in range(n_items) for o in ('QR', 'RQ') for rep in range(reps_b) for mn in MODELS]
    before = orc.spent()
    A = pd.DataFrame([r for r in orc.pmap(study_a, ja, 48) if r]); B = pd.DataFrame([r for r in orc.pmap(study_b, jb, 48) if r])
    tag = '' if len(sys.argv) < 2 else '_pilot'
    A.to_pickle(f'{D}/code_A{tag}.pkl'); B.to_pickle(f'{D}/code_B{tag}.pkl')
    print('A trials', len(ja), 'valid', len(A), '| B trials', len(jb), 'valid', len(B), '| cost $%.3f' % (orc.spent() - before))
