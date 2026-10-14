import re,json,numpy as np,pandas as pd
from scipy import stats,optimize,special
import statsmodels.api as sm
d=pd.read_csv("raw/truth_archive.csv"); d["t"]=pd.to_datetime(d.created_at,utc=True); d=d[(d.t>="2026-03-01")&(d.t<"2026-10-14")].copy()
d["c"]=d.content.fillna("").str.lower()
d=d[~d.c.str.fullmatch(r"\s*rt:?\s*https?://\S+\s*")]
IR=re.compile(r"\biran"); TH=re.compile(r"attack|strik|bomb|destroy|obliterat|annihilat|wipe[sd]? out|blow(n)? up|kill|ultimatum|very hard"); MO=re.compile(r"\bwill\b|\bwould\b|going to|\bif |unless|or else|tonight|\bsoon\b|\bnext\b")
d["iran"]=d.c.apply(lambda s:bool(IR.search(s))); d["S1"]=d.iran&d.c.apply(lambda s:bool(TH.search(s))); d["S2"]=d.S1&d.c.apply(lambda s:bool(MO.search(s)))
print("posts",len(d),"Iran posts",int(d.iran.sum()),"S1",int(d.S1.sum()),"S2",int(d.S2.sum()))
days=pd.date_range("2026-03-01","2026-10-13",tz="UTC",freq="D"); res={"n_posts":len(d),"n_iran":int(d.iran.sum())}
def nb_ll(x,r,mu): return stats.nbinom.logpmf(x,r,r/(r+mu)).sum()
def analyze(flag,lab):
    s=d[d[flag]]; daily=s.groupby(s.t.dt.floor("D")).size().reindex(days,fill_value=0).values
    wk=pd.Series(daily,index=days).resample("W-SUN").sum().values  # week index
    out=dict(total=int(daily.sum()),days=len(daily),mean_daily=float(daily.mean()),var_daily=float(daily.var(ddof=1)))
    for nm,x in[("daily",daily),("weekly",wk[1:-1] if len(wk)>3 else wk)]:
        m=x.mean(); D=((x-m)**2).sum()/m; df=len(x)-1; p=float(stats.chi2.sf(D,df))
        rng=np.random.default_rng(3); sim=np.array([((y-y.mean())**2).sum()/max(y.mean(),1e-9) for y in (rng.poisson(m,(5000,len(x))))]); pb=float(np.mean(sim>=D))
        # NB MLE
        f=lambda lr:-nb_ll(x,np.exp(lr),m); r=optimize.minimize_scalar(f,bounds=(-5,8),method="bounded"); lrstat=2*(-r.fun-stats.poisson.logpmf(x,m).sum())
        out[nm]=dict(mean=float(m),var=float(x.var(ddof=1)),dispersion_index=float(D),df=df,p_chi2=p,p_boot=pb,nb_size=float(np.exp(r.x)),LR=float(lrstat),p_LR=float(0.5*stats.chi2.sf(max(lrstat,0),1)))
    # inter-arrival
    t=s.t.sort_values().values.astype("datetime64[s]").astype(float)/3600
    if len(t)>5:
        ia=np.diff(t); ia=ia[ia>0]; cv=float(ia.std()/ia.mean()); ks=stats.kstest(ia,"expon",args=(0,ia.mean()))
        out["interarrival"]=dict(n=len(ia),mean_hours=float(ia.mean()),median_hours=float(np.median(ia)),cv=cv,ks_p=float(ks.pvalue))
    # clustering
    sr=pd.Series(daily); out["acf"]=[float(sr.autocorr(l)) for l in range(1,8)]
    prev=sr.shift(1).iloc[1:]; cur=sr.iloc[1:]
    out["mean_after_signal_day"]=float(cur[prev>0].mean()); out["mean_after_quiet_day"]=float(cur[prev==0].mean()); out["share_days_with_signal"]=float((sr>0).mean())
    # week fixed effects Poisson GLM
    wkid=pd.Series(np.arange(len(daily))//7).values; X=pd.get_dummies(wkid,dtype=float)
    try:
        g=sm.GLM(daily,X.values,family=sm.families.Poisson()).fit(); out["week_FE_pearson_dispersion"]=float(g.pearson_chi2/g.df_resid)
    except Exception as e: out["week_FE_pearson_dispersion"]=None
    # overlap with events
    EV=pd.to_datetime(["2026-03-06","2026-03-23","2026-04-06","2026-04-07","2026-04-13","2026-04-27","2026-05-26","2026-06-10","2026-06-11","2026-06-17","2026-06-22","2026-07-08","2026-10-05","2026-10-08"]).tz_localize("UTC")
    near=sum(any(abs((x.floor("D")-e).days)<=1 for e in EV) for x in s.t); out["share_signals_within_1day_of_14_events"]=float(near/max(len(s),1))
    out["share_of_all_days_within_1day_of_events"]=float(len(set([(e+pd.Timedelta(days=k)) for e in EV for k in(-1,0,1)]))/len(days))
    out["top_days"]=pd.Series(daily,index=days.strftime("%Y-%m-%d")).sort_values(ascending=False).head(8).to_dict()
    res[lab]=out
analyze("S1","S1"); analyze("S2","S2")
json.dump(res,open("results_poisson.json","w"),indent=1,default=float)
print(json.dumps(res,indent=1,default=float)[:6000])
