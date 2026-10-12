import pandas as pd, numpy as np, statsmodels.api as sm, json, warnings, re
warnings.filterwarnings('ignore')
rng=np.random.default_rng(7)
D='x/data/';B=400
w=pd.read_csv(D+'weekly.csv',parse_dates=['week']).sort_values(['repo','week']).reset_index(drop=True)
r=pd.read_csv(D+'releases.csv',parse_dates=['published_at'])
def dl(b,se):
    b=np.array(b);se=np.array(se);wi=1/se**2;m=(wi*b).sum()/wi.sum();Q=(wi*(b-m)**2).sum();k=len(b)
    t2=max(0,(Q-(k-1))/(wi.sum()-(wi**2).sum()/wi.sum()));ws=1/(se**2+t2);mu=(ws*b).sum()/ws.sum();s=ws.sum()**-.5
    return dict(b=mu,lo=mu-1.96*s,hi=mu+1.96*s,tau2=t2,k=k)
w['a']=w.groupby('repo').age.shift(1)+1
w['t']=w.groupby('repo').cumcount()/52.
w['cyc']=w.groupby('repo').release.cumsum().shift(1).fillna(0)
w.loc[w.groupby('repo').cumcount()==0,'cyc']=0
w['cyc']=w.groupby('repo').cyc.transform(lambda s:s) 
def fit_bug(g,off=True):
    g=g[g.issues>0]
    X=sm.add_constant(pd.DataFrame({'age':g.age.values,'t':g.t.values}),has_constant='add')
    m=sm.GLM(g.bugs.values,X,family=sm.families.Poisson(),offset=np.log(g.issues.values) if off else None).fit()
    return np.asarray(m.params)[1]
def fit_haz(g,col='release'):
    y=g[col].values;
    if y.sum()<3 or y.sum()==len(y): return np.nan
    m=sm.Logit(y,sm.add_constant(g[['a']].values)).fit(disp=0,maxiter=100)
    return np.asarray(m.params)[1]
def boot(g,fn):
    est=fn(g);cy=[c for _,c in g.groupby(g.cyc.values)];vals=[]
    for _ in range(B):
        idx=rng.integers(0,len(cy),len(cy));gg=pd.concat([cy[i] for i in idx])
        try: v=fn(gg)
        except Exception: continue
        if np.isfinite(v): vals.append(v)
    return est,np.std(vals,ddof=1) if len(vals)>30 else np.nan
h=w.dropna(subset=['a']).copy();h['a']=h.a.clip(upper=8)
res={}
spec={'bug':lambda g:fit_bug(g),'bug_nooff':lambda g:fit_bug(g,False),'haz':lambda g:fit_haz(g)}
rows=[]
for repo,g in w.groupby('repo'):
    gh=h[h.repo==repo];gh2=gh[gh.a>=2]
    row=dict(repo=repo,weeks=len(g))
    rl=r[(r.repo==repo)&(r.published_at.dt.tz_localize(None)>=g.week.min())]
    row['releases']=len(rl)
    rw=g.week[g.release==1];row['median_cycle']=float(np.median(np.diff(rw.values).astype('timedelta64[D]').astype(float)/7)) if len(rw)>1 else np.nan
    for name,fn,d in [('bug',spec['bug'],g),('bugno',spec['bug_nooff'],g),('haz',spec['haz'],gh),('haz2',spec['haz'],gh2)]:
        b,se=boot(d,fn);row[name+'_b']=b;row[name+'_se']=se
    rows.append(row);print(repo,flush=True)
T=pd.DataFrame(rows);T.to_csv('table1.csv',index=False)
