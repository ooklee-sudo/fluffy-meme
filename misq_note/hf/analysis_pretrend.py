import numpy as np, pandas as pd, json, statsmodels.api as sm
rng=np.random.default_rng(20261014)
o=pd.read_csv('post_reactions_oil_coded.csv'); o['t']=pd.to_datetime(o.t,utc=True,format='ISO8601'); o['ep']=o.t.map(lambda x:int(x.timestamp()))
b=pd.read_csv('raw2y/CL_1h.csv').sort_values('t').reset_index(drop=True); bt=b.t.values; op=b.open.values; cl=b.close.values
WAR=int(pd.Timestamp('2026-03-02',tz='UTC').timestamp())
sig=o[o.cls.isin(['ESC','DEESC'])]; allp=o.ep.values
def prior(k,h): return 100*np.log(op[k]/cl[k-h]) if k-h>=0 else np.nan
def fwd(k): return 100*np.log(cl[k+1]/op[k]) if k+1<len(b) else np.nan
res={}
def null_fit(h):
    X=[];Y=[]
    for j in range(h,len(b)-1):
        if bt[j]<WAR: continue
        if np.min(np.abs(allp-bt[j]))<=7200+1800: continue
        X.append(prior(j,h)); Y.append(fwd(j))
    X=np.array(X);Y=np.array(Y);m=~(np.isnan(X)|np.isnan(Y)); X,Y=X[m],Y[m]
    f=sm.OLS(Y,sm.add_constant(X)).fit(cov_type='HC1'); return f,len(X)
rows=[]
for r in sig.itertuples():
    k=np.searchsorted(bt,r.ep,side='right')-1
    if k<12 or k+1>=len(b) or r.ep-bt[k]>3600 or pd.isna(r.oil): continue
    rows.append(dict(cls=r.cls,ep=r.ep,r=r.oil,sgn=1 if r.cls=='ESC' else -1,**{f'p{h}':prior(k,h) for h in (2,6,12)}))
D=pd.DataFrame(rows); D=D[D.ep>=WAR]; res['n']=D.groupby('cls').size().to_dict()
extreme=[int(pd.Timestamp('2026-03-23 11:23:40',tz='UTC').timestamp()),int(pd.Timestamp('2026-04-07 22:32:26',tz='UTC').timestamp())]
def boot_mean(x):
    bm=np.array([rng.choice(x,len(x)).mean() for _ in range(20000)]); return float(x.mean()),[float(np.percentile(bm,2.5)),float(np.percentile(bm,97.5))],float((bm<=0).mean())
for h in (6,2,12):
    f,nn=null_fit(h); c,d=f.params; res[f'null_fit_h{h}']=dict(n_bars=nn,c=float(c),d=float(d),d_se=float(f.bse[1]),d_p=float(f.pvalues[1]))
    for cl_ in ('DEESC','ESC'):
        s=D[D.cls==cl_]; a=s.r-(c+d*s[f'p{h}']); e=(s.sgn*a).values; raw=(s.sgn*s.r).values
        m,ci,p=boot_mean(e); res[f'h{h}_{cl_}']=dict(n=len(s),raw_dir_mean=float(raw.mean()),abn_dir_mean=m,abn_CI95=ci,boot_p_onesided=p)
        if h==6 and cl_=='DEESC':
            s2=s[~s.ep.isin(extreme)]; a2=s2.r-(c+d*s2.p6); e2=(s2.sgn*a2).values; m2,ci2,p2=boot_mean(e2); res['h6_DEESC_excl_extremes']=dict(n=len(s2),raw_dir_mean=float((s2.sgn*s2.r).mean()),abn_dir_mean=m2,abn_CI95=ci2,boot_p_onesided=p2)
    if h==6:
        for cl_ in ('DEESC','ESC'):
            s=D[D.cls==cl_]; y=(s.sgn*s.r).values; x=(s.sgn*s.p6).values; f2=sm.OLS(y,sm.add_constant(x)).fit(cov_type='HC1')
            res[f'S2_{cl_}']=dict(alpha=float(f2.params[0]),alpha_se=float(f2.bse[0]),alpha_p=float(f2.pvalues[0]),beta=float(f2.params[1]),beta_se=float(f2.bse[1]),beta_p=float(f2.pvalues[1]))
json.dump(res,open('results_pretrend.json','w'),indent=1); print(json.dumps(res,indent=1))
