"""Preregistered test: QQ conformity in LLM judgments, stimulus-based (S) vs knowledge/policy-based (K) tasks.
See arena-strategic/prereg/qq_task_type_prereg.md."""
import sys, re, json, numpy as np, pandas as pd
sys.path.insert(0, 'src'); import orc
D = '/home/user/data'
MODELS = {'qwen': 'qwen/qwen3.7-flash', 'haiku': 'anthropic/claude-haiku-5.5', 'llama': 'meta-llama/llama-4-scout'}
K_ITEMS = [
 ('Is Donald Trump honest and trustworthy, or not?', 'Is Joe Biden honest and trustworthy, or not?'),
 ('Is Elon Musk trustworthy, or not?', 'Is Mark Zuckerberg trustworthy, or not?'),
 ('Should Lance Armstrong be allowed to keep his Tour de France titles, or not?', 'Should Marion Jones be allowed to keep her Olympic medals, or not?'),
 ('Do you think most Republicans dislike Democrats, or not?', 'Do you think most Democrats dislike Republicans, or not?'),
 ('Do you think most Americans distrust China, or not?', 'Do you think most Chinese people distrust America, or not?'),
 ('Is the federal government doing a good job, or not?', 'Is your state government doing a good job, or not?'),
 ('Are the news media generally trustworthy, or not?', 'Are social media platforms generally trustworthy, or not?'),
 ('Should the death penalty be legal, or not?', 'Should abortion be legal in most cases, or not?'),
 ('Was Richard Nixon a good president, or not?', 'Was Ronald Reagan a good president, or not?'),
 ('Is Apple an ethical company, or not?', 'Is Amazon an ethical company, or not?'),
 ('Do you think most young people respect older people, or not?', 'Do you think most older people respect young people, or not?'),
 ('Should marijuana be legal for recreational use, or not?', 'Should sports betting be legal, or not?'),
]
S_PAIRS = [
 ('Is this answer clear, or not?', 'Is this answer accurate, or not?'),
 ('Is this answer helpful, or not?', 'Is this answer concise, or not?'),
 ('Is the tone of this answer friendly, or not?', 'Is the tone of this answer professional, or not?'),
 ('Would you trust this answer, or not?', 'Would you recommend this assistant to a friend, or not?'),
 ('Is this answer well organized, or not?', 'Is this answer complete, or not?'),
 ('Does this answer address what was asked, or not?', 'Does this answer contain unnecessary information, or not?'),
]
STIM = json.load(open('/home/user/fluffy-meme/arena-strategic/prereg/qq_task_type_stimuli.json'))
ITEMS = {f'K{i+1:02d}': ('K', None, a, b) for i, (a, b) in enumerate(K_ITEMS)}
ITEMS.update({f'S{i+1:02d}': ('S', STIM[i], *S_PAIRS[i % 6]) for i in range(12)})
rng = np.random.default_rng(2026)
def persona():
    age = int(rng.integers(18, 86)); g = rng.choice(['man', 'woman'])
    race = rng.choice(['White', 'Black', 'Hispanic', 'Asian American'], p=[0.62, 0.13, 0.18, 0.07])
    party = rng.choice(['Republican', 'Democrat', 'independent'], p=[0.30, 0.30, 0.40])
    edu = rng.choice(['did not finish high school', 'a high school diploma', 'some college', 'a four-year college degree', 'a graduate degree'], p=[0.09, 0.28, 0.28, 0.22, 0.13])
    region = rng.choice(['the Northeast', 'the Midwest', 'the South', 'the West'], p=[0.17, 0.21, 0.38, 0.24])
    return f'a {age}-year-old {race} {g} from {region} with {edu}, who identifies as a {party}'
yn = lambda t: None if t is None else (1 if re.match(r'\W*yes', t, re.I) else 0 if re.match(r'\W*no', t, re.I) else None)
def run(job):
    item, order, k, p, mn = job
    typ, stim, qa, qb = ITEMS[item]; q1, q2 = (qa, qb) if order == 'AB' else (qb, qa)
    if typ == 'K':
        sysm = f'You are taking part in a US national telephone opinion poll today. Answer as yourself: {p}. Answer each question with a single word, Yes or No, based on your honest opinion.'
        first = q1
    else:
        sysm = f'You are taking part in a US study about answers written by AI assistants. Answer as yourself: {p}. Answer each question with a single word, Yes or No, based on your honest opinion.'
        first = f"Someone asked an AI assistant:\n\"{stim['prompt']}\"\n\nThe assistant answered:\n\"{stim['response']}\"\n\n{q1}"
    kw = dict(max_tokens=5, temperature=1.0, reasoning={'enabled': False})
    m = [{'role': 'system', 'content': sysm}, {'role': 'user', 'content': first}]
    a1 = orc.chat(MODELS[mn], m, **kw)
    if yn(a1) is None: return None
    a2 = orc.chat(MODELS[mn], m + [{'role': 'assistant', 'content': a1.strip()}, {'role': 'user', 'content': q2}], **kw)
    if yn(a2) is None: return None
    return dict(item=item, type=typ, order=order, k=k, model=mn, first=yn(a1), second=yn(a2))
if __name__ == '__main__':
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    jobs = [(it, o, k, persona(), mn) for it in ITEMS for o in ('AB', 'BA') for k in range(N) for mn in MODELS]
    before = orc.spent()
    out = pd.DataFrame([r for r in orc.pmap(run, jobs, 64) if r])
    out.to_pickle(f'{D}/qq_task_type{"_pilot" if N < 200 else ""}.pkl')
    print('trials', len(jobs), 'valid', len(out), 'cost $%.3f' % (orc.spent() - before))
