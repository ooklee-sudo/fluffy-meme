"""Preregistered test: do LLM judgments about nonexistent entities (hallucination) follow the QQ equality
more often than matched judgments about real entities? See arena-strategic/prereg/qq_hallucination_prereg.md."""
import sys, re, pandas as pd
sys.path.insert(0, 'src'); import orc
D = '/home/user/data'
MODELS = {'qwen': 'qwen/qwen3.7-flash', 'haiku': 'anthropic/claude-haiku-5.5', 'llama': 'meta-llama/llama-4-scout'}
# (entity description, question A, question B); fictional items mirror the real items one to one
F = [
 ("the novel 'The Glass Orchard' by Mirela Voss", 'Is it a tragedy?', 'Did it win a major literary prize?'),
 ("the film 'Northern Saltwork' (1987), directed by Oskar Lindqvist", 'Was it a commercial success?', 'Was it filmed in black and white?'),
 ("the Brennholt Bridge in Austria", 'Was it built before 1900?', 'Is it open to cars?'),
 ("the Rethwick reaction in organic chemistry", 'Is it widely used in industry?', 'Does it require a metal catalyst?'),
 ("the Scottish band The Pale Cartographers", 'Did they have a UK top-40 single?', 'Are they still active?'),
 ("Talvera Island in the Aegean Sea", 'Is it inhabited year-round?', 'Can it be reached by ferry?'),
 ("the Ilsworth curve in economics", 'Is it supported by empirical evidence?', 'Is it taught in introductory economics courses?'),
 ("the Kessandra grape variety", 'Is it used mostly for red wine?', 'Is it grown commercially outside Europe?'),
 ("the board game 'Hollow Crown Merchants' (2011)", 'Is it a competitive game rather than a cooperative one?', 'Did it win a major game award?'),
 ("the Varnholm Treaty of 1743", 'Did it end a war?', 'Is it still cited in international law?'),
 ("the programming language Quillet (2006)", 'Is it statically typed?', 'Is it used in production by large companies?'),
 ("the Belgian painter Lucia Fenwarde", 'Was she mainly a landscape painter?', 'Are her works held by a national museum?'),
]
R = [
 ("the novel 'Pride and Prejudice' by Jane Austen", 'Is it a tragedy?', 'Did it win a major literary prize?'),
 ("the film 'Casablanca' (1942), directed by Michael Curtiz", 'Was it a commercial success?', 'Was it filmed in black and white?'),
 ("the Golden Gate Bridge in San Francisco", 'Was it built before 1900?', 'Is it open to cars?'),
 ("the Haber-Bosch process in chemistry", 'Is it widely used in industry?', 'Does it require a metal catalyst?'),
 ("the English band Radiohead", 'Did they have a UK top-40 single?', 'Are they still active?'),
 ("the island of Santorini in the Aegean Sea", 'Is it inhabited year-round?', 'Can it be reached by ferry?'),
 ("the Phillips curve in economics", 'Is it supported by empirical evidence?', 'Is it taught in introductory economics courses?'),
 ("the Xinomavro grape variety", 'Is it used mostly for red wine?', 'Is it grown commercially outside Europe?'),
 ("the board game 'Hanabi' (2010)", 'Is it a competitive game rather than a cooperative one?', 'Did it win a major game award?'),
 ("the Treaty of Abo of 1743", 'Did it end a war?', 'Is it still cited in international law?'),
 ("the programming language Nim (2008)", 'Is it statically typed?', 'Is it used in production by large companies?'),
 ("the Belgian painter Theo van Rysselberghe", 'Was he mainly a landscape painter?', 'Are his works held by a national museum?'),
]
ITEMS = {f'F{i+1:02d}': ('F',) + x for i, x in enumerate(F)}
ITEMS.update({f'R{i+1:02d}': ('R',) + x for i, x in enumerate(R)})
SYS = 'Answer each question with a single word: Yes or No.'
yn = lambda t: None if t is None else (1 if re.match(r'\W*yes', t, re.I) else 0 if re.match(r'\W*no', t, re.I) else None)
def kw(rep): return dict(max_tokens=5, temperature=1.0, reasoning={'enabled': False}, seed=rep)
def trial(job):
    item, order, rep, mn = job
    typ, ent, qa, qb = ITEMS[item]; q1, q2 = (qa, qb) if order == 'AB' else (qb, qa)
    m = [{'role': 'system', 'content': SYS}, {'role': 'user', 'content': f'This question is about {ent}. {q1}'}]
    a1 = orc.chat(MODELS[mn], m, **kw(rep))
    v1 = yn(a1)
    if v1 is None: return dict(item=item, type=typ, order=order, rep=rep, model=mn, answered=0)
    a2 = orc.chat(MODELS[mn], m + [{'role': 'assistant', 'content': a1.strip()}, {'role': 'user', 'content': q2}], **kw(rep))
    v2 = yn(a2)
    if v2 is None: return dict(item=item, type=typ, order=order, rep=rep, model=mn, answered=0)
    return dict(item=item, type=typ, order=order, rep=rep, model=mn, answered=1, first=v1, second=v2)
def known(job):
    item, rep, mn = job; typ, ent, _, _ = ITEMS[item]
    a = orc.chat(MODELS[mn], [{'role': 'system', 'content': SYS}, {'role': 'user', 'content': f'Do you know {ent}?'}], **kw(1000 + rep))
    return dict(item=item, type=typ, rep=rep, model=mn, says_known=yn(a))
if __name__ == '__main__':
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    jobs = [(it, o, r, mn) for it in ITEMS for o in ('AB', 'BA') for r in range(N) for mn in MODELS]
    kj = [(it, r, mn) for it in ITEMS for r in range(20 if N >= 200 else 2) for mn in MODELS]
    before = orc.spent()
    T = pd.DataFrame(orc.pmap(trial, jobs, 64)); K = pd.DataFrame(orc.pmap(known, kj, 64))
    tag = '' if N >= 200 else '_pilot'
    T.to_pickle(f'{D}/qq_halluc{tag}.pkl'); K.to_pickle(f'{D}/qq_halluc_known{tag}.pkl')
    print('trials', len(T), 'answered', int(T.answered.sum()), '| known checks', len(K), '| cost $%.3f' % (orc.spent() - before))
