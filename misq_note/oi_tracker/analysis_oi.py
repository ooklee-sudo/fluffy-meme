import pandas as pd,numpy as np,statsmodels.api as sm,json
d=pd.read_csv('raw/Affinity_-_National_-_Daily.csv',na_values='.',low_memory=False)
d['date']=pd.to_datetime(d[['year','month','day']])
cols=[c for c in d.columns if c.startswith(('spend_acf_q','spend_grf_q'))]
dd=d[d.freq=='d'].set_index('date')[cols].astype(float)
dd['wk']=dd.index.to_period('W-SUN'); g=dd.groupby('wk'); cnt=g.size(); Wd=g.mean()[cnt==7]; Wd.index=Wd.index.end_time.normalize()
ww=d[d.freq=='w'].set_index('date')[cols].astype(float)   # Amendment 1: weekly rows (Sunday-dated) used after 2022-06-05; Sunday date treated as week-ending
W=pd.concat([Wd,ww]).sort_index(); W=W[~W.index.duplicated()]
W['gap_acf']=W.spend_acf_q1-W.spend_acf_q4
W['gap_grf']=W.spend_grf_q1-W.spend_grf_q4
gas=pd.read_csv('raw/GASREGW.csv',parse_dates=['observation_date']).set_index('observation_date').GASREGW
gas.index=gas.index.to_period('W-SUN').end_time.normalize(); gas=gas.groupby(level=0).mean()
W=W.join(np.log(gas).rename('lgas'),how='left')
W=W.loc['2021-07-11':'2024-06-16']; print(W.index.to_series().diff().value_counts().to_dict())
print(W.shape, W.lgas.isna().sum())
res={}
def dist(y,K=3,sub=None,diff=1):
    X=W[[y,'lgas']].copy()
    if sub is not None: X=X.loc[sub:]
    Y=X[y].diff(diff); L=X.lgas.diff(diff)
    if diff==1:
        Z=pd.concat([L.shift(k).rename(f'g{k}') for k in range(K+1)],axis=1)
        df=pd.concat([Y.rename('y'),Z],axis=1).dropna()
        m=sm.OLS(df.y,sm.add_constant(df.drop(columns='y'))).fit(cov_type='HAC',cov_kwds={'maxlags':8})
        gs=[f'g{k}' for k in range(K+1)]
        c=m.params[gs].sum(); se=np.sqrt(m.cov_params().loc[gs,gs].values.sum())
        return dict(beta=float(c),se=float(se),p=float(2*(1-__import__('scipy').stats.norm.cdf(abs(c/se)))),n=int(len(df)))
    else:
        df=pd.DataFrame({'y':X[y].diff(4),'g':X.lgas.diff(4)}).iloc[::4].dropna()
        m=sm.OLS(df.y,sm.add_constant(df.g)).fit(cov_type='HAC',cov_kwds={'maxlags':2})
        return dict(beta=float(m.params.g),se=float(m.bse.g),p=float(m.pvalues.g),n=int(len(df)))
res['G1_primary_gap_acf']=dist('gap_acf')
for y in ['spend_acf_q1','spend_acf_q4','gap_grf']:
    if y in W: res['G1_'+y]=dist(y)
res['chk_lags6']=dist('gap_acf',K=6)
res['chk_4wk']=dist('gap_acf',diff=4)
res['chk_excl2021']=dist('gap_acf',sub='2022-01-09')
# levels descriptive
X=sm.add_constant(pd.DataFrame({'lgas':W.lgas,'t':np.arange(len(W))}))
m=sm.OLS(W.gap_acf,X).fit(cov_type='HAC',cov_kwds={'maxlags':8}); res['chk_levels_desc']=dict(beta=float(m.params.lgas),p=float(m.pvalues.lgas))
# G2
s=W.gap_acf
def D(i): return s.iloc[i+17-8+0:i+17].mean()-s.iloc[i:i+8].mean()  # post window = 8 weeks starting 17 weeks after pre start-... see below
# pre: 2022-01-03..2022-02-27 (8 wks); post: 2022-05-02..2022-06-26 (8 wks): post start = pre start +17 wks
def Dstat(i): return s.iloc[i+17:i+25].mean()-s.iloc[i:i+8].mean()
i0=list(s.index).index(pd.Timestamp('2022-01-09'))
ref=[Dstat(i) for i in range(0,len(s)-25+1)]
shock=Dstat(i0)
res['G2']=dict(D=float(shock),n_ref=len(ref),rank_p_onesided=float(np.mean(np.array(ref)<=shock)),ref_min=float(min(ref)),ref_max=float(max(ref)),ref_sd=float(np.std(ref)))
# descriptive
res['desc']=dict(gap_pre=float(s.iloc[i0:i0+8].mean()),gap_post=float(s.iloc[i0+17:i0+25].mean()),gas_pre=float(np.exp(W.lgas.iloc[i0:i0+8].mean())),gas_post=float(np.exp(W.lgas.iloc[i0+17:i0+25].mean())))
json.dump(res,open('results_oi.json','w'),indent=1); print(json.dumps(res,indent=1))
