"""Study 2R with larger / reasoning models (prereg/qq_large_models_prereg.md)."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, 'src'); import orc
import qq_counterbalanced as cb
D = '/home/user/data'
MODELS = {'deepseek': ('deepseek/deepseek-v3.2', dict(max_tokens=5, reasoning={'enabled': False})),
          'qwen235b': ('qwen/qwen3-235b-a22b-2507', dict(max_tokens=5, reasoning={'enabled': False})),
          'deepseek_reason': ('deepseek/deepseek-v3.2', dict(max_tokens=3000, reasoning={'enabled': True}))}
def trial(args):
    item, order, k, p, mp, mn = args
    qa, qb, era = cb.S2ITEMS[item]; q1, q2 = (qa, qb) if order == 'AB' else (qb, qa)
    sysm = f'You are taking part in a US national telephone opinion poll in the {era}. Answer as yourself: {p}. Answer based on your honest opinion. ' + cb.sysline(mp)
    model, kw = MODELS[mn]
    m = [{'role': 'system', 'content': sysm}, {'role': 'user', 'content': f'{q1} {cb.tag(mp)}'}]
    a1 = orc.chat(model, m, temperature=1.0, **kw); v1 = cb.parse(a1, mp)
    if v1 is None: return None
    a2 = orc.chat(model, m + [{'role': 'assistant', 'content': a1.strip()[:20]}, {'role': 'user', 'content': f'{q2} {cb.tag(mp)}'}], temperature=1.0, **kw); v2 = cb.parse(a2, mp)
    if v2 is None: return None
    return dict(study='2RL', item=item, model=mn, order=order, map=mp, k=k, first=v1, second=v2)
if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    rng = np.random.default_rng(31415); cb.rng2 = rng
    jobs = [(it, o, k, cb.persona(), mp, mn) for it in cb.S2ITEMS for o in ('AB', 'BA') for mp in cb.MAPS for k in range(n) for mn in MODELS]
    before = orc.spent()
    R = pd.DataFrame([r for r in orc.pmap(trial, jobs, 64) if r]); R.to_pickle(f'{D}/cb_study2_large{"" if n >= 150 else "_pilot"}.pkl')
    print('trials', len(jobs), 'valid', len(R), '| cost $%.3f' % (orc.spent() - before)); print(R.groupby('model').size())
