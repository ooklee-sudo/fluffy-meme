"""Registered verdicts for C2 (AsPredicted #320124). Written and committed before any C2 confirmatory output was analyzed.
Usage: python3 analyze_c2_verdict.py <c2conf_dir> <out_prefix> [bootstrap_reps]
Choices fixed here before analysis: P7a and P7b are evaluated on the no-persona arm (the arm expected to work better); the persona arm is reported as robustness.
Quantities: excess agreement = mean over significant tests (chi-square p < .05 across arms) of (agree - 1/n_arms); pooled = unweighted mean over the five models.
Bootstrap resamples tests (same resampled test set for all models and arms), 1,000 repetitions by default. P7b compares the pooled disattenuated slope in cue-contrast tests with 1.
Verdict rule as registered: 'supported' if the sign holds in >= 4 of 5 models and the pooled CI excludes the null, 'partly supported' if the sign holds in >= 4 of 5 but the CI includes the null, otherwise 'not supported'.
Benjamini-Hochberg across P7a-P7d (two-sided percentile-bootstrap p-values)."""
import sys, io, contextlib
import numpy as np, pandas as pd
OUT, PRE = sys.argv[1], sys.argv[2]; BREP = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
src = open(__file__.replace('analyze_c2_verdict.py', 'analyze_c2.py')).read(); head = src.split('R = pd.DataFrame(rows); out = []')[0]
sys.argv = ['analyze_c2.py', OUT, PRE + '_tmp', '10']; ns = {'__file__': __file__.replace('analyze_c2_verdict.py', 'analyze_c2.py')}; exec(head, ns); R = pd.DataFrame(ns['rows']); CUE = ns['CUE']
for c in ['sxy', 'sxx', 'svv']: R[c] = 0.0
R['sxy'] = R.apply(lambda r: float(np.dot(r.dobs, r.dpred)), axis=1); R['sxx'] = R.apply(lambda r: float(np.dot(r.dobs, r.dobs)), axis=1); R['svv'] = R.apply(lambda r: float(np.sum(r.dvar)), axis=1)
models = sorted(R.model.unique()); arms = ['nopersona', 'persona']; tests = sorted(R.test.unique()); ti = {t: i for i, t in enumerate(tests)}; T = len(tests)
cue = np.array([CUE[t] for t in tests]); print('tests', T, 'cue-contrast', int(cue.sum()), 'non-cue', int((~cue).sum()))
A = {k: np.full((len(models), 2, T), np.nan) for k in ['excess', 'sig', 'sxy', 'sxx', 'svv']}
for r in R.itertuples():
    j, a, t = models.index(r.model), arms.index(r.arm), ti[r.test]
    A['excess'][j, a, t] = r.agree - r.chance; A['sig'][j, a, t] = float(r.sig); A['sxy'][j, a, t] = r.sxy; A['sxx'][j, a, t] = r.sxx; A['svv'][j, a, t] = r.svv
def stats_for(w):
    """w: bootstrap weights per test (counts). Returns dict of arrays over models."""
    out = {}
    for ai, an in enumerate(arms):
        for g, mask in [('all', np.ones(T, bool)), ('cue', cue), ('non', ~cue)]:
            ww = w * mask; sg = np.nan_to_num(A['sig'][:, ai, :]) * ww; ex = np.nan_to_num(A['excess'][:, ai, :])
            out[(an, g, 'excess')] = (sg * ex).sum(axis=1) / np.maximum(sg.sum(axis=1), 1e-9)
            have = ~np.isnan(A['sxx'][:, ai, :]); wh = ww * have
            out[(an, g, 'slope')] = (np.nan_to_num(A['sxy'][:, ai, :]) * wh).sum(axis=1) / np.maximum(((np.nan_to_num(A['sxx'][:, ai, :]) - np.nan_to_num(A['svv'][:, ai, :])) * wh).sum(axis=1), 1e-9)
    return out
def quantities(s):
    return {'P7a cue minus non-cue excess agreement (no-persona)': s[('nopersona', 'cue', 'excess')] - s[('nopersona', 'non', 'excess')],
            'P7b disattenuated slope in cue tests (no-persona), null = 1': s[('nopersona', 'cue', 'slope')],
            'P7c no-persona minus persona excess agreement (all tests)': s[('nopersona', 'all', 'excess')] - s[('persona', 'all', 'excess')],
            'P7d no-persona excess agreement (all tests)': s[('nopersona', 'all', 'excess')],
            'robustness: P7a persona arm': s[('persona', 'cue', 'excess')] - s[('persona', 'non', 'excess')],
            'robustness: P7b persona arm, null = 1': s[('persona', 'cue', 'slope')]}
rng = np.random.default_rng(2026); pt = quantities(stats_for(np.ones(T)))
bs = {k: [] for k in pt}
for _ in range(BREP):
    w = np.bincount(rng.integers(0, T, T), minlength=T).astype(float); q = quantities(stats_for(w))
    for k, v in q.items(): bs[k].append(np.nanmean(v))
rows_out = []
for k in pt:
    null = 1.0 if 'null = 1' in k else 0.0; per = pt[k]; pooled = float(np.nanmean(per)); b = np.array(bs[k]); lo, hi = np.percentile(b, [2.5, 97.5])
    nmod = int(np.sum(per > null)); p = max(2 * min((b <= null).mean(), (b >= null).mean()), 1 / BREP)
    v = 'supported' if (nmod >= 4 and lo > null) else ('partly supported' if nmod >= 4 else 'not supported')
    rows_out.append(dict(test=k, pooled=pooled, ci_lo=lo, ci_hi=hi, models_above_null=f'{nmod}/{len(per)}', p_boot=p, verdict_unadjusted=v, **{f'm_{models[i].split("/")[1]}': per[i] for i in range(len(models))}))
V = pd.DataFrame(rows_out); reg = ~V.test.str.startswith('robustness'); pv = V.loc[reg, 'p_boot'].values; o = np.argsort(pv); q = np.empty(len(pv)); prev = 1.0
for rank, i in reversed(list(enumerate(o, 1))): prev = min(prev, pv[i - 1] * len(pv) / rank); q[i - 1] = prev
V.loc[reg, 'q_BH'] = q; V.to_csv(f'{PRE}_verdicts.csv', index=False)
pd.set_option('display.width', 250, 'display.max_columns', 30, 'display.max_colwidth', 70); print(V.round(3).to_string(index=False))
