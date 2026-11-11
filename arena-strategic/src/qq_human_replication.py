"""Do LLM 'silicon respondents' reproduce human question-order effects and the QQ equality?
Human benchmark: Wang, Solloway, Shiffrin & Busemeyer (2014, PNAS), Table 1 (Gallup polls, ~1,000 US adults each)."""
import sys, re, numpy as np, pandas as pd
sys.path.insert(0, 'src'); import orc
D = '/home/user/data'
MODELS = {'qwen': 'qwen/qwen3.7-flash', 'haiku': 'anthropic/claude-haiku-5.5', 'llama': 'meta-llama/llama-4-scout'}
# Human cells (Yes-Yes, Yes-No, No-Yes, No-No), first answer = first question in that order
HUMAN = {
 'clinton_gore': {'AB': [0.4899, 0.0447, 0.1767, 0.2886], 'BA': [0.5625, 0.0255, 0.1991, 0.2130]},
 'white_black':  {'AB': [0.3987, 0.0174, 0.1612, 0.4227], 'BA': [0.4012, 0.1379, 0.0597, 0.4012]},
 'rose_jackson': {'AB': [0.3379, 0.3241, 0.0178, 0.3202], 'BA': [0.4156, 0.1234, 0.0671, 0.3939]},
}
ITEMS = {
 'clinton_gore': ('Do you generally think Bill Clinton is honest and trustworthy, or not?', 'Do you generally think Al Gore is honest and trustworthy, or not?', 'late 1990s'),
 'white_black':  ('Do you think that most white people dislike black people, or not?', 'Do you think that most black people dislike white people, or not?', 'late 1990s'),
 'rose_jackson': ('Do you think Pete Rose should or should not be eligible for admission to the Hall of Fame? Answer Yes if he should be eligible.', 'Do you think Shoeless Joe Jackson should or should not be eligible for admission to the Hall of Fame? Answer Yes if he should be eligible.', 'late 1990s'),
 # novel pairs, no published human data (contamination check)
 'bonds_clemens': ('Do you think Barry Bonds should be admitted to the Baseball Hall of Fame, or not?', 'Do you think Roger Clemens should be admitted to the Baseball Hall of Fame, or not?', 'early 2020s'),
 'urban_rural':  ('Do you think that most people who live in big cities look down on people who live in rural areas, or not?', 'Do you think that most people who live in rural areas look down on people who live in big cities, or not?', 'early 2020s'),
}
rng = np.random.default_rng(2014)
def persona():
    age = int(rng.integers(18, 86)); g = rng.choice(['man', 'woman'])
    race = rng.choice(['White', 'Black', 'Hispanic', 'Asian American'], p=[0.72, 0.12, 0.11, 0.05])
    party = rng.choice(['Republican', 'Democrat', 'independent'], p=[0.32, 0.34, 0.34])
    edu = rng.choice(['did not finish high school', 'a high school diploma', 'some college', 'a four-year college degree', 'a graduate degree'], p=[0.12, 0.30, 0.28, 0.19, 0.11])
    region = rng.choice(['the Northeast', 'the Midwest', 'the South', 'the West'], p=[0.18, 0.22, 0.37, 0.23])
    return f'a {age}-year-old {race} {g} from {region} with {edu}, who identifies as a {party}'
if __name__ == '__main__':
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    jobs = []
    for item, (qa, qb, era) in ITEMS.items():
        for order in ('AB', 'BA'):
            for k in range(N):
                p = persona()
                for mn in MODELS: jobs.append((item, order, k, p, era, mn))
    yn = lambda t: None if t is None else (1 if re.match(r'\W*yes', t, re.I) else 0 if re.match(r'\W*no', t, re.I) else None)
    def run(job):
        item, order, k, p, era, mn = job
        qa, qb, _ = ITEMS[item]; q1, q2 = (qa, qb) if order == 'AB' else (qb, qa)
        sysm = (f'You are taking part in a US national telephone opinion poll in the {era}. Answer as yourself: {p}. '
                'Answer each question with a single word, Yes or No, based on your honest opinion.')
        kw = dict(max_tokens=5, temperature=1.0, reasoning={'enabled': False})
        m = [{'role': 'system', 'content': sysm}, {'role': 'user', 'content': q1}]
        a1 = orc.chat(MODELS[mn], m, **kw)
        if yn(a1) is None: return None
        a2 = orc.chat(MODELS[mn], m + [{'role': 'assistant', 'content': a1.strip()}, {'role': 'user', 'content': q2}], **kw)
        if yn(a2) is None: return None
        return dict(item=item, order=order, k=k, model=mn, first=yn(a1), second=yn(a2))
    before = orc.spent()
    out = pd.DataFrame([r for r in orc.pmap(run, jobs, 48) if r])
    out.to_pickle(f'{D}/qq_human_rep.pkl')
    print('trials', len(jobs), 'valid', len(out), 'cost $%.3f' % (orc.spent() - before))
