"""MT-Bench human judgments vs GPT-4 pairwise judge: ledger check for the options paper.

Data: lmsys/mt_bench_human_judgments (CC-BY-4.0). Run:
    python mt_bench_ledger.py human.parquet gpt4.parquet out.json
J = GPT-4 pairwise judge (cheap quote); G = expert human majority (inspection).
Question ids 81-160 map to eight categories of ten questions each; math, reasoning
and coding have verifiable answers and play the role of canary classes.
"""
import sys, json
import numpy as np, pandas as pd

CATS = ['writing','roleplay','reasoning','math','coding','extraction','stem','humanities']
CANARY = {'reasoning','math','coding'}
rng = np.random.default_rng(0)

def last_len(conv):
    return len(conv[-1]['content'])

def load(hp, gp):
    h = pd.read_parquet(hp); g = pd.read_parquet(gp)
    for d in (h, g):
        d['cat'] = d.question_id.map(lambda q: CATS[(q-81)//10])
        d['len_a'] = d.conversation_a.map(last_len); d['len_b'] = d.conversation_b.map(last_len)
    key = ['question_id','model_a','model_b','turn']
    # human majority per pair; ties/splits -> 0
    h['s'] = h.winner.map({'model_a':1,'model_b':-1,'tie':0})
    hm = h.groupby(key).agg(s=('s','sum'), n=('s','size'), cat=('cat','first'),
                            len_a=('len_a','first'), len_b=('len_b','first')).reset_index()
    hm['G'] = np.sign(hm.s)
    g['J'] = g.winner.map({'model_a':1,'model_b':-1,'tie':0,'tie (inconsistent)':0})
    m = hm.merge(g[key+['J']], on=key, how='inner')
    return h, g, m

def boot(fn, df, B=2000):
    vals = [fn(df.iloc[rng.integers(0, len(df), len(df))]) for _ in range(B)]
    return float(np.mean(vals)), [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]

def agree_nt(d):                      # agreement on pairs where both pick a winner
    x = d[(d.G != 0) & (d.J != 0)]
    return float((x.G == x.J).mean()) if len(x) else np.nan

def winrates(d, col):
    rows = {}
    for _, r in d.iterrows():
        for side, sgn in (('model_a', 1), ('model_b', -1)):
            mdl = r[side]; v = r[col] * sgn
            rows.setdefault(mdl, []).append(1.0 if v > 0 else (0.5 if v == 0 else 0.0))
    return {k: float(np.mean(v)) for k, v in rows.items()}

def main(hp, gp, out):
    h, g, m = load(hp, gp)
    R = {'n_human_judgments': len(h), 'n_gpt4_judgments': len(g), 'n_matched_pairs': len(m),
         'n_models': int(pd.concat([m.model_a, m.model_b]).nunique())}
    # 1. mean agreement ("holdout mean") vs canary classes
    R['agree_all'] = boot(agree_nt, m)
    R['agree_noncanary'] = boot(agree_nt, m[~m.cat.isin(CANARY)])
    R['agree_canary'] = boot(agree_nt, m[m.cat.isin(CANARY)])
    R['agree_by_cat'] = {c: agree_nt(m[m.cat == c]) for c in CATS}
    R['agree_by_turn'] = {int(t): agree_nt(m[m.turn == t]) for t in (1, 2)}
    R['n_nonTie_both_by_cat'] = {c: int(((m.cat == c) & (m.G != 0) & (m.J != 0)).sum()) for c in CATS}
    R['judge_tie_rate'] = float((m.J == 0).mean()); R['human_tie_rate'] = float((m.G == 0).mean())
    # 2. verbosity: share of GPT-4 vs human picks going to the longer answer
    m['longer'] = np.sign(m.len_a - m.len_b)
    x = m[(m.G != 0) & (m.J != 0) & (m.longer != 0)]
    R['p_longer_wins_human'] = float((x.G == x.longer).mean())
    R['p_longer_wins_gpt4'] = float((x.J == x.longer).mean())
    dis = x[x.G != x.J]
    R['n_disagree'] = int(len(dis)); R['disagree_gpt4_picks_longer'] = float((dis.J == dis.longer).mean())
    R['disagree_gpt4_picks_longer_canary'] = float((dis[dis.cat.isin(CANARY)].J == dis[dis.cat.isin(CANARY)].longer).mean())
    # 3. ranking: argmax of J vs argmax of G, overall and on canary classes
    for name, d in (('all', m), ('canary', m[m.cat.isin(CANARY)]), ('noncanary', m[~m.cat.isin(CANARY)])):
        wj, wg = winrates(d, 'J'), winrates(d, 'G')
        ms = sorted(wj)
        R['rank_' + name] = {'J': {k: round(wj[k], 3) for k in ms}, 'G': {k: round(wg[k], 3) for k in ms},
                             'argmax_J': max(wj, key=wj.get), 'argmax_G': max(wg, key=wg.get),
                             'range_J': round(max(wj.values()) - min(wj.values()), 3),
                             'range_G': round(max(wg.values()) - min(wg.values()), 3)}
    # 4. promotion decisions: for each model pair, does J's direction match G's? (NPV-on-judge error)
    def pair_dir(d, col):
        t = {}
        for _, r in d.iterrows():
            k = tuple(sorted((r.model_a, r.model_b))); s = r[col] if r.model_a == k[0] else -r[col]
            t[k] = t.get(k, 0) + s
        return {k: np.sign(v) for k, v in t.items()}
    for name, d in (('all', m), ('canary', m[m.cat.isin(CANARY)]), ('noncanary', m[~m.cat.isin(CANARY)])):
        pj, pg = pair_dir(d, 'J'), pair_dir(d, 'G')
        R['promo_dir_' + name] = {'n_pairs': len(pj), 'J_G_disagree': int(sum(pj[k] != pg[k] for k in pj)),
                                  'false_promote_J_up_G_not': int(sum(pj[k] > 0 and pg[k] <= 0 for k in pj) + sum(pj[k] < 0 and pg[k] >= 0 for k in pj))}
    # 5. human-human noise sigma_{J|V}: expert agreement on the same pair vs judge-human
    hh = []
    for _, grp in h.groupby(['question_id','model_a','model_b','turn']):
        s = grp.s.values
        if len(s) >= 2:
            for i in range(len(s)):
                for j in range(i + 1, len(s)):
                    if s[i] != 0 and s[j] != 0: hh.append(s[i] == s[j])
    R['human_human_agree_nontie'] = float(np.mean(hh)); R['n_human_human_pairs'] = len(hh)
    json.dump(R, open(out, 'w'), indent=2, default=float)
    print(json.dumps(R, indent=2, default=float))

if __name__ == '__main__':
    main(*sys.argv[1:4])
