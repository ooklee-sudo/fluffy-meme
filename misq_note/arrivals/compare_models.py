import numpy as np, pandas as pd, json
from scipy import stats, optimize, special
GH_x,GH_w=np.polynomial.hermite_e.hermegauss(60); GH_w=GH_w/np.sqrt(2*np.pi)
def ll_pois(x,mu): return stats.poisson.logpmf(x,mu).sum()
def ll_nb(x,mu,r): return stats.nbinom.logpmf(x,r,r/(r+mu)).sum()
def ll_pln(x,m,s):
    lam=np.exp(m+s*GH_x)[None,:]; lp=stats.poisson.logpmf(x[:,None],lam)+np.log(GH_w)[None,:]; return special.logsumexp(lp,axis=1).sum()
def fit(f,x0,bounds): 
    r=optimize.minimize(lambda p:-f(p),x0,bounds=bounds,method='L-BFGS-B'); return -r.fun,r.x
def ingarch(x,nb):
    n=len(x); m0=x.mean()
    def f(p):
        w,a,b=p[0],p[1],p[2]; r=p[3] if nb else None
        if a+b>=0.999: return -1e12
        mu=np.empty(n); mu[0]=m0
        for t in range(1,n): mu[t]=w+a*x[t-1]+b*mu[t-1]
        mu=np.maximum(mu,1e-6); return ll_nb(x,mu,r) if nb else ll_pois(x,mu)
    x0=[m0*0.3,0.3,0.4]+([2.0] if nb else []); bd=[(1e-4,None),(0,0.999),(0,0.999)]+([(0.05,500)] if nb else [])
    return fit(f,x0,bd)
def daily_models(x):
    x=np.asarray(x,float); m=x.mean(); out={}
    out['Poisson']=(ll_pois(x,m),1)
    l,p=fit(lambda p:ll_nb(x,m,p[0]),[1.0],[(0.01,500)]); out['NB (Poisson-Gamma)']=(l,2)
    l,p=fit(lambda p:ll_pln(x,p[0],p[1]),[np.log(max(m,.05))-.5,1.0],[(-8,8),(0.05,4)]); out['Poisson-lognormal']=(l,2)
    l,p=ingarch(x,False); out['Poisson INGARCH(1,1)']=(l,3)
    l,p=ingarch(x,True); out['NB INGARCH(1,1)']=(l,4)
    n=len(x); res={}
    for k,(l,q) in out.items(): res[k]=dict(ll=float(l),k=q,AIC=float(2*q-2*l),BIC=float(q*np.log(n)-2*l))
    best=min(res,key=lambda k:res[k]['AIC']); 
    for k in res: res[k]['dAIC']=res[k]['AIC']-res[best]['AIC']
    return res,best
def interarrival_models(ia):
    ia=np.asarray(ia,float); ia=ia[ia>0]; n=len(ia); res={}
    def add(name,ll,q): res[name]=dict(ll=float(ll),k=q,AIC=float(2*q-2*ll))
    add('Exponential',stats.expon.logpdf(ia,0,ia.mean()).sum(),1)
    for name,d,q in (('Gamma',stats.gamma,2),('Weibull',stats.weibull_min,2),('Lognormal',stats.lognorm,2)):
        p=d.fit(ia,floc=0); add(name,d.logpdf(ia,*p).sum(),q)
    xm=ia.min(); a=n/np.log(ia/xm).sum(); add('Pareto (power law)',(np.log(a)+a*np.log(xm)-(a+1)*np.log(ia)).sum(),2)
    best=min(res,key=lambda k:res[k]['AIC'])
    for k in res: res[k]['dAIC']=res[k]['AIC']-res[best]['AIC']
    return res,best,dict(cv=float(ia.std()/ia.mean()),mean_h=float(ia.mean()/3600),median_h=float(np.median(ia)/3600))
def series_daily(ts,start,end):
    days=pd.date_range(start,end,tz='UTC',freq='D'); return ts.dt.floor('D').value_counts().reindex(days,fill_value=0).sort_index().values
SER={}
tw=pd.read_csv('../twitter/tweets_in_office_parsed.csv.gz'); tw['id']=tw.url.str.extract(r'status/(\d+)')[0].map(int); tw['ep']=tw.id.map(lambda i:((i>>22)+1288834974657)/1000.0); tw['text']=tw.text.fillna(''); tw=tw[~tw.text.str.startswith('RT @')].sort_values('ep')
SER['Trump Twitter 2017-21, all original']=(pd.to_datetime(tw.ep,unit='s',utc=True),'2017-01-21','2021-01-07')
for nm,fn in (('Trump Twitter, oil/Iran tweets','../twitter/frame_oil_iran.csv'),('Trump Twitter, tariff/trade/China tweets','../twitter/frame_tariff.csv')):
    f=pd.read_csv(fn,dtype={'id':str}); SER[nm]=(pd.to_datetime(f.ep,unit='s',utc=True),'2017-01-21','2021-01-07')
ts=pd.read_csv('../hf/raw/truth_archive.csv'); ts['t']=pd.to_datetime(ts.created_at,utc=True,format='ISO8601'); ts=ts[(ts.t>='2026-03-01')&(ts.t<'2026-10-14')]; ts['c']=ts.content.fillna(''); ts=ts[~ts.c.str.fullmatch(r'\s*rt:?\s*https?://\S+\s*',case=False)]
SER['Trump Truth Social 2026, all original']=(ts.t,'2026-03-01','2026-10-13')
mk=pd.read_csv('musk_2017_tweets.csv',encoding='latin-1'); mk['t']=pd.to_datetime(mk.Time,utc=True); mo=mk[~mk.Tweet.str.startswith('RT @')]
SER['Musk Twitter 2012-17, original (full span)']=(mo.t,'2012-11-16','2017-09-29')
SER['Musk Twitter 2016-17, original']=(mo[mo.t>='2016-01-01'].t,'2016-01-01','2017-09-29')
R={}
for name,(t,s,e) in SER.items():
    t=t.sort_values(); x=series_daily(t,s,e); dm,best=daily_models(x); ia=np.diff(t.map(lambda z:z.timestamp()).values); im,bi,st=interarrival_models(ia)
    mu=x.mean(); R[name]=dict(n=int(x.sum()),days=len(x),mean=float(mu),var=float(x.var(ddof=1)),daily=dm,daily_best=best,interarrival=im,interarrival_best=bi,interarrival_stats=st)
    print(f"\n{name}: n={int(x.sum())}, days={len(x)}, mean {mu:.2f}, var {x.var(ddof=1):.2f}\n  daily best by AIC: {best}; "+'; '.join(f"{k}: dAIC {v['dAIC']:.0f}" for k,v in dm.items())+f"\n  inter-arrival best: {bi}; "+'; '.join(f"{k}: dAIC {v['dAIC']:.0f}" for k,v in im.items())+f"; CV {st['cv']:.2f}")
json.dump(R,open('results_model_comparison.json','w'),indent=1)
