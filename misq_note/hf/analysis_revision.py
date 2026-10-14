import numpy as np, pandas as pd, json, statsmodels.api as sm
from scipy import stats
rng=np.random.default_rng(20261014)
b=pd.read_csv('raw2y/CL_1h.csv').sort_values('t').reset_index(drop=True); bt=b.t.values; op=b.open.values; cl=b.close.values
b['et']=pd.to_datetime(b.t,unit='s',utc=True).dt.tz_convert('America/New_York')
bret=100*np.log(cl/op)                       # one-bar return
two=100*np.log(np.r_[cl[1:],np.nan]/op)      # two-hour reaction convention: close[j+1]/open[j]
WAR=int(pd.Timestamp('2026-03-02',tz='UTC').timestamp())
o=pd.read_csv('post_reactions_oil_coded.csv'); o['t']=pd.to_datetime(o.t,utc=True,format='ISO8601'); o['ep']=o.t.map(lambda x:int(x.timestamp()))
allp=o.ep.values
def kidx(ep): return np.searchsorted(bt,ep,side='right')-1
rows=[]
for r in o[o.cls.isin(['ESC','DEESC'])&o.oil.notna()&(o.ep>=WAR)].itertuples():
    k=kidx(r.ep)
    if k<301 or k+13>=len(b) or r.ep-bt[k]>3600: continue
    s=1 if r.cls=='ESC' else -1
    sd=np.nanstd(two[k-300:k])
    d=dict(cls=r.cls,ep=r.ep,k=k,sgn=s,e2=s*r.oil,sd=sd,week=pd.Timestamp(r.ep,unit='s',tz='UTC').isocalendar()[1],
       bm1=s*bret[k-1],b0=s*bret[k],b1=s*bret[k+1],b2=s*bret[k+2])
    for h in (1,2,4,6,12): d[f'c{h}']=s*100*np.log(cl[k+h-1]/op[k])
    d['z']=d['e2']/sd; rows.append(d)
D=pd.DataFrame(rows); R={'n':D.groupby('cls').size().to_dict()}
def blockboot(x,wk,B=20000):
    ws=np.unique(wk); g={w:x[wk==w] for w in ws}; out=[]
    for _ in range(B):
        c=rng.choice(ws,len(ws)); out.append(np.concatenate([g[w] for w in c]).mean())
    return [float(np.percentile(out,2.5)),float(np.percentile(out,97.5))]
for cls in ('DEESC','ESC'):
    s=D[D.cls==cls]; R[cls]={}
    for v in ('bm1','b0','b1','b2','e2'):
        x=s[v].values; R[cls][v]=dict(mean=float(x.mean()),median=float(np.median(x)),wilcoxon_p_greater=float(stats.wilcoxon(x,alternative='greater').pvalue),sign_pos=int((x>0).sum()),n=len(x))
    x=s.e2.values; R[cls]['robust']=dict(trim10=float(stats.trim_mean(x,.1)),trim20=float(stats.trim_mean(x,.2)),sign_p_greater=float(stats.binomtest(int((x>0).sum()),len(x),.5,alternative='greater').pvalue),block_boot_CI=blockboot(x,s.week.values),weeks=int(s.week.nunique()),
        leave_one_week_out=[float(min(x[s.week.values!=w].mean() for w in s.week.unique())),float(max(x[s.week.values!=w].mean() for w in s.week.unique()))])
    for a_,b_ in (('b1','bm1'),('b0','bm1')):
        dd=(s[a_]-s[b_]).values; R[cls][f'paired_{a_}_minus_{b_}']=dict(mean=float(dd.mean()),wilcoxon_p_greater=float(stats.wilcoxon(dd,alternative='greater').pvalue))
    R[cls]['z_mean']=float(s.z.mean()); R[cls]['sd_2h_mean']=float(s.sd.mean())
    R[cls]['CAR']={h:dict(mean=float(s[f'c{h}'].mean()),median=float(s[f'c{h}'].median()),CI=blockboot(s[f'c{h}'].values,s.week.values,5000)) for h in (1,2,4,6,12)}
# R3 pre-war z
p=pd.read_csv('paper_signal_posts.csv',dtype={'id':str}); p=p[(p.topic=='O')&(p.cls=='DEESC')&(p.regime=='low')].drop_duplicates('id'); zl=[]
for r in p.itertuples():
    ep=int(r.ep); k=kidx(ep)
    if k<301 or k+2>=len(b) or ep-bt[k]>3600: continue
    zl.append((-1*two[k])/np.nanstd(two[k-300:k]))
zl=np.array(zl); zh=D[D.cls=='DEESC'].z.values; R['R3']=dict(z_war_DEESC=float(zh.mean()),n_war=len(zh),z_pre_low_DEESC=float(zl.mean()),n_pre=len(zl),diff=float(zh.mean()-zl.mean()))
pool=np.r_[zh,zl]; cnt=0; obs=zh.mean()-zl.mean()
for _ in range(20000):
    q=rng.permutation(pool); cnt+= q[:len(zh)].mean()-q[len(zh):].mean()>=obs
R['R3']['perm_p_greater']=float((cnt+1)/20001)
# R4 timing placebo
dee=D[D.cls=='DEESC']; used=np.zeros(len(b),bool)
for ep in allp: used|=(np.abs(bt-ep)<=7200+1800)
obs=dee.e2.mean(); sims=[]
eth=b.et.dt.hour.values; wk=(b.et.dt.weekday.values>=5)
pool_idx=[]
for r in dee.itertuples():
    k=r.k; cand=np.where((np.abs(bt-bt[k])<=3*86400)&(eth==eth[k])&(wk==wk[k])&(~used)&(np.arange(len(b))>=1)&(np.arange(len(b))<len(b)-2))[0]; pool_idx.append(cand)
cand_ok=[len(c)>0 for c in pool_idx]; R['R4']=dict(events_with_placebo_pool=int(sum(cand_ok)),mean_pool_size=float(np.mean([len(c) for c in pool_idx])))
for _ in range(10000):
    sims.append(np.mean([-two[rng.choice(c)] for c in pool_idx if len(c)>0]))
sims=np.array(sims); R['R4'].update(observed=float(obs),placebo_mean=float(sims.mean()),placebo_sd=float(sims.std()),share_ge_observed=float((sims>=obs).mean()))
# R5 asymmetry
x=D[D.cls=='DEESC'].e2.values; y=D[D.cls=='ESC'].e2.values; diff=x.mean()-y.mean(); pool=np.r_[x,y]; cnt=0
for _ in range(20000):
    q=rng.permutation(pool); cnt+= q[:len(x)].mean()-q[len(x):].mean()>=diff
R['R5']=dict(diff=float(diff),perm_p_greater=float((cnt+1)/20001),mannwhitney_p_greater=float(stats.mannwhitneyu(x,y,alternative='greater').pvalue),MDE_ESC_2h=float(2.8*y.std(ddof=1)/np.sqrt(len(y))))
# R6 filter sensitivity
a=pd.read_csv('raw/truth_archive.csv',dtype={'id':str}); a['t']=pd.to_datetime(a.created_at,utc=True,format='ISO8601'); a['ep']=a.t.map(lambda x:int(x.timestamp()))
pc=pd.DataFrame(json.load(open('posts_coded.json'))).merge(a[['id','ep']],on='id'); pc=pc[pc.ep>=WAR].sort_values('ep').reset_index(drop=True)
R['R6']={}
for gap in (0,3,6):
    last=-1e18; keep=[]
    for e in pc.ep:
        keep.append(e-last>=gap*3600); last=e
    kp=pc[keep]; res_=dict(kept=int(len(kp)),DEESC_kept=int((kp.cls=='DEESC').sum()),ESC_kept=int((kp.cls=='ESC').sum())); vals=[]
    for r in kp[kp.cls=='DEESC'].itertuples():
        k=kidx(r.ep)
        if 0<=k<len(b)-2 and r.ep-bt[k]<=3600 and not np.isnan(two[k]): vals.append(-two[k])
    res_['DEESC_with_bars']=len(vals); res_['DEESC_mean_directional']=float(np.mean(vals)) if vals else None; res_['DEESC_median']=float(np.median(vals)) if vals else None
    R['R6'][gap]=res_
# R7 hazard
mask=(bt>=WAR)&(np.arange(len(b))>=7)&(np.arange(len(b))<len(b)-2)
prior6=np.array([100*np.log(op[j]/cl[j-6]) if j>=6 else np.nan for j in range(len(b))]); rth=((b.et.dt.weekday<5)&(b.et.dt.hour*60+b.et.dt.minute>=570)&(b.et.dt.hour<16)).values.astype(float)
for cls in ('DEESC','ESC'):
    y=np.zeros(len(b)); 
    for ep in o[(o.cls==cls)&(o.ep>=WAR)].ep: 
        k=kidx(ep)
        if 0<=k<len(b) and ep-bt[k]<=3600: y[k]=1
    X=np.c_[prior6,np.abs(prior6),rth]; m=mask&~np.isnan(X).any(1)
    f=sm.Logit(y[m],sm.add_constant(X[m])).fit(disp=0,cov_type='HC1')
    from sklearn.metrics import roc_auc_score
    R[f'R7_{cls}']=dict(n_bars=int(m.sum()),n_events=int(y[m].sum()),coef=dict(zip(['const','prior6','abs_prior6','rth'],map(float,f.params))),p=dict(zip(['const','prior6','abs_prior6','rth'],map(float,f.pvalues))),auc=float(roc_auc_score(y[m],f.predict())))
# R8 arrivals by coded class
days=pd.date_range('2026-03-02','2026-10-13',tz='UTC',freq='D'); R['R8']={}
from scipy import optimize
for cls in ('DEESC','ESC'):
    s=pc[pc.cls==cls]; dd=pd.to_datetime(s.ep,unit='s',utc=True).dt.floor('D'); x=dd.value_counts().reindex(days,fill_value=0).sort_index().values; m=x.mean()
    Dx=((x-m)**2).sum()/m; f=lambda lr:-stats.nbinom.logpmf(x,np.exp(lr),np.exp(lr)/(np.exp(lr)+m)).sum(); r=optimize.minimize_scalar(f,bounds=(-5,8),method='bounded')
    lr=2*(-r.fun-stats.poisson.logpmf(x,m).sum()); wk=pd.Series(x,index=days).groupby(days.to_period('W')).transform('sum'); 
    mu_w=wk.values/7.0; pear=((x-mu_w)**2/np.maximum(mu_w,1e-9)).sum()/(len(x)-len(np.unique(wk.index)))
    R['R8'][cls]=dict(total=int(x.sum()),days=len(x),mean=float(m),var=float(x.var(ddof=1)),dispersion_index=float(Dx),chi2_p=float(stats.chi2.sf(Dx,len(x)-1)),NB_size=float(np.exp(r.x)),LR=float(lr),LR_p=float(stats.chi2.sf(lr,1)/2))
json.dump(R,open('results_revision.json','w'),indent=1,default=float); print(json.dumps(R,indent=1,default=float))
