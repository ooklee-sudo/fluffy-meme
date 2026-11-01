import pandas as pd, numpy as np, statsmodels.formula.api as smf, warnings; warnings.filterwarnings('ignore')
d=pd.read_parquet('/tmp/wc/all.parquet')
d['wk']=d.ts.dt.tz_localize(None).dt.to_period('W').dt.start_time.dt.strftime('%Y-%m-%d')
d['g4']=d.model.str.startswith('gpt-4').astype(int)
CUT={'gpt-3.5-turbo-0301':'2021-09','gpt-3.5-turbo-0613':'2021-09','gpt-3.5-turbo-0125':'2021-09','gpt-4-0314':'2021-09','gpt-4-1106-preview':'2023-04','gpt-4-0125-preview':'2023-12'}
d['cut']=pd.PeriodIndex(d.model.map(CUT),freq='M')
tm=d.ts.dt.tz_localize(None).dt.to_period('M')
d['gap_m']=(tm-d.cut).apply(lambda x:x.n)
# dedupe: <=5 per week x model x first-80-chars
rng=np.random.default_rng(0); d=d.sample(frac=1,random_state=0)
d['r']=d.groupby(['wk','model','fp80']).cumcount(); dd=d[d.r<5].copy()
print('rows',len(d),'after dedupe',len(dd))
m=dd[dd.n_later>0].copy()
m['y1']=(m.corr1>0).astype(int); m['y2']=(m.corr2>0).astype(int)
m['lfp']=np.log1p(m.fp_len); m['code']=m.code.astype(int); m['tox']=m.toxic.astype(int)
m['mod']=m.model
# weeks with both families
both=m.groupby('wk').g4.agg(lambda s:s.nunique()==2); m=m[m.wk.isin(both[both].index)]
print('overlap weeks',m.wk.nunique(),'multi-turn convs',len(m))
print(m.groupby('model').agg(n=('y1','size'),weeks=('wk','nunique'),gap_med=('gap_m','median'),y1=('y1','mean'),y2=('y2','mean'),code=('code','mean')).round(3).to_string())

m['g4_0314']=(m.model=='gpt-4-0314').astype(int); m['g4_1106']=(m.model=='gpt-4-1106-preview').astype(int); m['g4_0125']=(m.model=='gpt-4-0125-preview').astype(int)
m['cutdiff']=m.model.map({'gpt-4-0314':0,'gpt-4-1106-preview':19,'gpt-4-0125-preview':27}).fillna(0)
print('tox mean',m.tox.mean())
grp=pd.factorize(m.wk)[0]
for y in ['y1','y2']:
    print('\n',y,'LPM, week FE, SE clustered by week; effects in percentage points vs gpt-3.5 same week')
    r=smf.ols(f"{y} ~ g4_0314 + g4_1106 + g4_0125 + code + lfp + n_user + C(wk)",m).fit(cov_type='cluster',cov_kwds={'groups':grp})
    for k in ['g4_0314','g4_1106','g4_0125']:
        c=r.conf_int().loc[k]; print(f"  {k}: {100*r.params[k]:.2f} pp [{100*c[0]:.2f},{100*c[1]:.2f}] p={r.pvalues[k]:.3f}")
    for k in ['g4_1106','g4_0125']:
        t=r.t_test(f"{k} - g4_0314 = 0"); e=float(np.squeeze(t.effect)); se=float(np.squeeze(t.sd))
        print(f"  DiD {k} - g4_0314: {100*e:.2f} pp (se {100*se:.2f}) p={float(np.squeeze(t.pvalue)):.3f}")
    r2=smf.ols(f"{y} ~ g4 + g4:cutdiff + code + lfp + n_user + C(wk)",m).fit(cov_type='cluster',cov_kwds={'groups':grp})
    k='g4:cutdiff'; c=r2.conf_int().loc[k]; print(f"  per month of cutoff advantage: {100*r2.params[k]:.3f} pp [{100*c[0]:.3f},{100*c[1]:.3f}] p={r2.pvalues[k]:.3f}  (H3 predicts < 0)")
m.to_parquet('/tmp/wc/design_sample.parquet')
