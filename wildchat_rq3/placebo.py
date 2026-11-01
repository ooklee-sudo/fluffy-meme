import os
DATA=os.environ.get('DATA','/tmp/wc')
# Placebo: snapshot changes with NO cutoff change (all GPT-3.5 snapshots = 2021-09).
# If same-size "effects" appear here, the GPT-4 DiD is not evidence about cutoff drift.
import pandas as pd, numpy as np, statsmodels.formula.api as smf, warnings; warnings.filterwarnings('ignore')
m=pd.read_parquet(DATA+'/design_sample.parquet')           # overlap-week sample from design.py
a=pd.read_parquet(DATA+'/all.parquet')
a['wk']=a.ts.dt.tz_localize(None).dt.to_period('W').dt.start_time.dt.strftime('%Y-%m-%d')
a=a.sample(frac=1,random_state=0); a['r']=a.groupby(['wk','model','fp80']).cumcount(); a=a[(a.r<5)&(a.n_later>0)].copy()
a['y1']=(a.corr1>0).astype(int); a['y2']=(a.corr2>0).astype(int); a['lfp']=np.log1p(a.fp_len); a['code']=a.code.astype(int)
print('weeks per model with both snapshots of 3.5 present:')
p=a[a.model.str.startswith('gpt-3.5')].groupby(['wk','model']).size().unstack(fill_value=0); print(p[(p>0).sum(axis=1)>1].to_string())
s=a[a.model.str.startswith('gpt-3.5')].copy(); grp=pd.factorize(s.wk)[0]
for y in ['y1','y2']:
    r=smf.ols(f"{y} ~ C(model,Treatment('gpt-3.5-turbo-0301')) + code + lfp + n_user",s).fit(cov_type='cluster',cov_kwds={'groups':grp})
    print(f"\n{y}: GPT-3.5 snapshot differences, same cutoff, no week FE (calendar-confounded by design), cluster by week")
    for k in r.params.index:
        if 'C(model' in k:
            c=r.conf_int().loc[k]; print(f"  {k.split('[T.')[1][:-1]} vs 0301: {100*r.params[k]:+.2f} pp [{100*c[0]:+.2f},{100*c[1]:+.2f}] p={r.pvalues[k]:.3f}")
