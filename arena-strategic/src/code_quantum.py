"""Preregistered quantum-cognition signatures in LLM code review (prereg/code_quantum_prereg.md)."""
import sys, re, json, pandas as pd
sys.path.insert(0, 'src'); import orc
from qq_counterbalanced import MAPS, tag, sysline, parse
D = '/home/user/data'
MODELS = {'qwen': 'qwen/qwen3.7-flash', 'haiku': 'anthropic/claude-haiku-5.5', 'llama': 'meta-llama/llama-4-scout', 'deepseek': 'deepseek/deepseek-v3.2'}
ITEMS = json.load(open('/home/user/fluffy-meme/arena-strategic/prereg/code_items.json'))
SYS = 'You are an experienced Python code reviewer.'
code = lambda it: f"Here is a pull request with the following code:\n```python\n{it['code']}\n```"
CTX = {'P': 'The CI test suite was run on this code and all tests passed.', 'F': 'The CI test suite was run on this code and one test failed.',
       'U': 'The CI test suite has not finished running yet, so you do not know whether the tests will pass.'}
APPROVE, BUG = 'Would you approve merging this pull request?', 'Does this code contain a bug?'
O1, O2 = 'This code contains a bug.', 'This code contains a bug in a comparison, arithmetic, or boolean operator.'
def kw(rep): return dict(max_tokens=5, temperature=1.0, reasoning={'enabled': False}, seed=rep)
def e1(a):
    i, cond, mp, rep, mn = a; it = ITEMS[i]
    t = orc.chat(MODELS[mn], [{'role': 'system', 'content': SYS + ' ' + sysline(mp)}, {'role': 'user', 'content': f'{code(it)}\n\n{CTX[cond]} {APPROVE} {tag(mp)}'}], **kw(rep))
    v = parse(t, mp); return None if v is None else dict(exp='E1', item=i, label=it['label'], cond=cond, map=mp, rep=rep, model=mn, approve=v)
def e2(a):
    i, cond, mp, rep, mn = a; it = ITEMS[i]; s = {'role': 'system', 'content': SYS + ' ' + sysline(mp)}
    if cond == 'direct':
        v = parse(orc.chat(MODELS[mn], [s, {'role': 'user', 'content': f'{code(it)}\n\n{APPROVE} {tag(mp)}'}], **kw(rep)), mp)
        return None if v is None else dict(exp='E2', item=i, label=it['label'], cond=cond, map=mp, rep=rep, model=mn, approve=v, bug=None)
    m = [s, {'role': 'user', 'content': f'{code(it)}\n\n{BUG} {tag(mp)}'}]; a1 = orc.chat(MODELS[mn], m, **kw(rep)); b = parse(a1, mp)
    if b is None: return None
    v = parse(orc.chat(MODELS[mn], m + [{'role': 'assistant', 'content': a1.strip()}, {'role': 'user', 'content': f'{APPROVE} {tag(mp)}'}], **kw(rep)), mp)
    return None if v is None else dict(exp='E2', item=i, label=it['label'], cond=cond, map=mp, rep=rep, model=mn, approve=v, bug=b)
def e3(a):
    i, order, rep, mn = a; it = ITEMS[i]; A, B = (O1, O2) if order == 'single_first' else (O2, O1)
    t = orc.chat(MODELS[mn], [{'role': 'system', 'content': SYS + ' Answer with a single letter, A or B.'}, {'role': 'user', 'content': f'{code(it)}\n\nWhich statement is more probable?\n(A) {A}\n(B) {B}\nAnswer A or B.'}], **kw(rep))
    m = re.match(r'\W*([AB])\b', (t or '').strip(), re.I)
    if not m: return None
    chose_conj = (m.group(1).upper() == 'B') if order == 'single_first' else (m.group(1).upper() == 'A')
    return dict(exp='E3', item=i, label=it['label'], order=order, rep=rep, model=mn, conj=int(chose_conj))
if __name__ == '__main__':
    n = len(ITEMS) if len(sys.argv) < 2 else int(sys.argv[1]); R = range(2)
    j1 = [(i, c, mp, r, mn) for i in range(n) for c in CTX for mp in MAPS for r in R for mn in MODELS]
    j2 = [(i, c, mp, r, mn) for i in range(n) for c in ('direct', 'indirect') for mp in MAPS for r in R for mn in MODELS]
    j3 = [(i, o, r, mn) for i in range(n) for o in ('single_first', 'conj_first') for r in R for mn in MODELS]
    before = orc.spent()
    out = pd.DataFrame([x for f, j in ((e1, j1), (e2, j2), (e3, j3)) for x in orc.pmap(f, j, 64) if x])
    out.to_pickle(f'{D}/code_quantum{"" if n == len(ITEMS) else "_pilot"}.pkl')
    print('jobs', len(j1) + len(j2) + len(j3), 'valid', len(out), '| cost $%.3f' % (orc.spent() - before)); print(out.groupby(['exp', 'model']).size().unstack())
