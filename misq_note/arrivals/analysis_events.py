"""Exploratory event-explanation test, as fixed in ANALYSIS_PLAN_EVENTS.md. Deviation: 500 block-bootstrap resamples (plan: 2,000), see RESULTS_EVENTS.md."""
import numpy as np, pandas as pd, json, glob, os, re, warnings, sys
import statsmodels.api as sm
from scipy import stats, optimize
warnings.filterwarnings('ignore')
sys.path.insert(0,'.'); from compare_models import ll_nb
BASE='/home/user/fluffy-meme/misq_note/'; rng=np.random.default_rng(20261014); B=int(os.environ.get('NBOOT',500))
G=pd.DataFrame({os.path.basename(f)[:8]:json.load(open(f)) for f in sorted(glob.glob('gdelt/*.json'))}).T; G.index=pd.to_datetime(G.index,format='%Y%m%d'); G=G.dropna(subset=['N_ALL']).astype(float)
def daily(eps,start,end):
    d=pd.to_datetime(pd.Series(eps),unit='s',utc=True).dt.tz_localize(None).dt.normalize(); idx=pd.date_range(start,end)
    return d.value_counts().reindex(idx,fill_value=0).astype(float)
tw=pd.read_csv(BASE+'twitter/tweets_in_office_parsed.csv.gz'); tw['id']=tw.url.str.extract(r'status/(\d+)')[0]; tw['ep']=tw.id.map(int).map(lambda i:((i>>22)+1288834974657)/1000.0)
tw=tw[~tw.text.fillna('').str.startswith('RT @')]
ts=pd.read_csv(BASE+'hf/raw/truth_archive.csv',dtype={'id':str}); ts['ep']=pd.to_datetime(ts.created_at,utc=True,format='ISO8601').map(lambda x:x.timestamp()); ts['content']=ts.content.fillna('')
ts=ts[~ts.content.str.match(r'^\s*RT:?')]
T1=('2017-01-20','2021-01-08'); T2=('2026-03-01','2026-10-13')
oil=pd.read_csv(BASE+'twitter/frame_oil_iran.csv'); tar=pd.read_csv(BASE+'twitter/frame_tariff.csv')
S={'TW_all':daily(tw.ep,*T1),'TW_oil':daily(oil.ep,*T1),'TW_tariff':daily(tar.ep,*T1),'TS_all':daily(ts.ep,*T2),'TS_iran':daily(ts[ts.content.str.contains('iran',case=False)].ep,*T2)}
PAIRS=[('TW_all','E_WORLD_CONF'),('TW_all','E_RIOT'),('TW_oil','E_IRN'),('TW_tariff','E_USCHN'),('TS_all','E_IRN'),('TS_iran','E_IRN')]
def design(y,E,kind):
    df=pd.DataFrame({'y':y}); df['dow']=df.index.dayofweek
    e=G[E].reindex(df.index); n=G['N_ALL'].reindex(df.index)
    df['e1']=np.log1p(e.shift(1)); df['e27']=np.log1p(e.shift(2).rolling(6).mean()); df['n1']=np.log(n.shift(1)); df['e0']=np.log1p(e)
    df['wk']=((df.index-df.index[0]).days//7)
    return df.dropna()
def X_of(df,cols,wk=False):
    X=pd.get_dummies(df.dow,prefix='d',drop_first=True,dtype=float)
    if wk: X=pd.concat([X,pd.get_dummies(df.wk,prefix='w',drop_first=True,dtype=float)],axis=1)
    for c in cols: X[c]=df[c].values
    return sm.add_constant(X,has_constant='add')
def nbfit(y,X):
    try:
        r=sm.NegativeBinomial(y,X).fit(disp=0,maxiter=200,method='bfgs'); a=float(r.params['alpha']) if 'alpha' in r.params else float(r.params[-1]); return r,a
    except Exception as e: return None,np.nan
def run(name,E):
    y=S[name]; df=design(y,E,None); yy=df.y.values
    r0,a0=nbfit(yy,X_of(df,[])); rE,aE=nbfit(yy,X_of(df,['e1','e27','n1'])); rW,aW=nbfit(yy,X_of(df,[],wk=True)); rE0,aE0=nbfit(yy,X_of(df,['e1','e27','n1','e0']))
    out=dict(n=len(df),mean=float(yy.mean()),var=float(yy.var()),alpha_base=a0,alpha_events=aE,alpha_week=aW,alpha_events_same_day=aE0)
    if r0 is not None and rE is not None:
        lr=2*(rE.llf-fit_ll_restricted(rE,r0,df)); 
    out['R']=1-aE/a0; out['R_week']=1-aW/a0; out['R_same_day']=1-aE0/a0
    # LR test event terms: events model vs baseline with n1 only
    rN,aN=nbfit(yy,X_of(df,['n1'])); 
    if rE is not None and rN is not None:
        lr=2*(rE.llf-rN.llf); out['LR_chi2_2df']=float(lr); out['LR_p']=float(stats.chi2.sf(lr,2))
    out['coef_e1']=float(rE.params['e1']) if rE is not None else None; out['coef_e27']=float(rE.params['e27']) if rE is not None else None
    # moving block bootstrap of R
    blocks=14; n=len(df); rs=[]
    for _ in range(B):
        starts=rng.integers(0,n-blocks,int(np.ceil(n/blocks))); idx=np.concatenate([np.arange(s,s+blocks) for s in starts])[:n]; d=df.iloc[idx].reset_index(drop=True); d['dow']=df.dow.values
        _,b0=nbfit(d.y.values,X_of(d,[])); _,bE=nbfit(d.y.values,X_of(d,['e1','e27','n1']))
        if np.isfinite(b0) and np.isfinite(bE) and b0>0: rs.append(1-bE/b0)
    out['R_ci95']=[float(np.percentile(rs,2.5)),float(np.percentile(rs,97.5))] if len(rs)>50 else None; out['n_boot_ok']=len(rs)
    return out,df
def fit_ll_restricted(*a): return 0
def ingarch_cov(y,Z,nb=True):
    n=len(y); k=Z.shape[1]; m0=y.mean()
    def f(p):
        g=p[:k]; a,b,r=p[k],p[k+1],p[k+2]
        if a+b>=0.999: return 1e12
        base=np.exp(Z@g); mu=np.empty(n); mu[0]=m0
        for t in range(1,n): mu[t]=base[t]+a*y[t-1]+b*mu[t-1]
        mu=np.maximum(mu,1e-6); return -ll_nb(y,mu,r)
    x0=np.r_[np.log(m0*0.3),np.zeros(k-1),0.3,0.4,2.0]; bd=[(-10,10)]*k+[(0,.999),(0,.999),(0.05,500)]
    r=optimize.minimize(f,x0,bounds=bd,method='L-BFGS-B'); return -r.fun,r.x
if __name__=='__main__':
    R={'gdelt_days':int(len(G))}
    for name,E in PAIRS:
        R[f'{name}|{E}'],df=run(name,E)
    # Holm over LR p
    ps=sorted([(k,v['LR_p']) for k,v in R.items() if isinstance(v,dict) and 'LR_p' in v],key=lambda x:x[1]); run_=0
    for i,(k,p) in enumerate(ps): run_=max(run_,min(1,(len(ps)-i)*p)); R[k]['LR_p_holm']=run_
    # INGARCH persistence with and without covariates
    R['ingarch']={}
    for name,E in (('TW_all','E_WORLD_CONF'),('TS_all','E_IRN')):
        df=design(S[name],E,None); y=df.y.values; Z0=np.ones((len(y),1)); Z1=np.c_[np.ones(len(y)),df.e1.values,df.e27.values,df.n1.values]
        l0,p0=ingarch_cov(y,Z0); l1,p1=ingarch_cov(y,Z1)
        R['ingarch'][f'{name}|{E}']=dict(a_plus_b_no_cov=float(p0[1]+p0[2]),a_plus_b_cov=float(p1[4]+p1[5]),ll_no_cov=float(l0),ll_cov=float(l1),coef_cov=[float(x) for x in p1[1:4]])
    # event series themselves: dispersion/self-excitation of E_IRN in the two periods
    R['event_series']={}
    for E,(a,b) in (('E_IRN',T1),('E_IRN',T2),('E_WORLD_CONF',T1),('E_USCHN',T1)):
        x=G[E].reindex(pd.date_range(a,b)).dropna(); R['event_series'][f'{E}|{a}']=dict(n=len(x),mean=float(x.mean()),var=float(x.var()),lag1_autocorr=float(x.autocorr(1)),lag7_autocorr=float(x.autocorr(7)))
    json.dump(R,open('results_events.json','w'),indent=1,default=float); print(json.dumps(R,indent=1,default=float))
