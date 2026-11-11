"""Study 2 (event study around model debuts) and Study 3 (counterfactual Bradley-Terry leaderboards)."""
import sys, numpy as np, pandas as pd, statsmodels.formula.api as smf
from scipy.stats import kendalltau
from scipy.optimize import minimize
D = '/home/user/data'
f = pd.read_pickle(f'{D}/conv140_flags.pkl')
s = pd.read_pickle(f'{D}/screen.pkl'); ok = s[s.self_disclosure == True]
leak_ids = set(ok.id)
conv = pd.read_pickle(f'{D}/140k.pkl')[['id', 'turn', 'user_turns']]
f = f.merge(conv, on='id')
f['day'] = f.ts.dt.floor('D')
norm = f.user_turns.map(lambda t: ' '.join((t[0] if t else '').lower().split())[:300])
f['dup'] = norm.duplicated(keep='first') & (norm.str.len() > 15)   # exact repeat of an earlier prompt
f['single'] = (f.turn == 1)
# ---------- Study 2 -------------
long = pd.concat([f.assign(model=f.model_a, won=(f.winner == 'model_a')), f.assign(model=f.model_b, won=(f.winner == 'model_b'))])
first = long.groupby('model').day.min()
t0 = f.day.min()
debut = first[first > t0 + pd.Timedelta(days=10)]
print('debut events:', {k: str(v.date()) for k, v in debut.items()})
long['k'] = (long.day - long.model.map(debut)).dt.days
ev = long[long.model.isin(debut.index) & long.k.between(0, 42)].copy()
ev['wk'] = np.minimum(ev.k // 7, 5).astype(int)
# outcome by week since debut, model fixed effects, decisive votes only for win share
dec = ev[ev.winner.isin(['model_a', 'model_b'])]
print('\nStudy 2: event-model outcomes by week since debut (model FE; week 5+ = reference)')
for y, data in [('won', dec), ('single', ev), ('dup', ev)]:
    data = data.assign(y=data[y].astype(float))
    m = smf.ols('y ~ C(wk, Treatment(5)) + C(model) + C(opp_dev)', data.assign(opp_dev=np.where(data.model == data.model_a, data.model_b, data.model_a))).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(data.model)[0]})
    print(f'  {y:7s}', '  '.join(f'w{w}:{m.params[f"C(wk, Treatment(5))[T.{w}]"]:+.3f}({m.bse[f"C(wk, Treatment(5))[T.{w}]"]:.3f})' for w in range(5)))
# daily volume share of the debut model relative to its own week-5+ level
vol = ev.groupby(['model', 'wk']).size().div(ev.groupby(['model', 'wk']).day.nunique()).unstack()
print('  daily battles, median across models by week:', vol.median().round(0).to_dict())
# ---------- Study 3 -------------
def bt(df, models):
    idx = {m: i for i, m in enumerate(models)}
    a = df.model_a.map(idx).values; b = df.model_b.map(idx).values
    y = np.select([df.winner == 'model_a', df.winner == 'model_b'], [1.0, 0.0], 0.5)
    def nll(th):
        th = np.r_[0, th]; z = th[a] - th[b]; p = 1 / (1 + np.exp(-z))
        g = y - p; grad = np.bincount(a, g, len(models)) - np.bincount(b, g, len(models))
        return -np.sum(y * np.log(p + 1e-12) + (1 - y) * np.log(1 - p + 1e-12)) + 1e-4 * th @ th, -(grad[1:] - 2e-4 * th[1:])
    th = minimize(nll, np.zeros(len(models) - 1), jac=True, method='L-BFGS-B').x
    return pd.Series(np.r_[0, th] * 400 / np.log(10) + 1000, index=models)
g = f[f.winner != 'both_bad']   # Arena counts both_bad as tie; we drop it for a cleaner BT; results similar
models = sorted(set(g.model_a) | set(g.model_b))
full = bt(g, models)
# flag rules: (1) any confirmed self-disclosure; (2) + battles of debut models in their first 7 days; (3) + repeated prompts
fl1 = g.id.isin(leak_ids)
deb_k = np.maximum((g.day - g.model_a.map(debut)).dt.days.fillna(99).abs() * 0 + (g.day - g.model_a.map(debut)).dt.days.fillna(99),
                   -1)
in_deb = ((g.day - g.model_a.map(debut)).dt.days.between(0, 6)) | ((g.day - g.model_b.map(debut)).dt.days.between(0, 6))
rules = {'leaks': fl1, 'leaks+debut week': fl1 | in_deb, 'leaks+debut+dup prompts': fl1 | in_deb | g.dup}
top = full.sort_values(ascending=False)
print('\nStudy 3: top 10 (full sample):', ', '.join(f'{m}:{v:.0f}' for m, v in top.head(10).items()))
rng = np.random.default_rng(0)
for name, fl in rules.items():
    cf_ = bt(g[~fl], models)
    out = []
    for K in (10, 20):
        mk = top.index[:K]; out.append(f'tau@{K}={kendalltau(full[mk], cf_[mk])[0]:.3f}')
    r_full = full.rank(ascending=False); r_cf = cf_.rank(ascending=False)
    mk = top.index[:20]
    rev = sum((full[i] - full[j]) * (cf_[i] - cf_[j]) < 0 for x, i in enumerate(mk) for j in mk[x + 1:])
    print(f'  drop {name:24s} n_dropped={int(fl.sum()):6d}  {" ".join(out)}  reversals in top20={rev}  max|dScore|={np.abs(cf_ - full).max():.1f}')
# bootstrap: how many top-20 reversals does mere resampling produce?
revs = []
for b in range(30):
    bs = bt(g.sample(len(g), replace=True, random_state=b), models)
    mk = top.index[:20]; revs.append(sum((full[i] - full[j]) * (bs[i] - bs[j]) < 0 for x, i in enumerate(mk) for j in mk[x + 1:]))
print(f'  bootstrap (30 resamples) top-20 reversals: median={np.median(revs):.0f}, 90th pct={np.percentile(revs, 90):.0f}')
