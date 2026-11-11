"""Variance decomposition of approval verdicts into model, elicitation, and model x elicitation components
(Study 2 data: every condition ends in the same approval question). Elicitation configurations = E1 contexts
(passed / failed / unknown) and E2 (direct / after bug question), crossed with the two label mappings."""
import numpy as np, pandas as pd, statsmodels.formula.api as smf
d = pd.read_pickle('/home/user/data/code_quantum.pkl')
a = d[d.exp.isin(['E1', 'E2'])].copy()
a['elic'] = np.where(a.exp == 'E1', 'ci_' + a.cond.astype(str), 'q_' + a.cond.astype(str)) + '_' + a['map'].astype(str)
# only configurations that carry no outcome information about the code (exclude CI passed/failed, which are informative)
noninf = a[a.elic.str.startswith(('q_direct', 'q_indirect', 'ci_U'))].copy()
def decompose(df, label):
    # cell means: program x model x elicitation; then two-way decomposition of the model x elicitation table
    cell = df.groupby(['item', 'model', 'elic']).approve.mean().reset_index()
    tot = cell.approve.var(ddof=0)
    m = smf.ols('approve ~ C(item) + C(model) * C(elic)', cell).fit()
    import statsmodels.api as sm
    an = sm.stats.anova_lm(m, typ=2); ss = an['sum_sq']; share = (ss / ss.sum()).round(3)
    print(f'\n{label}: share of variance in program-level approval rates (type II sums of squares)')
    for k in ['C(item)', 'C(model)', 'C(elic)', 'C(model):C(elic)', 'Residual']: print(f'  {k:20s} {share.get(k, float("nan")):.3f}')
    # elicitation range per model: max - min approval across elicitation configs
    rng = cell.groupby(['model', 'elic']).approve.mean().unstack()
    print('  approval range across elicitation configurations, by model:', (rng.max(1) - rng.min(1)).round(3).to_dict())
    print('  approval range across models, averaged over configurations:', round(float((rng.max(0) - rng.min(0)).mean()), 3))
decompose(noninf, 'Non-informative elicitations (direct, after bug question, CI unknown) x label mapping')
decompose(a, 'All elicitations including CI passed / failed')
