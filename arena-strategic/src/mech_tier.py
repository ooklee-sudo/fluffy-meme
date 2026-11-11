import re, numpy as np, pandas as pd, statsmodels.formula.api as smf
exec(open('src/mechanisms.py').read().split("ctrl = ")[0])
ctrl = 'tok_diff + hdr_diff + lst_diff + bold_diff + ref + opp_ref + C(np.minimum(turns,4)) + short_prompt'
fe = 'C(opair) + C(cl50) + C(lang)'
U = S[S.grp.isin(['none', 'unprompted'])].copy(); U['unprompted'] = (U.grp == 'unprompted').astype(int); U['net'] = U.win - U.lose
small = U.model.str.contains(r'gemma|mini|lite|haiku|scout|small|30b|3n|nova', case=False)
U['up_small'] = U.unprompted * small; U['up_large'] = U.unprompted * ~small
m = smf.ols(f'net ~ up_small + up_large + {ctrl} + {fe}', U).fit(cov_type='cluster', cov_kwds={'groups': pd.factorize(U.pair)[0]})
print('small/cheap-tier model discloses: %+.1f (%.1f) n=%d | flagship discloses: %+.1f (%.1f) n=%d' % (100*m.params.up_small, 100*m.bse.up_small, U.up_small.sum(), 100*m.params.up_large, 100*m.bse.up_large, U.up_large.sum()))
print(U[U.unprompted == 1].groupby(small[U.unprompted == 1]).model.value_counts().groupby(level=0).head(6))
