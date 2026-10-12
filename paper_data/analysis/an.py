import pandas as pd, numpy as np, statsmodels.api as sm, json, re, warnings
from scipy import stats, optimize
warnings.filterwarnings('ignore')
D='x/data/'
w=pd.read_csv(D+'weekly.csv',parse_dates=['week']);r=pd.read_csv(D+'releases.csv',parse_dates=['published_at'])
def dl(b,se):
    b=np.array(b);se=np.array(se);wi=1/se**2;m=(wi*b).sum()/wi.sum();Q=(wi*(b-m)**2).sum();k=len(b)
    t2=max(0,(Q-(k-1))/(wi.sum()-(wi**2).sum()/wi.sum()));ws=1/(se**2+t2);mu=(ws*b).sum()/ws.sum();s=ws.sum()**-.5
    return mu,s,mu-1.96*s,mu+1.96*s,t2
out={}
# ---- (1) error signature: Poisson QMLE + NB
rows=[]
for repo,g in w.groupby('repo'):
    g=g[g.issues>0].copy();g['t']=np.arange(len(g))/52.
    X=sm.add_constant(g[['age','t']]);y=g.bugs
    p=sm.GLM(y,X,family=sm.families.Poisson(),offset=np.log(g.issues)).fit(cov_type='HC1')
    disp=p.pearson_chi2/p.df_resid
    try:
        nb=sm.NegativeBinomial(y,X,offset=np.log(g.issues)).fit(disp=0,maxiter=200)
        nb_b,nb_se,alpha=nb.params['age'],nb.bse['age'],nb.params['alpha']
    except Exception as e: nb_b=nb_se=alpha=np.nan
    rows.append(dict(repo=repo,n=len(g),pois_b=p.params['age'],pois_se=p.bse['age'],disp=disp,nb_b=nb_b,nb_se=nb_se,alpha=alpha))
E1=pd.DataFrame(rows);E1.to_csv('e1.csv',index=False)
ok=E1.dropna()
out['pois_pool']=dl(E1.pois_b,E1.pois_se);out['nb_pool']=dl(ok.nb_b,ok.nb_se)
out['disp_median']=E1.disp.median();out['disp_range']=(E1.disp.min(),E1.disp.max());out['nb_k']=len(ok)
out['pois_pos']=int((E1.pois_b>0).sum());out['pois_sig_pos']=int((E1.pois_b/E1.pois_se>1.96).sum())
# ---- hazard prep
w=w.sort_values(['repo','week']).reset_index(drop=True)
w['a']=w.groupby('repo').age.shift(1)+1
h=w.dropna(subset=['a']).copy();h['a']=h.a.clip(upper=8)
# hot-fix classification from tags
def ver(t):
    m=re.search(r'(\d+)\.(\d+)(?:\.(\d+))?',t); return tuple(int(x) if x else 0 for x in m.groups()) if m else None
r=r.sort_values(['repo','published_at']).reset_index(drop=True)
r['v']=r.tag.map(ver);hf=[]
for repo,g in r.groupby('repo'):
    prev=None
    for i,row in g.iterrows():
        f=False
        if prev is not None and row.v and prev[0]:
            gap=(row.published_at-prev[1]).days
            f= gap<=7 and row.v[:2]==prev[0][:2] and row.v[2]>prev[0][2]
        hf.append((i,f));prev=(row.v,row.published_at)
r['hotfix']=pd.Series(dict(hf)).reindex(r.index).fillna(False)
out['hotfix_share']=float(r.hotfix.mean());out['hf_share_by_repo']=r.groupby('repo').hotfix.mean().round(3).to_dict()
r['week']=r.published_at.dt.tz_localize(None).dt.to_period('W-SUN').dt.start_time
reg=r[~r.hotfix].groupby(['repo','week']).size().rename('reg_rel');hot=r[r.hotfix].groupby(['repo','week']).size().rename('hot_rel')
h=h.merge(reg.reset_index(),on=['repo','week'],how='left').merge(hot.reset_index(),on=['repo','week'],how='left')
h['reg']=(h.reg_rel.fillna(0)>0).astype(int);h['hot']=(h.hot_rel.fillna(0)>0).astype(int)
def slopes(df,ycol,cond=None):
    res=[]
    for repo,g in df.groupby('repo'):
        if cond is not None: g=g[cond(g)]
        if g[ycol].sum()<3 or g[ycol].sum()==len(g): continue
        try:
            m=sm.Logit(g[ycol],sm.add_constant(g[['a']])).fit(disp=0,cov_type='HC0')
            res.append((repo,m.params['a'],m.bse['a']))
        except Exception: pass
    return pd.DataFrame(res,columns=['repo','b','se'])
S={}
S['all']=slopes(h,'release');S['regular_only']=slopes(h,'reg');S['hotfix_only']=slopes(h,'hot')
S['regular_a>=2']=slopes(h,'reg',lambda g:g.a>=2)
for k,v in S.items():
    v=v[(v.se>0)&v.se.notna()];out['haz_'+k]=dict(dl=dl(v.b,v.se),k=len(v),pos=int((v.b>0).sum()),sigpos=int((v.b/v.se>1.96).sum()),signeg=int((v.b/v.se<-1.96).sum()))
# hazard by age (pooled raw)
out['haz_by_age_all']=h.groupby(h.a.astype(int)).release.mean().round(3).to_dict()
out['haz_by_age_regular']=h.groupby(h.a.astype(int)).reg.mean().round(3).to_dict()
out['haz_by_age_hotfix']=h.groupby(h.a.astype(int)).hot.mean().round(3).to_dict()
# ---- (ii) random-intercept discrete-time logit (Gauss-Hermite)
gh_x,gh_w=np.polynomial.hermite.hermgauss(30)
def frailty(df,ycol):
    gs=[(g[ycol].values,g.a.values.astype(float)) for _,g in df.groupby('repo')]
    def nll(p):
        b0,b1,ls=p;s=np.exp(ls);tot=0
        for y,a in gs:
            eta=b0+b1*a[:,None]+np.sqrt(2)*s*gh_x[None,:]
            ll=(y[:,None]*eta-np.logaddexp(0,eta)).sum(0)
            tot+=np.log((gh_w*np.exp(ll-ll.max())).sum()/np.sqrt(np.pi))+ll.max()
        return -tot
    f=optimize.minimize(nll,[-1,0,0],method='BFGS');H=f.hess_inv
    return dict(b1=f.x[1],se=float(np.sqrt(H[1,1])),sigma=float(np.exp(f.x[2])),n=int(sum(len(y) for y,_ in gs)))
out['frailty_all']=frailty(h,'release');out['frailty_regular']=frailty(h,'reg')
out['frailty_all_a>=2']=frailty(h[h.a>=2],'release');out['frailty_regular_a>=2']=frailty(h[h.a>=2],'reg')
# fixed-effects pooled (no frailty) for comparison
for k in ['release','reg']:
    m=sm.Logit(h[k],sm.add_constant(h[['a']])).fit(disp=0,cov_type='cluster',cov_kwds={'groups':pd.factorize(h.repo)[0]});out['pooled_logit_'+k]=(m.params['a'],m.bse['a'])
# ---- (iii) CV of intervals (days) per repo
iv=r.groupby('repo').published_at.apply(lambda s:s.diff().dt.total_seconds().div(86400).dropna())
cv=iv.groupby('repo').agg(lambda s:s.std()/s.mean());mean_iv=iv.groupby('repo').mean()
ivr=r[~r.hotfix].groupby('repo').published_at.apply(lambda s:s.diff().dt.total_seconds().div(86400).dropna())
cvr=ivr.groupby('repo').agg(lambda s:s.std()/s.mean())
C=pd.DataFrame(dict(n_rel=r.groupby('repo').size(),mean_days=mean_iv,cv=cv,cv_nohotfix=cvr,hotfix_share=r.groupby('repo').hotfix.mean()));C.to_csv('cv.csv')
out['cv_summary']=dict(median=float(cv.median()),min=float(cv.min()),max=float(cv.max()),median_nohf=float(cvr.median()),n_gt1=int((cv>1).sum()))
json.dump(out,open('out.json','w'),indent=1,default=str)
print(json.dumps(out,indent=1,default=str));print(E1.round(3).to_string());print(C.round(2).to_string())
