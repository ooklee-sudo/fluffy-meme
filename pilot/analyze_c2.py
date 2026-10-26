"""Score twin-predicted headline performance against observed Upworthy clicks.
Usage: python3 analyze_c2.py <c2_dir> <out_prefix> [bootstrap_reps]
Per test: observed CTR per arm; predicted click probability per arm averaged over personas.
 - Winner agreement: predicted best arm == observed best arm, among tests whose arms differ at p < .05 (chi-square across arms).
   Exact binomial CI; chance level is 1/(number of arms) per test, so the primary comparison is agreement vs the test-specific chance rate
   (reported as excess agreement) and vs 0.5 for two-arm tests.
 - Spearman: mean within-test Spearman between predicted and observed log CTR across arms.
 - Calibration slope: pooled slope of predicted log-odds difference on observed log-odds difference over all arm pairs (through the origin);
   slope > 1 means the twin overstates effects. (Clarification: the registered text said 'observed on predicted', which would invert the meaning of > 1.)"""
import sys, json, re
import numpy as np, pandas as pd
from scipy import stats
OUT, PRE = sys.argv[1], sys.argv[2]; B = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
tests = json.load(open(f'{OUT}/tests.json'))
obs = {}
for t, arms in tests.items():
    imp = np.array([a['impressions'] for a in arms], float); clk = np.array([a['clicks'] for a in arms], float); ctr = clk / imp
    if (clk == 0).any(): continue
    tab = np.vstack([clk, imp - clk]); p = stats.chi2_contingency(tab)[1]
    obs[t] = dict(ctr=ctr, lo=np.log(ctr / (1 - ctr)), p=p, n=len(arms))
pred = {}
for l in open(f'{OUT}/raw.jsonl'):
    x = json.loads(l); m = re.search(r'\{.*\}', x['content'] or '', re.S)
    try: j = json.loads(m.group(0))
    except Exception: continue
    n = len(tests[x['test']]); v = np.full(n, np.nan)
    for k, i in enumerate(x['order']):
        try: v[i] = float(j['ABCDEF'[k]])
        except Exception: pass
    if np.isnan(v).any(): continue
    pred.setdefault((x['model'], x['test']), []).append(np.clip(v, 0.5, 99.5) / 100)
rows = []
for (m, t), lst in pred.items():
    if t not in obs: continue
    pm = np.mean(lst, axis=0); lo = np.log(pm / (1 - pm)); o = obs[t]
    best_ok = int(np.argmax(pm) == np.argmax(o['ctr'])); rho = stats.spearmanr(pm, o['ctr'])[0] if o['n'] > 2 else (1.0 if best_ok else -1.0)
    pairs = [(i, j) for i in range(o['n']) for j in range(i + 1, o['n'])]
    rows.append(dict(model=m, test=t, n_arms=o['n'], sig=o['p'] < .05, agree=best_ok, chance=1 / o['n'], rho=rho, n_pred=len(lst),
                     dobs=[o['lo'][i] - o['lo'][j] for i, j in pairs], dpred=[lo[i] - lo[j] for i, j in pairs]))
R = pd.DataFrame(rows); out = []
rng = np.random.default_rng(2026)
for m, g in R.groupby('model'):
    s = g[g.sig]; k = int(s.agree.sum()); n = len(s); lo_, hi_ = stats.beta.ppf([.025, .975], [k, k + 1], [n - k + 1, n - k]) if n else (np.nan, np.nan)
    xs = np.concatenate([np.array(v) for v in g.dobs]); ys = np.concatenate([np.array(v) for v in g.dpred]); slope = (xs * ys).sum() / (xs ** 2).sum()
    sl = []
    for _ in range(B):
        idx = rng.integers(0, len(g), len(g)); xb = np.concatenate([np.array(g.dobs.iloc[i]) for i in idx]); yb = np.concatenate([np.array(g.dpred.iloc[i]) for i in idx]); sl.append((xb * yb).sum() / (xb ** 2).sum())
    out.append(dict(model=m, tests=len(g), sig_tests=n, agreement=k / n if n else np.nan, agr_ci_lo=lo_, agr_ci_hi=hi_, chance_sig=s.chance.mean() if n else np.nan,
                    mean_rho=g.rho.mean(), slope_pred_on_obs=slope, slope_lo=np.percentile(sl, 2.5), slope_hi=np.percentile(sl, 97.5)))
S = pd.DataFrame(out); S.to_csv(f'{PRE}_summary.csv', index=False)
pd.set_option('display.width', 220); print(S.round(3).to_string(index=False))
