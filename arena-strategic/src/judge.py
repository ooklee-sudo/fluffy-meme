"""LLM-judge quality controls on the Study 1 matched sample. Names masked, A/B order randomized per pair."""
import sys, re, json, numpy as np, pandas as pd
sys.path.insert(0, 'src'); import orc
from leaks import RX_ANY
D = '/home/user/data'
S = pd.read_pickle(f'{D}/study1_sample_scr.pkl')
rng = np.random.default_rng(0)
L = S[S.leak == 1]
ctrl = []
for _, r in L.iterrows():
    pool = S[(S.leak == 0) & (S.opair == r.opair) & (S.cl50 == r.cl50)]
    if len(pool) < 2: pool = S[(S.leak == 0) & (S.opair == r.opair)]
    ctrl += list(pool.sample(min(2, len(pool)), random_state=int(rng.integers(1e9))).index)
M = pd.concat([L, S.loc[sorted(set(ctrl))]])
print('matched rows', len(M), 'leaked', M.leak.sum())
conv = pd.read_pickle(f'{D}/140k.pkl').set_index('id')
mask = lambda t: RX_ANY.sub('[NAME]', t or '')
def render(turns, n): return mask('\n\n---\n\n'.join(turns))[:n]
JUDGES = {'deepseek': 'deepseek/deepseek-v3.2', 'qwen': 'qwen/qwen3-235b-a22b-2507', 'haiku': 'anthropic/claude-haiku-5.5'}
PROMPT = """Compare two AI assistant responses to the same user conversation. Judge helpfulness, correctness, and how well each serves the user. Names of AI models or companies have been replaced with [NAME]; ignore this.
[USER]
{u}
[RESPONSE A]
{a}
[RESPONSE B]
{b}
Return JSON only: {{"score_a": <1-10>, "score_b": <1-10>, "winner": "A" | "B" | "tie"}}"""
jobs = []
for i, r in M.iterrows():
    c = conv.loc[r.cid]; foc = c[f'{r.side}_turns']; opp = c[f'{"b" if r.side == "a" else "a"}_turns']
    flip = bool(rng.integers(2))
    a, b = (opp, foc) if flip else (foc, opp)
    msg = PROMPT.format(u=('\n---\n'.join(c.user_turns))[:1500], a=render(a, 4000), b=render(b, 4000))
    jobs.append((i, flip, msg))
sub = set(rng.choice(len(jobs), size=min(600, len(jobs)), replace=False))
def run(args):
    k, (i, flip, msg) = args
    out = {'row': i}
    for name, model in JUDGES.items():
        if name == 'haiku' and k not in sub: continue
        t = orc.chat(model, [{'role': 'user', 'content': msg}], max_tokens=300, reasoning={'enabled': False})
        try:
            j = json.loads(re.search(r'\{.*?\}', t or '', re.S).group(0)); sa, sb = float(j['score_a']), float(j['score_b']); w = j['winner']
            sf, so = (sb, sa) if flip else (sa, sb)
            wf = {'A': 0, 'B': 1}.get(w, 0.5) if flip else {'A': 1, 'B': 0}.get(w, 0.5)
            out[f'{name}_diff'] = sf - so; out[f'{name}_win'] = wf
        except Exception: pass
    return out
lim = int(sys.argv[1]) if len(sys.argv) > 1 else len(jobs)
res = pd.DataFrame(orc.pmap(run, list(enumerate(jobs))[:lim], 48)).set_index('row')
M = M.join(res); M.to_pickle(f'{D}/study1_matched.pkl')
print(res.notna().mean()); print('total LLM spend so far $%.3f' % orc.spent())
