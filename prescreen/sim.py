"""Policy simulation: does synthetic pre-screening save A/B traffic on Upworthy headline tests?"""
import sys, json, numpy as np, pandas as pd
arms_csv, twin_jsonl, out_json = sys.argv[1:4]
R = 400                                   # simulated experiments per test and budget
BUDGETS = [2000, 4000, 8000, 16000, 32000, 64000]
rng = np.random.default_rng(7)
a = pd.read_csv(arms_csv)
rows = [json.loads(l) for l in open(twin_jsonl)]
tw = pd.DataFrame([dict(test=r['test'], model=r['model'], draw=r['draw'], headline=h, s=v)
                   for r in rows if r.get('pred') for h, v in r['pred'].items()])
tw = tw.groupby(['test', 'model', 'headline'], as_index=False).s.mean()
# within-test z-score of twin scores; ensemble = mean z across models
tw['z'] = tw.groupby(['test', 'model']).s.transform(lambda x: (x - x.mean()) / (x.std(ddof=0) + 1e-9))
ens = tw.groupby(['test', 'headline'], as_index=False).z.mean().assign(model='ensemble')
tw = pd.concat([tw, ens], ignore_index=True)
a = a.rename(columns={'clickability_test_id': 'test'})
a['K'] = a.groupby('test').headline.transform('size')
a['dev'] = a.y_true - a.groupby('test').y_true.transform('mean')
a['dev_raw'] = a.y - a.groupby('test').y.transform('mean')
TAU2 = max((a.dev_raw**2 * a.K / (a.K - 1)).mean() - a.v.mean(), 1e-4)   # variance of true headline effects

def diagnostics(df):
    # pairwise agreement and implied rho
    agree, n = 0, 0
    for _, g in df.groupby('test'):
        z, y = g.z.values, g.y_true.values
        i, j = np.triu_indices(len(z), 1)
        ok = (z[i] != z[j])
        agree += ((np.sign(z[i] - z[j]) == np.sign(y[i] - y[j])) & ok).sum() + 0.5 * (~ok).sum(); n += len(i)
    pa = agree / n
    r = np.corrcoef(df.z, df.dev)[0, 1]
    return dict(pairwise_agree=pa, implied_rho=float(np.sin(np.pi * (pa - .5))), corr_z_dev=float(r))

def simulate(df, m_frac=0.5, prior=None):
    out = {p: {N: [] for N in BUDGETS} for p in ['A_all', 'B_twin_topm', 'C_random_m', 'D_twin_only', 'E_twin_prior']}
    discard = []
    for t, g in df.groupby('test'):
        p = g.p_true.values; z = g.z.values; K = len(p); m = max(2, int(round(K * m_frac)))
        best = p.max()
        topm = np.argsort(-z)[:m]
        discard.append(p.argmax() not in topm)
        def run(idx, N, prior_mu=None):
            n = N // len(idx)
            c = rng.binomial(n, p[idx], size=(R, len(idx)))
            if prior_mu is None:
                est = c / n + rng.uniform(0, 1e-9, c.shape)        # random tie-break
            else:                                               # normal-normal on logit scale
                ph = (c + .5) / (n + 1); y = np.log(ph / (1 - ph)); v = 1 / (c + .5) + 1 / (n - c + .5)
                pm, pv = prior_mu[idx], prior['var']
                est = (y / v + pm / pv) / (1 / v + 1 / pv)
            pick = idx[est.argmax(1)]
            return (best - p[pick]) / best, (p[pick] == best)
        for N in BUDGETS:
            for name, idx, pm in [('A_all', np.arange(K), None), ('B_twin_topm', topm, None),
                                  ('C_random_m', None, None), ('E_twin_prior', np.arange(K), 'prior')]:
                if name == 'C_random_m':
                    regs, hits = [], []
                    for _ in range(4):
                        rg, h = run(rng.choice(K, m, replace=False), N); regs.append(rg[:R // 4]); hits.append(h[:R // 4])
                    rg, h = np.concatenate(regs), np.concatenate(hits)
                elif pm == 'prior':
                    mu = g.y_true.mean() + prior['b'] * z           # prior uses twin only + test mean level
                    rg, h = run(idx, N, mu)
                else:
                    rg, h = run(idx, N)
                out[name][N].append((rg.mean(), h.mean()))
            out['D_twin_only'][N].append(((best - p[z.argmax()]) / best, float(p[z.argmax()] == best)))
    res = {name: {N: dict(regret=float(np.mean([x[0] for x in v])), p_best=float(np.mean([x[1] for x in v])))
                  for N, v in d.items()} for name, d in out.items()}
    res['false_discard_rate'] = float(np.mean(discard))
    return res

def traffic_saving(res, pol, target_N=16000, metric='p_best'):
    """Share of traffic saved: budget the policy needs to match A_all at target_N (log-linear interpolation)."""
    sgn = 1 if metric == 'p_best' else -1                 # regret: lower is better
    goal = sgn * res['A_all'][target_N][metric]
    xs = np.log(BUDGETS); ys = np.array([sgn * res[pol][N][metric] for N in BUDGETS])
    if ys.max() < goal: return None
    if ys[0] >= goal: return 1 - BUDGETS[0] / target_N
    k = np.argmax(ys >= goal)
    x = xs[k - 1] + (goal - ys[k - 1]) * (xs[k] - xs[k - 1]) / (ys[k] - ys[k - 1])
    return float(1 - np.exp(x) / target_N)

result = {}
tests = sorted(tw.test.unique()); rng2 = np.random.default_rng(1); rng2.shuffle(tests)
folds = {t: i % 2 for i, t in enumerate(tests)}
for model, g in tw.groupby('model'):
    df = a.merge(g[['test', 'headline', 'z']], on=['test', 'headline'])
    full = df.groupby('test').headline.transform('size') == df.groupby('test').K.transform('first')
    df = df[full & df.groupby('test').z.transform(lambda x: x.std() > 0)]
    diag = diagnostics(df)
    # cross-fitted prior calibration: slope of true logit deviation on twin z, fit on other fold
    parts = []
    for f in (0, 1):
        tr, te = df[df.test.map(folds) != f], df[df.test.map(folds) == f]
        b = np.polyfit(tr.z, tr.dev_raw, 1)[0]                  # noise in raw CTR is independent of z
        r = simulate(te, prior=dict(b=b, var=max(TAU2 - b**2 * tr.z.var(), 0.2 * TAU2)))
        parts.append((len(te.test.unique()), r, b))
    n0, n1 = parts[0][0], parts[1][0]
    comb = {}
    for pol in parts[0][1]:
        if pol == 'false_discard_rate':
            comb[pol] = (n0 * parts[0][1][pol] + n1 * parts[1][1][pol]) / (n0 + n1); continue
        comb[pol] = {N: {k: (n0 * parts[0][1][pol][N][k] + n1 * parts[1][1][pol][N][k]) / (n0 + n1)
                         for k in ('regret', 'p_best')} for N in BUDGETS}
    pols = ['B_twin_topm', 'C_random_m', 'E_twin_prior']
    comb['saving'] = {f'{met}@{N}': {p: traffic_saving(comb, p, N, met) for p in pols}
                      for met in ('p_best', 'regret') for N in (4000, 16000)}
    result[model] = dict(n_tests=int(df.test.nunique()), **diag, prior_slope=float(np.mean([p[2] for p in parts])), **comb)
    print(model, result[model]['n_tests'], {k: round(v, 3) for k, v in diag.items()},
          'discard', round(comb['false_discard_rate'], 3), 'saving', comb['saving'], flush=True)
json.dump(result, open(out_json, 'w'), indent=1)
