"""Best-of-n selection on MT-Bench: choose the answer GPT-4 (J) prefers among n candidates,
then check it against expert human votes (G) on a randomly drawn incumbent from the same set.
    python mt_bench_bestofn.py human.parquet gpt4.parquet out.json
"""
import sys, json, itertools
import numpy as np, pandas as pd
from mt_bench_ledger import load, CANARY

def main(hp, gp, out, draws=300):
    rng = np.random.default_rng(1)
    h, g, m = load(hp, gp)
    gj = g.copy(); gj['J'] = gj.winner.map({'model_a':1,'model_b':-1,'tie':0,'tie (inconsistent)':0})
    gj['len_a'] = g.len_a; gj['len_b'] = g.len_b
    Jt, Gt, L = {}, {}, {}
    for _, r in gj.iterrows():
        Jt[(r.question_id, r.turn, r.model_a, r.model_b)] = r.J
        L[(r.question_id, r.turn, r.model_a)] = r.len_a; L[(r.question_id, r.turn, r.model_b)] = r.len_b
    for _, r in m.iterrows():
        Gt[(r.question_id, r.turn, r.model_a, r.model_b)] = r.G
    def pj(q, t, a, b):   # J outcome of a vs b (+1 a wins)
        k = (q, t, a, b)
        if k in Jt: return Jt[k]
        return -Jt[(q, t, b, a)]
    def pg(q, t, a, b):
        k = (q, t, a, b)
        if k in Gt: return Gt[k]
        k2 = (q, t, b, a)
        return -Gt[k2] if k2 in Gt else None
    models = sorted(set(m.model_a) | set(m.model_b))
    qts = sorted({(r.question_id, r.turn) for _, r in m.iterrows()})
    res = {}
    for scope, keep in (('all', lambda q: True), ('canary', lambda q: ((q - 81)//10) in (2, 3, 4)),
                        ('noncanary', lambda q: ((q - 81)//10) not in (2, 3, 4))):
        res[scope] = {}
        for n in range(2, 7):
            win, tot, lens, lenb = 0.0, 0, [], []
            for q, t in qts:
                if not keep(q): continue
                for _ in range(draws // 10):
                    S = list(rng.choice(models, n, replace=False))
                    sc = {a: sum(pj(q, t, a, b) for b in S if b != a) + 1e-6 * rng.random() for a in S}
                    sel = max(sc, key=sc.get)
                    base = S[int(rng.integers(0, n))]
                    while base == sel: base = S[int(rng.integers(0, n))]
                    gv = pg(q, t, sel, base)
                    if gv is None: continue
                    win += 1.0 if gv > 0 else (0.5 if gv == 0 else 0.0); tot += 1
                    lens.append(L[(q, t, sel)]); lenb.append(L[(q, t, base)])
            res[scope][n] = {'human_win_rate_selected_vs_random': round(win / tot, 3), 'n_evals': tot,
                             'mean_len_selected': round(float(np.mean(lens))), 'mean_len_baseline': round(float(np.mean(lenb)))}
    json.dump(res, open(out, 'w'), indent=2); print(json.dumps(res, indent=1))

if __name__ == '__main__':
    main(*sys.argv[1:4])
