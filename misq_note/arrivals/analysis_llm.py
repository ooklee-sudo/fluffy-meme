"""Exploratory test, as fixed in ANALYSIS_PLAN_LLM_RELEASES.md."""
import numpy as np, pandas as pd, json, warnings
import statsmodels.api as sm
from scipy import stats, optimize
warnings.filterwarnings('ignore'); rng=np.random.default_rng(20261014)
D=pd.read_csv('llm/llm_releases.csv'); D=D[D.month.notna()].copy(); D['m']=pd.PeriodIndex(D.month,freq='M')
D['d']=pd.to_datetime(D.day,errors='coerce'); R={'rows':int(len(D)),'day_precision':int(D.d.notna().sum()),'by_year':D.groupby(D.m.dt.year).size().to_dict()}
def monthly(a,b):
    idx=pd.period_range(a,b,freq='M'); y=D.groupby('m').size().reindex(idx,fill_value=0).values.astype(float); t=np.arange(len(y)); t=(t-t.mean())/t.std()
    out={'months':len(y),'total':int(y.sum()),'mean':float(y.mean()),'var':float(y.var(ddof=1))}
    for nm,X in (('lin',np.c_[np.ones(len(y)),t]),('quad',np.c_[np.ones(len(y)),t,t**2])):
        p=sm.GLM(y,X,family=sm.families.Poisson()).fit(); 
        try:
            nb=sm.NegativeBinomial(y,X).fit(disp=0,maxiter=300,method='bfgs'); a=float(nb.params[-1]); llnb=nb.llf; aicnb=nb.aic
        except Exception: a=np.nan; llnb=np.nan; aicnb=np.nan
        pear=float(((y-p.mu)**2/p.mu).sum()/p.df_resid); lr=2*(llnb-p.llf); out[nm]=dict(AIC_pois=float(p.aic),AIC_nb=float(aicnb),alpha=a,pearson_chi2_df=pear,df=int(p.df_resid),p_pearson=float(stats.chi2.sf(pear*p.df_resid,p.df_resid)),LR=float(lr),p_LR=float(0.5*stats.chi2.sf(max(lr,0),1)))
    # profile CI for alpha (quad)
    return out
R['A1']=monthly('2018-06','2026-09'); R['A2']=monthly('2024-01','2026-09')
# A3 weekday
dd=D[D.d.notna()&(D.d>='2023-01-01')].copy(); dd['dow']=dd.d.dt.dayofweek; c=dd.dow.value_counts().reindex(range(7),fill_value=0).values
R['A3']=dict(n=int(len(dd)),counts_mon_to_sun=c.tolist(),chi2=float(stats.chisquare(c).statistic),p=float(stats.chisquare(c).pvalue),weekend_share=float(c[5:].sum()/c.sum()),expected_weekend_share=2/7)
# A4 gaps
g=dd[dd.d>='2024-01-01'].sort_values('d'); days=g.d.values.astype('datetime64[D]'); gap=np.diff(days).astype(int)
def dll(f,x): return np.log(np.maximum(f(x),1e-300)).sum()
res={}
mu=gap.mean(); pgeo=1/(1+mu); res['Geometric']=(dll(lambda x:stats.geom.pmf(x+1,pgeo),gap),1)
def nbnll(p): r,pp=np.exp(p[0]),1/(1+np.exp(p[1])); return -dll(lambda x:stats.nbinom.pmf(x,r,pp),gap)
o=optimize.minimize(nbnll,[0,np.log(max(mu,.1))],method='Nelder-Mead'); res['NegBin']=(-o.fun,2)
def lnnll(p): m,s=p[0],np.exp(p[1]); return -dll(lambda x:stats.norm.cdf((np.log(x+1)-m)/s)-stats.norm.cdf((np.log(np.maximum(x,0)+1e-9)-m)/s) if False else stats.norm.cdf((np.log(x+1)-m)/s)-np.where(x>0,stats.norm.cdf((np.log(x)-m)/s),0),gap)
o2=optimize.minimize(lnnll,[0,0],method='Nelder-Mead'); res['Discrete lognormal']=(-o2.fun,2)
aic={k:2*v[1]-2*v[0] for k,v in res.items()}; best=min(aic.values())
R['A4']=dict(n_gaps=int(len(gap)),mean=float(mu),var=float(gap.var(ddof=1)),cv=float(gap.std(ddof=1)/mu),share_zero_gap=float((gap==0).mean()),dAIC={k:float(v-best) for k,v in aic.items()},nb_params=[float(np.exp(o.x[0])),float(1/(1+np.exp(o.x[1])))])
# A5 per developer
A5={}
for dv,gdf in dd.groupby('developer'):
    if len(gdf)>=10:
        s=gdf.sort_values('d'); gg=np.diff(s.d.values.astype('datetime64[D]')).astype(int); A5[dv]=dict(n=int(len(s)),mean_gap=float(gg.mean()),cv=float(gg.std(ddof=1)/gg.mean()),median_gap=float(np.median(gg)))
R['A5']=A5
# A6 clustering permutation
def share(dates,devs):
    o=np.argsort(dates); d=dates[o]; v=devs[o]; hit=0
    for i in range(len(d)):
        j=i+1; ok=False
        while j<len(d) and (d[j]-d[i])<=14:
            if v[j]!=v[i]: ok=True;break
            j+=1
        hit+=ok
    return hit/len(d)
q=dd[dd.d>='2024-01-01'].copy(); q['dn']=(q.d-pd.Timestamp('2024-01-01')).dt.days.values; q['qtr']=q.d.dt.to_period('Q').astype(str); q['dev']=q.developer.fillna('').values
obs=share(q.dn.values.astype(int),q.dev.values)
def perm(weekday):
    sims=[]
    for _ in range(3000):
        nd=np.empty(len(q),int)
        for qt,idx in q.groupby('qtr').indices.items():
            lo=q.dn.values[idx].min(); 
            per=pd.Period(qt,freq='Q'); a=(per.start_time-pd.Timestamp('2024-01-01')).days; b=(per.end_time.normalize()-pd.Timestamp('2024-01-01')).days
            pool=np.arange(a,b+1)
            if weekday: pool=np.array([x for x in pool if (pd.Timestamp('2024-01-01')+pd.Timedelta(days=int(x))).dayofweek<5])
            nd[idx]=rng.choice(pool,len(idx),replace=len(idx)>len(pool))
        sims.append(share(nd,q.dev.values))
    sims=np.array(sims); return dict(obs=float(obs),perm_mean=float(sims.mean()),p_lower=float((sims<=obs).mean()),p_upper=float((sims>=obs).mean()))
R['A6_all_days']=perm(False); R['A6_weekdays_only']=perm(True)
# Holm over (A1 LR quad, A2 LR quad, A3)
ps=sorted([('A1_LR_quad',R['A1']['quad']['p_LR']),('A2_LR_quad',R['A2']['quad']['p_LR']),('A3_weekday',R['A3']['p'])],key=lambda x:x[1]); run=0; R['holm']={}
for i,(k,p) in enumerate(ps): run=max(run,min(1,(3-i)*p)); R['holm'][k]=dict(p=float(p),p_holm=float(run))
json.dump(R,open('results_llm.json','w'),indent=1,default=float); print(json.dumps(R,indent=1,default=float))
