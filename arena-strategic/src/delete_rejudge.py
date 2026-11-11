"""Counterfactual editing: real leaked replies, judged (a) as-is with names visible vs (b) with disclosure sentences deleted."""
import sys, re, json, numpy as np, pandas as pd
sys.path.insert(0, 'src'); import orc
from leaks import RX, RX_ANY
D = '/home/user/data'
M = pd.read_pickle(f'{D}/study1_matched.pkl'); L = M[M.leak == 1]
conv = pd.read_pickle(f'{D}/140k.pkl').set_index('id')
SPLIT = re.compile(r'(?<=[.!?])\s+|\n+')
def delete(t):
    parts = [p for p in SPLIT.split(t or '') if p and not RX.search(p)]
    return ' '.join(parts)
PROMPT = open('src/judge.py').read().split('PROMPT = """')[1].split('"""')[0].replace(' Names of AI models or companies have been replaced with [NAME]; ignore this.', '')
JUDGES = {'deepseek': 'deepseek/deepseek-v3.2', 'qwen': 'qwen/qwen3-235b-a22b-2507'}
rng = np.random.default_rng(7)
jobs = []
for i, r in L.iterrows():
    c = conv.loc[r.cid]; foc = c[f'{r.side}_turns']; opp = c[f'{"b" if r.side == "a" else "a"}_turns']
    flip = bool(rng.integers(2)); u = ('\n---\n'.join(c.user_turns))[:1500]
    for cond, f in (('original', foc), ('deleted', [delete(t) for t in foc])):
        ftxt = '\n\n---\n\n'.join(f)[:4000]; otxt = RX_ANY.sub('[NAME]', '\n\n---\n\n'.join(opp))[:4000]   # opponent masked as before
        a, b = (otxt, ftxt) if flip else (ftxt, otxt)
        jobs.append((i, cond, flip, PROMPT.format(u=u, a=a, b=b), len('\n'.join(foc)) - len('\n'.join(f))))
def run(job):
    i, cond, flip, msg, removed = job; out = {'row': i, 'cond': cond, 'removed_chars': removed}
    for name, model in JUDGES.items():
        t = orc.chat(model, [{'role': 'user', 'content': msg}], max_tokens=300, reasoning={'enabled': False})
        try:
            j = json.loads(re.search(r'\{.*?\}', t or '', re.S).group(0)); sa, sb = float(j['score_a']), float(j['score_b'])
            out[f'{name}_diff'] = (sb - sa) if flip else (sa - sb)
            out[f'{name}_win'] = ({'A': 0, 'B': 1} if flip else {'A': 1, 'B': 0}).get(j['winner'], 0.5)
        except Exception: pass
    return out
before = orc.spent()
R = pd.DataFrame(orc.pmap(run, jobs, 48)); R.to_pickle(f'{D}/delete_rejudge.pkl')
print('items', L.shape[0], 'cost $%.3f' % (orc.spent() - before))
W = R.pivot_table(index='row', columns='cond', values=['deepseek_diff', 'qwen_diff', 'deepseek_win', 'qwen_win']).dropna()
for k in ['deepseek', 'qwen']:
    for v in ['diff', 'win']:
        x = W[(f'{k}_{v}', 'original')] - W[(f'{k}_{v}', 'deleted')]
        print(f'{k:8s} {v:4s}: original={W[(f"{k}_{v}", "original")].mean():+.3f} deleted={W[(f"{k}_{v}", "deleted")].mean():+.3f}  effect of disclosure sentence={x.mean():+.3f} (se {x.std() / np.sqrt(len(x)):.3f}) n={len(x)}')
