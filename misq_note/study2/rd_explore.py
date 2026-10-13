import pandas as pd, numpy as np, statsmodels.api as sm, statsmodels.formula.api as smf, warnings
warnings.filterwarnings("ignore")
d=pd.read_pickle('app.pkl'); d['ym']=d.t.dt.to_period('M')
c=d.groupby('pa').size(); keep=c[c>=100].index; d=d[d.pa.isin(keep)]
g=d.groupby(['pa','ym']).agg(y=('rating','size'),rs=('rating','sum')).reset_index(); g['pa']=pd.factorize(g.pa)[0]
rows=[]
for pa,s in g.groupby('pa'):
    per=pd.period_range(s.ym.min(),'2023-08',freq='M'); s=s.set_index('ym').reindex(per,fill_value=0)
    s['cum']=s.y.cumsum().shift(1); s['crs']=s.rs.cumsum().shift(1); s['avg']=s.crs/s.cum; s['pa']=pa; s['mo']=per.astype(str)
    rows.append(s.reset_index(drop=True))
P=pd.concat(rows); P=P[(P.cum>=30)].copy()
print(len(P),P.pa.nunique())
P['thr']=np.floor(P.avg*4+0.5)/4*0  # placeholder
# thresholds at x.25 and x.75 in [3.25,4.75]
thr=np.array([3.25,3.75,4.25,4.75]); idx=np.abs(P.avg.values[:,None]-thr).argmin(1); P['t0']=thr[idx]; P['run']=P.avg-P.t0; P['above']=(P.run>=0).astype(int)
bw=0.10; Q=P[P.run.abs()<=bw].copy(); Q['ly']=np.log1p(Q.cum)
print('n in bw',len(Q), Q.above.mean())
print(Q.groupby(pd.cut(Q.run,np.linspace(-bw,bw,11))).agg(n=('y','size'),ym=('y','mean')).round(2))
for ctl in ['','+ly']:
    m=smf.glm(f'y ~ above + run + above:run + C(t0) + C(mo){ctl}',Q,family=sm.families.Poisson()).fit(cov_type='cluster',cov_kwds={'groups':pd.factorize(Q.pa)[0]})
    print(ctl,'above',round(m.params['above'],4),'se',round(m.bse['above'],4),'p',round(m.pvalues['above'],4))
