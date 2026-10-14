"""Reporting fixes for the human-label headline (ANALYSIS_PLAN_V2RELABEL.md, parts D and E) and event-time figure."""
import numpy as np, pandas as pd, json
from scipy import stats
rng=np.random.default_rng(20261014)
T=pd.read_csv('raw5m_duka/ticks_WTI.csv.gz'); tep=T.ep.values; mid=T.mid.values
def P(s):
    i=np.searchsorted(tep,s,side='right')-1
    return np.nan if i<0 or s-tep[i]>600 else mid[i]
H=pd.read_csv('human_labels_191.csv',dtype={'id':str}); a=pd.read_csv('raw/truth_archive.csv',dtype={'id':str}); a['ep']=pd.to_datetime(a.created_at,utc=True,format='ISO8601').map(lambda x:x.timestamp())
H=H.merge(a[['id','ep']],on='id').sort_values('ep').reset_index(drop=True); H['gap']=H.ep.diff().fillna(1e9); H['day']=pd.to_datetime(H.ep,unit='s',utc=True).dt.date.astype(str)
def events(lab_col='final',mask=None):
    d=H.copy(); d['lab']=d[lab_col]
    if mask is not None: d.loc[~mask(d),'lab']='OTHER'
    k=d[(d.gap>=3*3600)&d.lab.isin(['ESC','DEESC'])].copy(); k['sgn']=np.where(k.lab=='ESC',1,-1)
    k['p0']=k.ep.map(P); k['p30']=(k.ep+1800).map(P); k['post30']=k.sgn*100*np.log(k.p30/k.p0); return k.dropna(subset=['post30'])
def dcb(v,days,B=10000,stat=np.mean):
    ud=np.unique(days); g={u:v[days==u] for u in ud}; o=[stat(np.concatenate([g[u] for u in rng.choice(ud,len(ud))])) for _ in range(B)]; return [float(np.percentile(o,2.5)),float(np.percentile(o,97.5))]
def summ(s):
    v=s.post30.values; o=dict(n=int(len(v)),mean=float(v.mean()),median=float(np.median(v)),p_two=float(stats.wilcoxon(v).pvalue),p_one=float(stats.wilcoxon(v,alternative='greater').pvalue),n_days=int(s.day.nunique()))
    o['mean_ci_day']=dcb(v,s.day.values); o['median_ci_day']=dcb(v,s.day.values,stat=np.median); return o
R={}
k=events()
R['headline']={c:summ(k[k.lab==c]) for c in ('DEESC','ESC')}
# D: adjudication sensitivity
R['adjudication']={}
for name,mask in (('all_final',None),('consensus_only',lambda d:d.source=='consensus'),('adjudicated_only',lambda d:d.source!='consensus')):
    kk=events(mask=mask); R['adjudication'][name]={c:(summ(kk[kk.lab==c]) if (kk.lab==c).sum()>=5 else dict(n=int((kk.lab==c).sum()))) for c in ('DEESC','ESC')}
# E: placebo on the headline sample (post-30 only)
allep=H.ep.values
def pool(ev,B=40):
    out=[]
    for r in ev.itertuples():
        base=np.floor(r.ep/3600)*3600; wk=pd.Timestamp(r.ep,unit='s',tz='UTC').weekday()>=5; cs=[]
        for dd in (-3,-2,-1,1,2,3):
            for _ in range(B):
                s=base+dd*86400+rng.uniform(0,3600)
                if (pd.Timestamp(s,unit='s',tz='UTC').weekday()>=5)!=wk or np.min(np.abs(allep-s))<=7200: continue
                p0=P(s); p30=P(s+1800)
                if not np.isnan([p0,p30]).any(): cs.append(r.sgn*100*np.log(p30/p0))
        out.append(np.array(cs))
    return out
R['placebo_same_sample']={}
for c in ('DEESC','ESC'):
    s=k[k.lab==c]; pl=pool(s); ok=[i for i,p in enumerate(pl) if len(p)>0]; obs=float(s.post30.iloc[ok].mean())
    sims=np.array([np.mean([pl[i][rng.integers(len(pl[i]))] for i in ok]) for _ in range(10000)])
    R['placebo_same_sample'][c]=dict(n=int(len(s)),n_with_pool=len(ok),observed=obs,placebo_mean=float(sims.mean()),placebo_p95=float(np.percentile(sims,95)),placebo_p99=float(np.percentile(sims,99)),share_ge=float((sims>=obs).mean()))
# Figure data: directional path at offsets
offs=np.arange(-60,61,5)
def path(eps,sgns,ref=0):
    p0=np.array([P(e) for e in eps]); M=[]
    for o in offs:
        po=np.array([P(e+o*60) for e in eps]); M.append(sgns*100*np.log(po/p0))
    return np.array(M).T  # events x offsets
fig={}
for c in ('DEESC','ESC'):
    s=k[k.lab==c]; Mx=path(s.ep.values,s.sgn.values); fig[c]=dict(mean=np.nanmean(Mx,0).tolist(),median=np.nanmedian(Mx,0).tolist(),se=(np.nanstd(Mx,0,ddof=1)/np.sqrt((~np.isnan(Mx)).sum(0))).tolist(),n=int(len(s)))
    pl=[]
    for r in s.itertuples():
        base=np.floor(r.ep/3600)*3600; wk=pd.Timestamp(r.ep,unit='s',tz='UTC').weekday()>=5; cs=[]
        for dd in (-3,-2,-1,1,2,3):
            for _ in range(25):
                t=base+dd*86400+rng.uniform(0,3600)
                if (pd.Timestamp(t,unit='s',tz='UTC').weekday()>=5)!=wk or np.min(np.abs(allep-t))<=7200: continue
                if np.isnan(P(t)): continue
                cs.append(t)
        pl.append(cs)
    sims=[]
    for _ in range(1000):
        ts=[x[rng.integers(len(x))] for x in pl if len(x)>0]; sg=s.sgn.values[[i for i,x in enumerate(pl) if len(x)>0]]
        sims.append(np.nanmean(path(np.array(ts),sg),0))
    sims=np.array(sims); fig[c]['placebo_lo']=np.nanpercentile(sims,2.5,axis=0).tolist(); fig[c]['placebo_hi']=np.nanpercentile(sims,97.5,axis=0).tolist(); fig[c]['placebo_mean']=np.nanmean(sims,0).tolist()
R['figure']=dict(offsets=offs.tolist(),**fig)
json.dump(R,open('results_v4_headline.json','w'),indent=1,default=float)
print(json.dumps({k_:R[k_] for k_ in ('headline','adjudication','placebo_same_sample')},indent=1,default=float))
