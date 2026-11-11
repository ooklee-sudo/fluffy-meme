"""Quantum-cognition order-effect / QQ-equality experiment with LLMs as participants.
Each trial: one chat, two sequential yes/no questions (Q = quality, B = brand), order randomized by cell.
Cells: disclosure {none, brand} x order {QB, BQ}. Every item runs in all four cells for each model."""
import sys, re, json, numpy as np, pandas as pd
sys.path.insert(0, 'src'); import orc
from leaks import RX_ANY
D = '/home/user/data'
MODELS = {'qwen': 'qwen/qwen3.7-flash', 'haiku': 'anthropic/claude-haiku-5.5', 'llama': 'meta-llama/llama-4-scout'}
BRANDS = [('Claude', 'Anthropic'), ('Gemini', 'Google'), ('ChatGPT', 'OpenAI'), ('Grok', 'xAI'), ('Orion', 'Nimbus Labs')]
M = pd.read_pickle(f'{D}/study1_matched.pkl')
M = M[(M.leak == 0)].dropna(subset=['deepseek_diff', 'qwen_diff'])
M['q'] = (M.deepseek_diff + M.qwen_diff) / 2
items = M[M.q.abs() <= 2].drop_duplicates('cid')
conv = pd.read_pickle(f'{D}/140k.pkl').set_index('id')
rng = np.random.default_rng(42)
mask = lambda t: RX_ANY.sub('[NAME]', t or '')
recs = []
for _, r in items.iterrows():
    c = conv.loc[r.cid]
    foc = mask((c[f'{r.side}_turns'] or [''])[0])[:1500]; opp = mask((c[f'{"b" if r.side == "a" else "a"}_turns'] or [''])[0])[:1500]
    if len(foc) < 40 or len(opp) < 40: continue
    recs.append(dict(cid=r.cid, user=mask((c.user_turns or [''])[0])[:800], foc=foc, opp=opp,
                     brand=BRANDS[int(rng.integers(len(BRANDS)))], focal_first=bool(rng.integers(2))))
recs = recs[:int(sys.argv[1]) if len(sys.argv) > 1 else 850]
SYS = 'You are evaluating two AI assistant responses. Answer each question with a single word: Yes or No.'
def build(it, disc):
    f = (f"I'm {it['brand'][0]}, an AI assistant made by {it['brand'][1]}. " + it['foc']) if disc else it['foc']
    x, y = ('1', '2') if it['focal_first'] else ('2', '1')
    r1, r2 = (f, it['opp']) if it['focal_first'] else (it['opp'], f)
    ctx = f"[USER PROMPT]\n{it['user']}\n\n[RESPONSE 1]\n{r1}\n\n[RESPONSE 2]\n{r2}"
    Q = f'Is Response {x} better than Response {y}? Answer Yes or No.'
    B = (f"Is {it['brand'][1]} a trustworthy AI company? Answer Yes or No." if disc else
         f'Do you think Response {x} was written by a model from a leading AI company (OpenAI, Google, or Anthropic)? Answer Yes or No.')
    return ctx, Q, B
yn = lambda t: None if t is None else (1 if re.match(r'\W*yes', t, re.I) else 0 if re.match(r'\W*no', t, re.I) else None)
def trial(args):
    k, it, disc, order, mname = args
    ctx, Q, B = build(it, disc)
    first, second = (Q, B) if order == 'QB' else (B, Q)
    kw = dict(max_tokens=5, temperature=0.7, reasoning={'enabled': False})
    m1 = [{'role': 'system', 'content': SYS}, {'role': 'user', 'content': ctx + '\n\n' + first}]
    a1 = orc.chat(MODELS[mname], m1, **kw)
    if yn(a1) is None: return None
    a2 = orc.chat(MODELS[mname], m1 + [{'role': 'assistant', 'content': a1.strip()}, {'role': 'user', 'content': second}], **kw)
    if yn(a2) is None: return None
    q, b = (yn(a1), yn(a2)) if order == 'QB' else (yn(a2), yn(a1))
    return dict(item=k, model=mname, disc=disc, order=order, Q=q, B=b, brand=it['brand'][0])
jobs = [(k, it, disc, order, mn) for mn in MODELS for k, it in enumerate(recs) for disc in (0, 1) for order in ('QB', 'BQ')]
before = orc.spent()
out = pd.DataFrame([r for r in orc.pmap(trial, jobs, 48) if r])
out.to_pickle(f'{D}/qq_llm.pkl')
print('trials', len(jobs), 'valid', len(out), 'cost this run $%.3f' % (orc.spent() - before))
