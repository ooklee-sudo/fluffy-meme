"""Amendment 1 analyses F1-F5 (ANALYSIS_PLAN_V2RELABEL.md)."""
import numpy as np, pandas as pd, json
from scipy import stats
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
rng=np.random.default_rng(20261014)
T=pd.read_csv('raw5m_duka/ticks_WTI.csv.gz'); tep=T.ep.values; mid=T.mid.values
def mk(maxage):
    def P(s):
        i=np.searchsorted(tep,s,side='right')-1
        return np.nan if i<0 or s-tep[i]>maxage else mid[i]
    return P
P=mk(600)
L=pd.read_csv('model_v2_labels_191.csv',dtype={'id':str})
a=pd.read_csv('raw/truth_archive.csv',dtype={'id':str}); a['ep']=pd.to_datetime(a.created_at,utc=True,format='ISO8601').map(lambda x:x.timestamp())
H=L.merge(a[['id','ep']],on='id').sort_values('ep').reset_index(drop=True); H['gap']=H.ep.diff().fillna(1e9); H['day']=pd.to_datetime(H.ep,unit='s',utc=True).dt.date.astype(str)
allep=H.ep.values
R={}
# ---- F1 matched placebo on headline events
def events(col='final',mask=None):
    d=H.copy(); d['lab']=d[col]
    if mask is not None: d.loc[~mask(d),'lab']='OTHER'
    k=d[(d.gap>=3*3600)&d.lab.isin(['ESC','DEESC'])].copy(); k['sgn']=np.where(k.lab=='ESC',1,-1)
    k['p0']=k.ep.map(P); k['p30']=(k.ep+1800).map(P); k['m30']=(k.ep-1800).map(P)
    k['post']=k.sgn*100*np.log(k.p30/k.p0); k['pre']=k.sgn*100*np.log(k.p0/k.m30); return k
K=events(); V=K.dropna(subset=['post','pre'])
R['F1']={}
for c in ('DEESC','ESC'):
    s=V[V.lab==c]; pools=[]
    for r in s.itertuples():
        base=np.floor(r.ep/3600)*3600; wk=pd.Timestamp(r.ep,unit='s',tz='UTC').weekday()>=5; cs=[]
        for dd in (-3,-2,-1,1,2,3):
            for _ in range(60):
                t=base+dd*86400+rng.uniform(0,3600)
                if (pd.Timestamp(t,unit='s',tz='UTC').weekday()>=5)!=wk or np.min(np.abs(allep-t))<=7200: continue
                p0=P(t); p30=P(t+1800); m30=P(t-1800)
                if np.isnan([p0,p30,m30]).any(): continue
                cs.append((r.sgn*100*np.log(p30/p0), r.sgn*100*np.log(p0/m30)))
        cs=np.array(cs)
        if len(cs)>=10:
            k=max(5,int(0.2*len(cs))); idx=np.argsort(np.abs(cs[:,1]-r.pre))[:k]; pools.append(cs[idx,0])
        else: pools.append(np.array([]))
    ok=[i for i,p in enumerate(pools) if len(p)>0]; obs=float(s.post.iloc[ok].mean())
    sims=np.array([np.mean([pools[i][rng.integers(len(pools[i]))] for i in ok]) for _ in range(10000)])
    R['F1'][c]=dict(n=int(len(s)),n_pool=len(ok),observed=obs,placebo_mean=float(sims.mean()),placebo_p95=float(np.percentile(sims,95)),placebo_p99=float(np.percentile(sims,99)),share_ge=float((sims>=obs).mean()),mean_dir_pre_event=float(s.pre.mean()))
# ---- F2 next-open return for signal posts without a window
d=H.copy(); d['lab']=d.final; k2=d[(d.gap>=3*3600)&d.lab.isin(['ESC','DEESC'])].copy(); k2['sgn']=np.where(k2.lab=='ESC',1,-1)
k2['p0']=k2.ep.map(P); k2['p30']=(k2.ep+1800).map(P); nw=k2[k2.p0.isna()|k2.p30.isna()].copy()
def gap_ret(r):
    i=np.searchsorted(tep,r.ep,side='right')-1; j=i+1
    if i<0 or j>=len(tep): return np.nan,np.nan
    # first tick after, but at least 5 minutes of market data after it: take tick j
    hrs=(tep[j]-tep[i])/3600
    return r.sgn*100*np.log(mid[j]/mid[i]),hrs
res=[gap_ret(r) for r in nw.itertuples()]; nw['gapret']=[x[0] for x in res]; nw['gaphrs']=[x[1] for x in res]
R['F2']={c:dict(n=int((nw.lab==c).sum()),mean=float(nw[nw.lab==c].gapret.mean()),median=float(nw[nw.lab==c].gapret.median()),share_positive=float((nw[nw.lab==c].gapret>0).mean()),median_gap_hours=float(nw[nw.lab==c].gaphrs.median())) for c in ('DEESC','ESC')}
# ---- F3 discordant decomposition
E=H[(H.gap>=3*3600)].copy(); E['p0']=E.ep.map(P); E['p30']=(E.ep+1800).map(P); E['r30']=100*np.log(E.p30/E.p0); E=E[E.r30.notna()]
R['F3']={}
for nm,col in (('model1','model1'),('v2_majority','v2_maj')):
    R['F3'][nm]={}
    for c in ('ESC','DEESC'):
        sg=1 if c=='ESC' else -1; ma=E[E[col]==c]
        o=dict(model_class_n=int(len(ma)),agree_human_n=int((ma.final==c).sum()),agree_mean=float((sg*ma[ma.final==c].r30).mean()) if (ma.final==c).any() else None)
        for h in ('DEESC','ESC','MIXED','OTHER'):
            if h==c: continue
            g=ma[ma.final==h]; o[f'human_{h}']=dict(n=int(len(g)),mean_in_model_class_direction=float((sg*g.r30).mean()) if len(g) else None,median=float((sg*g.r30).median()) if len(g) else None)
        R['F3'][nm][c]=o
# ---- F4 two-sided p for robustness variants
def variant(gap_h=3,only_consensus=False,exclude_days=(),win=30):
    d=H.copy(); d['lab']=d.final
    if only_consensus: d.loc[d.source!='consensus','lab']='OTHER'
    k=d[(d.gap>=gap_h*3600 if gap_h>0 else True)&d.lab.isin(['ESC','DEESC'])].copy(); k['sgn']=np.where(k.lab=='ESC',1,-1)
    if exclude_days: k=k[~k.day.isin(exclude_days)]
    w=win*60; k['post']=k.sgn*100*np.log(k.ep.add(w).map(P)/k.ep.map(P)); k['pre']=k.sgn*100*np.log(k.ep.map(P)/k.ep.sub(w).map(P)); return k
def cell(k):
    o={}
    for c in ('DEESC','ESC'):
        s=k[k.lab==c]; v=s.dropna(subset=['post']); b=s.dropna(subset=['post','pre']); x=dict(n=int(len(v)))
        if len(v)>=6:
            x.update(mean=float(v.post.mean()),p_two_post_ne0=float(stats.wilcoxon(v.post).pvalue))
            if len(b)>=6: dd=b.post-b.pre; x.update(paired=float(dd.mean()),p_two_post_vs_pre=float(stats.wilcoxon(dd).pvalue))
        o[c]=x
    return o
R['F4']={'baseline':cell(variant()),'cluster_0h':cell(variant(0)),'cluster_1h':cell(variant(1)),'cluster_2h':cell(variant(2)),'cluster_6h':cell(variant(6)),'consensus_only':cell(variant(only_consensus=True)),'window_5':cell(variant(win=5)),'window_15':cell(variant(win=15)),'window_60':cell(variant(win=60)),'drop_big_days':cell(variant(exclude_days=('2026-03-23','2026-04-07')))}
# ---- F5 forest plot
days=E.day.unique(); byday={x:E[E.day==x] for x in days}
def dcb(df,col,c,B=4000):
    sg=1 if c=='ESC' else -1; out=[]
    for _ in range(B):
        s=pd.concat([byday[x] for x in rng.choice(days,len(days))]); g=s[s[col]==c]
        if len(g): out.append((sg*g.r30).mean())
    return float(np.percentile(out,2.5)),float(np.percentile(out,97.5))
sets=[('Human (final)','final'),('Model 1 (original)','model1'),('v2 majority','v2_maj'),('v2 opus','v2_run1'),('v2 sonnet','v2_run2'),('v2 haiku','v2_run3'),('v2 sonnet repeat','v2_run4')]
fig,ax=plt.subplots(1,2,figsize=(9,3.6),sharey=True); F5={}
for a_,c,t in zip(ax,('DEESC','ESC'),('De-escalation','Escalation')):
    ys=[];
    for i,(nm,col) in enumerate(sets):
        sg=1 if c=='ESC' else -1; g=E[E[col]==c]; m=(sg*g.r30).mean(); lo,hi=dcb(E,col,c); F5[f'{nm}|{c}']=dict(n=int(len(g)),mean=float(m),lo=lo,hi=hi)
        a_.errorbar(m,len(sets)-i,xerr=[[m-lo],[hi-m]],fmt='o',color='#1f4e79' if i==0 else '#7f7f7f',capsize=3); a_.text(hi+0.05,len(sets)-i,f'n={len(g)}',va='center',fontsize=7)
    a_.axvline(0,color='k',lw=.6); a_.set_title(f'{t}: mean directional 30-min return',fontsize=9); a_.set_xlabel('% (day-clustered 95% CI)'); a_.spines[['top','right']].set_visible(False)
ax[0].set_yticks(range(len(sets),0,-1)); ax[0].set_yticklabels([n for n,_ in sets],fontsize=8)
plt.tight_layout(); plt.savefig('figs/fig_forest_labelsets.png',dpi=200)
R['F5']=F5
json.dump(R,open('results_v4b.json','w'),indent=1,default=float)
print(json.dumps({k:R[k] for k in ('F1','F2','F3')},indent=1,default=float)); 
for k,v in R['F4'].items(): print(k,{c:{x:round(y,3) if isinstance(y,float) else y for x,y in o.items()} for c,o in v.items()})
