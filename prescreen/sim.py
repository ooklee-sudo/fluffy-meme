"""Policy simulation: does synthetic pre-screening save A/B traffic on Upworthy headline tests?

Usage: python sim.py arms.csv twin.jsonl[,more.jsonl] out.json [truth]
truth = eb    : true CTR = empirical-Bayes shrinkage estimate on all impressions (main analysis)
        raw   : true CTR = raw CTR on all impressions (no shrinkage; overstates true spread)
        split : impressions split in two halves; truth = EB estimate on half B only, while the
                prior is calibrated on half A, so calibration noise and truth noise are independent
95% intervals come from a bootstrap over tests (B = 1000).
"""
import sys, json, numpy as np, pandas as pd
arms_csv, twin_files, out_json = sys.argv[1:4]
TRUTH = sys.argv[4] if len(sys.argv) > 4 else 'eb'
R = 400                                   # simulated experiments per test and budget
BUDGETS = [2000, 4000, 8000, 16000, 32000, 64000]
NBOOT = 1000
POLS = ['A_all', 'B_twin_topm', 'C_random_m', 'D_twin_only', 'E_twin_prior']
ENSEMBLES = {
    'ensemble_original': ['anthropic/claude-haiku-5.5', 'google/gemini-3.7-flash', 'meta-llama/llama-4-maverick',
                          'openai/gpt-5.6-luna', 'x-ai/grok-4.3'],
    'ensemble_current': ['anthropic/claude-haiku-5.5', 'google/gemini-3.7-flash', 'openai/gpt-6-luna',
                         'deepseek/deepseek-v4.1-flash'],
}
rng = np.random.default_rng(7)

# ---------- twin scores ----------
rows = [json.loads(l) for f in twin_files.split(',') for l in open(f)]
tw = pd.DataFrame([dict(test=r['test'], model=r['model'], draw=r['draw'], headline=h, s=v)
                   for r in rows if r.get('pred') for h, v in r['pred'].items()])
tw = tw.groupby(['test', 'model', 'headline'], as_index=False).s.mean()
tw['z'] = tw.groupby(['test', 'model']).s.transform(lambda x: (x - x.mean()) / (x.std(ddof=0) + 1e-9))
for name, members in ENSEMBLES.items():
    sub = tw[tw.model.isin(members)]
    if sub.model.nunique() == len(members):
        full = sub.groupby(['test', 'headline']).model.transform('nunique') == len(members)
        tw = pd.concat([tw, sub[full].groupby(['test', 'headline'], as_index=False).z.mean().assign(model=name)],
                       ignore_index=True)

# ---------- truth ----------
a = pd.read_csv(arms_csv).rename(columns={'clickability_test_id': 'test'})
a['K'] = a.groupby('test').headline.transform('size')

def logit_stats(clicks, imps):
    p = (clicks + .5) / (imps + 1)
    return np.log(p / (1 - p)), 1 / (clicks + .5) + 1 / (imps - clicks + .5)

def eb(df, y, v):
    dev = y - df.assign(y=y).groupby('test').y.transform('mean')
    tau2 = max(((dev**2) * df.K / (df.K - 1)).mean() - v.mean(), 1e-6)
    mu = y - dev
    return mu + tau2 / (tau2 + v) * dev, tau2

if TRUTH == 'split':
    srng = np.random.default_rng(11)
    nA = (a.impressions // 2).astype(int)
    cA = srng.hypergeometric(a.clicks.astype(int), (a.impressions - a.clicks).astype(int), nA)
    yA, vA = logit_stats(cA, nA)                                   # half A: calibration
    yB, vB = logit_stats(a.clicks - cA, a.impressions - nA)        # half B: truth
    a['y_true'], _ = eb(a, yB, vB)
    a['y_cal'], a['v_cal'] = yA, vA
else:
    y, v = logit_stats(a.clicks, a.impressions)
    a['y_true'] = eb(a, y, v)[0] if TRUTH == 'eb' else y
    a['y_cal'], a['v_cal'] = y, v
a['p_true'] = 1 / (1 + np.exp(-a.y_true))
a['dev'] = a.y_true - a.groupby('test').y_true.transform('mean')
a['dev_cal'] = a.y_cal - a.groupby('test').y_cal.transform('mean')
TAU2 = max((a.dev_cal**2 * a.K / (a.K - 1)).mean() - a.v_cal.mean(), 1e-4)  # variance of true headline effects

# ---------- per-test simulation ----------
def simulate_test(g, prior, m_frac=0.5):
    p = g.p_true.values; z = g.z.values; K = len(p); m = max(2, int(round(K * m_frac)))
    best = p.max(); topm = np.argsort(-z)[:m]
    def run(idx, N, prior_mu=None):
        n = N // len(idx)
        c = rng.binomial(n, p[idx], size=(R, len(idx)))
        if prior_mu is None:
            est = c / n + rng.uniform(0, 1e-9, c.shape)
        else:                                                      # normal-normal update on the logit scale
            y, v = logit_stats(c, n)
            est = (y / v + prior_mu[idx] / prior['var']) / (1 / v + 1 / prior['var'])
        pick = idx[est.argmax(1)]
        return ((best - p[pick]) / best).mean(), (p[pick] == best).mean()
    out = {pol: np.zeros((len(BUDGETS), 2)) for pol in POLS}
    mu = g.y_true.mean() + prior['b'] * z
    for k, N in enumerate(BUDGETS):
        out['A_all'][k] = run(np.arange(K), N)
        out['B_twin_topm'][k] = run(topm, N)
        out['C_random_m'][k] = np.mean([run(rng.choice(K, m, replace=False), N) for _ in range(4)], axis=0)
        out['E_twin_prior'][k] = run(np.arange(K), N, mu)
        out['D_twin_only'][k] = ((best - p[z.argmax()]) / best, float(p[z.argmax()] == best))
    i, j = np.triu_indices(K, 1); y = g.y_true.values
    tie = z[i] == z[j]
    agree = ((np.sign(z[i] - z[j]) == np.sign(y[i] - y[j])) & ~tie).sum() + 0.5 * tie.sum()
    return out, float(p.argmax() not in topm), agree, len(i)

def saving(curve_A, curve_P, target_k):
    """Traffic share saved by policy P for the same expected regret as A at BUDGETS[target_k]."""
    goal = curve_A[target_k]; xs = np.log(BUDGETS); ys = curve_P
    if ys.min() > goal: return np.nan                               # never reaches A's regret
    if ys[0] <= goal: return 1 - BUDGETS[0] / BUDGETS[target_k]
    k = np.argmax(ys <= goal)
    x = xs[k - 1] + (ys[k - 1] - goal) * (xs[k] - xs[k - 1]) / (ys[k - 1] - ys[k])
    return 1 - np.exp(x) / BUDGETS[target_k]

def ci(v):
    v = np.asarray(v, float); v = v[~np.isnan(v)]
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if len(v) else [None, None]

result = {'truth': TRUTH, 'budgets': BUDGETS}
tests = sorted(tw.test.unique()); np.random.default_rng(1).shuffle(tests)
folds = {t: i % 2 for i, t in enumerate(tests)}
K16 = BUDGETS.index(16000)
for model, g in tw.groupby('model'):
    df = a.merge(g[['test', 'headline', 'z']], on=['test', 'headline'])
    full = df.groupby('test').headline.transform('size') == df.K
    df = df[full & df.groupby('test').z.transform(lambda x: x.std() > 0)]
    per = []                                                       # one record per test
    slopes = []
    for f in (0, 1):
        tr, te = df[df.test.map(folds) != f], df[df.test.map(folds) == f]
        b = np.polyfit(tr.z, tr.dev_cal, 1)[0]                     # calibration noise is independent of z
        slopes.append(b)
        prior = dict(b=b, var=max(TAU2 - b**2 * tr.z.var(), 0.2 * TAU2))
        for _, gt in te.groupby('test'):
            per.append(simulate_test(gt, prior))
    T = len(per)
    reg = {pol: np.array([r[0][pol][:, 0] for r in per]) for pol in POLS}     # T x budgets
    hit = {pol: np.array([r[0][pol][:, 1] for r in per]) for pol in POLS}
    disc = np.array([r[1] for r in per]); agr = np.array([r[2] for r in per]); npair = np.array([r[3] for r in per])

    def stats(idx):
        s = {pol: reg[pol][idx].mean(0) for pol in POLS}
        pa = agr[idx].sum() / npair[idx].sum()
        return dict(reg=s, discard=disc[idx].mean(), pa=pa, rho=np.sin(np.pi * (pa - .5)),
                    save_E=saving(s['A_all'], s['E_twin_prior'], K16),
                    diffBA=s['B_twin_topm'][K16] - s['A_all'][K16], diffEA=s['E_twin_prior'][K16] - s['A_all'][K16])
    point = stats(np.arange(T))
    boots = [stats(rng.integers(0, T, T)) for _ in range(NBOOT)]
    res = dict(n_tests=T, pairwise_agree=float(point['pa']), implied_rho=float(point['rho']),
               implied_rho_ci=ci([b['rho'] for b in boots]), prior_slope=float(np.mean(slopes)),
               false_discard_rate=float(point['discard']), false_discard_ci=ci([b['discard'] for b in boots]))
    for pol in POLS:
        res[pol] = {str(N): dict(regret=float(point['reg'][pol][k]), p_best=float(hit[pol][:, k].mean()),
                                 regret_ci=ci([b['reg'][pol][k] for b in boots])) for k, N in enumerate(BUDGETS)}
    res['saving_E_regret@16000'] = float(point['save_E'])
    res['saving_E_regret@16000_ci'] = ci([b['save_E'] for b in boots])
    res['diff_B_minus_A@16000'] = float(point['diffBA']); res['diff_B_minus_A@16000_ci'] = ci([b['diffBA'] for b in boots])
    res['diff_E_minus_A@16000'] = float(point['diffEA']); res['diff_E_minus_A@16000_ci'] = ci([b['diffEA'] for b in boots])
    # B never beats A at any budget?  (crossover diagnostic)
    res['B_better_than_A_at'] = [N for k, N in enumerate(BUDGETS) if point['reg']['B_twin_topm'][k] < point['reg']['A_all'][k]]
    result[model] = res
    print(f"{model:32s} T={T} rho={res['implied_rho']:.2f} {np.round(res['implied_rho_ci'], 2)} "
          f"discard={res['false_discard_rate']:.2f} A={100*res['A_all']['16000']['regret']:.2f} "
          f"B={100*res['B_twin_topm']['16000']['regret']:.2f} E={100*res['E_twin_prior']['16000']['regret']:.2f} "
          f"saveE={100*res['saving_E_regret@16000']:.1f}% {np.round(100*np.array(res['saving_E_regret@16000_ci'], float), 1)} "
          f"B>A at {res['B_better_than_A_at']}", flush=True)
json.dump(result, open(out_json, 'w'), indent=1)
