"""Analysis for prereg/code_review_freetext_prereg.md (item bootstrap over PRs, 2,000 resamples)."""
import numpy as np, pandas as pd, statsmodels.formula.api as smf, statsmodels.api as sm
d = pd.read_pickle('/home/user/data/code_freetext.pkl'); rng = np.random.default_rng(0); NB = 2000
print('parsed share by model:', d.groupby('model').approve.apply(lambda x: x.notna().mean()).round(3).to_dict())
d = d[d.approve.notna()].copy(); d['approve'] = d.approve.astype(float)
def rates(g):
    prs = np.sort(g.pr.unique()); idx = {p: i for i, p in enumerate(prs)}; S, N = {}, {}
    for c, gc in g.groupby('cond'):
        s = np.zeros(len(prs)); n = np.zeros(len(prs)); agg = gc.groupby('pr').approve.agg(['sum', 'count'])
        for p, r in agg.iterrows(): s[idx[p]] = r['sum']; n[idx[p]] = r['count']
        S[c], N[c] = s, n
    B = rng.integers(0, len(prs), size=(NB, len(prs)))
    point = {c: S[c].sum() / N[c].sum() for c in S}; boot = {c: S[c][B].sum(1) / np.maximum(N[c][B].sum(1), 1) for c in S}
    return point, boot
ci = lambda x: np.percentile(x, [2.5, 97.5])
print('\nApproval rates by condition (all PRs) and tests')
rows = []
for scope, sub in [('all', d), ('clean', d[~d.defective]), ('defective', d[d.defective])]:
    for m, g in sub.groupby('model'):
        P, Bt = rates(g)
        inter = P['DIRECT'] - P['BUGFIRST']; ilo, ihi = ci(Bt['DIRECT'] - Bt['BUGFIRST'])
        lo_b = np.minimum(Bt['CI_PASS'], Bt['CI_FAIL']); hi_b = np.maximum(Bt['CI_PASS'], Bt['CI_FAIL'])
        below = ci(Bt['CI_UNKNOWN'] - lo_b)[1] < 0; above = ci(Bt['CI_UNKNOWN'] - hi_b)[0] > 0
        rows.append(dict(scope=scope, model=m, **{c: round(P[c], 3) for c in ['DIRECT', 'BUGFIRST', 'CI_PASS', 'CI_FAIL', 'CI_UNKNOWN']},
                         interference=round(inter, 3), interf_CI=f'[{ilo:+.3f},{ihi:+.3f}]', interf_sig=bool(ilo > 0 or ihi < 0),
                         STP_violation='below' if below else 'above' if above else 'none'))
R = pd.DataFrame(rows); pd.set_option('display.width', 250); pd.set_option('display.max_columns', 30); print(R.to_string(index=False))
det = d[d.defective].groupby(['model', 'cond']).names_buggy_fn.mean().unstack().round(3)
print('\nShare of reviews of defective PRs that name the defective function:'); print(det)
print('\nMean review length (characters):', d.groupby('model').review_chars.mean().round(0).to_dict())
# elicitation-variance decomposition over non-informative elicitations (DIRECT, BUGFIRST, CI_UNKNOWN)
cell = d[d.cond.isin(['DIRECT', 'BUGFIRST', 'CI_UNKNOWN'])].groupby(['pr', 'model', 'cond']).approve.mean().reset_index()
an = sm.stats.anova_lm(smf.ols('approve ~ C(pr) + C(model) * C(cond)', cell).fit(), typ=2); share = (an.sum_sq / an.sum_sq.sum()).round(3)
print('\nVariance shares (non-informative elicitations):', share.to_dict())
R.to_csv('/home/user/fluffy-meme/arena-strategic/results/code_freetext_summary.csv', index=False)
