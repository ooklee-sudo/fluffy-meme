"""Stage-2 LLM screen of regex-flagged leaks: genuine self-disclosure? induced by user?"""
import sys, json, re, pandas as pd
sys.path.insert(0, 'src'); import orc
from leaks import RX
D = '/home/user/data'; M = 'anthropic/claude-haiku-5.5'
d = pd.read_pickle(f'{D}/140k.pkl').set_index('id')
f = pd.read_pickle(f'{D}/conv140_flags.pkl')
f = f[f.self_a | f.self_b | f.other_a | f.other_b]
items = []
for _, r in f.iterrows():
    c = d.loc[r.id]
    for side in 'ab':
        if r[f'self_{side}'] or r[f'other_{side}']:
            turns = c[f'{side}_turns']
            for i, t in enumerate(turns):
                m = RX.search(t or '')
                if m:
                    items.append(dict(id=r.id, side=side, model=r[f'model_{side}'], users=' || '.join(u[:400] for u in c.user_turns[:i+1]),
                                      snip=(t[max(0, m.start()-300):m.end()+200]))); break
PROMPT = """You are auditing chatbot transcripts. A model's reply contains a passage that mentions an AI model or company.
User message(s) so far: <<<{users}>>>
Passage from the model's reply: <<<{snip}>>>
Answer in JSON with keys:
"self_disclosure": true if the model states, in the first person, its own name or the company that made it (e.g. "I'm Claude, made by Anthropic"); false if it merely discusses other models, quotes, role-plays a character, or writes code/text mentioning them.
"claimed": the model or company it claims to be (string, or null).
"user_induced": true if the user asked who/what the model is, its name, creator, or which model it is, or asked it to introduce itself; else false.
Return JSON only."""
def run(it):
    t = orc.chat(M, [{'role': 'user', 'content': PROMPT.format(**it)}], max_tokens=300, reasoning={'enabled': False})
    try: j = json.loads(re.search(r'\{.*\}', t, re.S).group(0))
    except Exception: j = {}
    return {**it, **{k: j.get(k) for k in ('self_disclosure', 'claimed', 'user_induced')}}
out = pd.DataFrame(orc.pmap(run, items, 24))
out.to_pickle(f'{D}/screen.pkl')
print(len(out), 'cost so far $%.3f' % orc.spent())
print(pd.crosstab(out.self_disclosure, out.user_induced, dropna=False))
