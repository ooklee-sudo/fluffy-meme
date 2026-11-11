"""Label-counterbalanced replication of Studies 1 and 2 (prereg/qq_counterbalanced_prereg.md)."""
import sys, re, json, numpy as np, pandas as pd
sys.path.insert(0, 'src'); import orc
from leaks import RX_ANY
D = '/home/user/data'
MODELS = {'qwen': 'qwen/qwen3.7-flash', 'haiku': 'anthropic/claude-haiku-5.5', 'llama': 'meta-llama/llama-4-scout'}
MAPS = {'M1': ('Yes', 'No'), 'M2': ('No', 'Yes')}   # meaning of A, meaning of B
def tag(m): a, b = MAPS[m]; return f'(Answer A for {a}, B for {b}.)'
def sysline(m): a, b = MAPS[m]; return f'Answer each question with a single letter. In this conversation, A means {a} and B means {b}.'
def parse(t, m):
    if t is None: return None
    s = re.match(r'\W*([AB])\b', t.strip(), re.I)
    if not s: return None
    a, b = MAPS[m]; meaning = a if s.group(1).upper() == 'A' else b
    return 1 if meaning == 'Yes' else 0
# ---------- Study 1R items: rebuild exactly as in qq_llm.py ----------
BRANDS = [('Claude', 'Anthropic'), ('Gemini', 'Google'), ('ChatGPT', 'OpenAI'), ('Grok', 'xAI'), ('Orion', 'Nimbus Labs')]
def study1_items(n=400):
    M = pd.read_pickle(f'{D}/study1_matched.pkl'); M = M[(M.leak == 0)].dropna(subset=['deepseek_diff', 'qwen_diff'])
    M['q'] = (M.deepseek_diff + M.qwen_diff) / 2; items = M[M.q.abs() <= 2].drop_duplicates('cid')
    conv = pd.read_pickle(f'{D}/140k.pkl').set_index('id'); rng = np.random.default_rng(42); mask = lambda t: RX_ANY.sub('[NAME]', t or '')
    recs = []
    for _, r in items.iterrows():
        c = conv.loc[r.cid]
        foc = mask((c[f'{r.side}_turns'] or [''])[0])[:1500]; opp = mask((c[f'{"b" if r.side == "a" else "a"}_turns'] or [''])[0])[:1500]
        if len(foc) < 40 or len(opp) < 40: continue
        recs.append(dict(cid=r.cid, user=mask((c.user_turns or [''])[0])[:800], foc=foc, opp=opp, brand=BRANDS[int(rng.integers(len(BRANDS)))], focal_first=bool(rng.integers(2))))
    return recs[:n]
def s1_trial(args):
    k, it, disc, order, mp, mn = args
    f = (f"I'm {it['brand'][0]}, an AI assistant made by {it['brand'][1]}. " + it['foc']) if disc else it['foc']
    x, y = ('1', '2') if it['focal_first'] else ('2', '1')
    r1, r2 = (f, it['opp']) if it['focal_first'] else (it['opp'], f)
    ctx = f"[USER PROMPT]\n{it['user']}\n\n[RESPONSE 1]\n{r1}\n\n[RESPONSE 2]\n{r2}"
    Q = f'Is Response {x} better than Response {y}? {tag(mp)}'
    B = (f"Is {it['brand'][1]} a trustworthy AI company? {tag(mp)}" if disc else f'Do you think Response {x} was written by a model from a leading AI company (OpenAI, Google, or Anthropic)? {tag(mp)}')
    first, second = (Q, B) if order == 'QB' else (B, Q)
    kw = dict(max_tokens=5, temperature=0.7, reasoning={'enabled': False})
    m1 = [{'role': 'system', 'content': 'You are evaluating two AI assistant responses. ' + sysline(mp)}, {'role': 'user', 'content': ctx + '\n\n' + first}]
    a1 = orc.chat(MODELS[mn], m1, **kw); v1 = parse(a1, mp)
    if v1 is None: return None
    a2 = orc.chat(MODELS[mn], m1 + [{'role': 'assistant', 'content': a1.strip()}, {'role': 'user', 'content': second}], **kw); v2 = parse(a2, mp)
    if v2 is None: return None
    q, b = (v1, v2) if order == 'QB' else (v2, v1)
    return dict(study='1R', item=k, model=mn, disc=disc, order=order, map=mp, Q=q, B=b, first=v1, second=v2)
# ---------- Study 2R ----------
from qq_human_replication import ITEMS as S2ITEMS
rng2 = np.random.default_rng(2627)
def persona():
    age = int(rng2.integers(18, 86)); g = rng2.choice(['man', 'woman'])
    race = rng2.choice(['White', 'Black', 'Hispanic', 'Asian American'], p=[0.72, 0.12, 0.11, 0.05])
    party = rng2.choice(['Republican', 'Democrat', 'independent'], p=[0.32, 0.34, 0.34])
    edu = rng2.choice(['did not finish high school', 'a high school diploma', 'some college', 'a four-year college degree', 'a graduate degree'], p=[0.12, 0.30, 0.28, 0.19, 0.11])
    region = rng2.choice(['the Northeast', 'the Midwest', 'the South', 'the West'], p=[0.18, 0.22, 0.37, 0.23])
    return f'a {age}-year-old {race} {g} from {region} with {edu}, who identifies as a {party}'
def s2_trial(args):
    item, order, k, p, mp, mn = args
    qa, qb, era = S2ITEMS[item]; q1, q2 = (qa, qb) if order == 'AB' else (qb, qa)
    sysm = f'You are taking part in a US national telephone opinion poll in the {era}. Answer as yourself: {p}. Answer based on your honest opinion. ' + sysline(mp)
    kw = dict(max_tokens=5, temperature=1.0, reasoning={'enabled': False})
    m = [{'role': 'system', 'content': sysm}, {'role': 'user', 'content': f'{q1} {tag(mp)}'}]
    a1 = orc.chat(MODELS[mn], m, **kw); v1 = parse(a1, mp)
    if v1 is None: return None
    a2 = orc.chat(MODELS[mn], m + [{'role': 'assistant', 'content': a1.strip()}, {'role': 'user', 'content': f'{q2} {tag(mp)}'}], **kw); v2 = parse(a2, mp)
    if v2 is None: return None
    return dict(study='2R', item=item, model=mn, order=order, map=mp, k=k, first=v1, second=v2)
if __name__ == '__main__':
    n1, n2 = (400, 250) if len(sys.argv) < 2 else (int(sys.argv[1]), int(sys.argv[2]))
    recs = study1_items(n1)
    j1 = [(k, it, d, o, mp, mn) for k, it in enumerate(recs) for d in (0, 1) for o in ('QB', 'BQ') for mp in MAPS for mn in MODELS]
    j2 = [(it, o, k, persona(), mp, mn) for it in S2ITEMS for o in ('AB', 'BA') for mp in MAPS for k in range(n2) for mn in MODELS]
    before = orc.spent()
    R1 = pd.DataFrame([r for r in orc.pmap(s1_trial, j1, 64) if r]); R2 = pd.DataFrame([r for r in orc.pmap(s2_trial, j2, 64) if r])
    tagp = '' if len(sys.argv) < 2 else '_pilot'
    R1.to_pickle(f'{D}/cb_study1{tagp}.pkl'); R2.to_pickle(f'{D}/cb_study2{tagp}.pkl')
    print('1R trials', len(j1), 'valid', len(R1), '| 2R trials', len(j2), 'valid', len(R2), '| cost $%.3f' % (orc.spent() - before))
