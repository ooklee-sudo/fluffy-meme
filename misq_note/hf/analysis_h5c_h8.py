import numpy as np, pandas as pd, json
from scipy import stats
rng=np.random.default_rng(20261014)
T=pd.read_csv('raw5m_duka/ticks_WTI.csv.gz'); tep=T.ep.values; mid=T.mid.values
def P(s):
    i=np.searchsorted(tep,s,side='right')-1
    if i<0 or s-tep[i]>600: return np.nan
    return mid[i]
def nticks(a,b): return int(np.searchsorted(tep,b,side='left')-np.searchsorted(tep,a,side='left'))
a=pd.read_csv('raw/truth_archive.csv',dtype={'id':str}); a['ep']=pd.to_datetime(a.created_at,utc=True,format='ISO8601').map(lambda x:x.timestamp())
H=pd.read_csv('human_labels_191.csv',dtype={'id':str}).merge(a[['id','ep']],on='id').sort_values('ep').reset_index(drop=True)
allep=H.ep.values
def stats_at(s,sgn):
    p0=P(s); p30=P(s+1800); m60=P(s-3600); m5=P(s-300); m30=P(s-1800)
    if np.isnan([p0,p30,m60]).any(): return None
    return dict(post30=sgn*100*np.log(p30/p0),pre60=sgn*100*np.log(m5/m60) if not np.isnan(m5) else np.nan,pre30=sgn*100*np.log(p0/m30) if not np.isnan(m30) else np.nan,tc=nticks(s-1800,s))
def events(label_col,filt=True):
    d=H.copy(); d['lab']=d[label_col]; d['gap']=d.ep.diff().fillna(1e9); d['keep']=(d.gap>=3*3600) if filt else True
    k=d[d.keep&d.lab.isin(['ESC','DEESC'])].copy(); k['sgn']=np.where(k.lab=='ESC',1,-1); out=[]
    for r in k.itertuples():
        s=stats_at(r.ep,r.sgn)
        if s is not None: out.append(dict(id=r.id,lab=r.lab,ep=r.ep,sgn=r.sgn,**s))
    return pd.DataFrame(out)
def cands(ev,B=40):
    pools=[]
    for r in ev.itertuples():
        base=np.floor(r.ep/3600)*3600; wk=pd.Timestamp(r.ep,unit='s',tz='UTC').weekday()>=5; cs=[]
        for dd in (-3,-2,-1,1,2,3):
            for _ in range(B):
                s=base+dd*86400+rng.uniform(0,3600)
                if (pd.Timestamp(s,unit='s',tz='UTC').weekday()>=5)!=wk: continue
                if np.min(np.abs(allep-s))<=7200: continue
                st=stats_at(s,r.sgn)
                if st is not None: cs.append(st)
        pools.append(cs)
    return pools
def draws(ev,pools,key,n=10000):
    ok=[i for i,p in enumerate(pools) if len(p)>0]; obs=ev[key].iloc[ok].mean() if key!='tc' else None
    sims=[]
    for _ in range(n):
        vals=[pools[i][rng.integers(len(pools[i]))][key] for i in ok]; sims.append(np.nanmean(vals))
    return ok,np.array(sims)
R={}
def run(name,ev):
    pools=cands(ev); R[name]=dict(n_events=len(ev),events_with_pool=int(sum(len(p)>0 for p in pools)),mean_pool=float(np.mean([len(p) for p in pools])))
    for lab in ('DEESC','ESC'):
        idx=[i for i in range(len(ev)) if ev.lab.iloc[i]==lab]; sub=ev.iloc[idx]; sp=[pools[i] for i in idx]
        o=dict(n=len(sub),n_with_pool=int(sum(len(p)>0 for p in sp)))
        ok=[i for i,p in enumerate(sp) if len(p)>0]
        if len(ok)<5: R[name][lab]=o; continue
        for key in ('post30','pre60','pre30'):
            obs=float(np.nanmean(sub[key].iloc[ok])); sims=np.array([np.nanmean([sp[i][rng.integers(len(sp[i]))][key] for i in ok]) for _ in range(10000)])
            o[key]=dict(observed=obs,placebo_mean=float(sims.mean()),placebo_p95=float(np.percentile(sims,95)),share_ge_observed=float((sims>=obs).mean()))
        obs=float(sub.tc.iloc[ok].mean()); sims=np.array([np.mean([sp[i][rng.integers(len(sp[i]))]['tc'] for i in ok]) for _ in range(10000)])
        o['ticks_pre30']=dict(observed=obs,placebo_mean=float(sims.mean()),ratio=float(obs/sims.mean()),share_ge_observed=float((sims>=obs).mean()))
        R[name][lab]=o
evh=events('final'); run('human',evh)
evm=events('model1'); 
K=pd.read_csv('qual/wire_cases_KEY.csv',dtype={'id':str}); evm=evm[evm.id.isin(K.id)]; run('model1_61',evm)
# H8c
W={}
for f in 'ABCD': W.update({k:v['class'] for k,v in json.load(open(f'qual/wire_{f}.json')).items()})
K['src']=K.wid.map(W); m=evh.merge(K[['id','src']],on='id'); R['H8c']=dict(n_overlap=len(m),by_class=m.groupby('src').pre30.agg(['count','mean','median']).round(3).to_dict('index'))
pf=m[m.src=='POST_FIRST'].pre30.dropna(); of=m[m.src=='OTHER_FIRST'].pre30.dropna()
if len(pf)>=3 and len(of)>=3: R['H8c']['wilcoxon_two_sided_p']=float(stats.mannwhitneyu(pf,of,alternative='two-sided').pvalue)
json.dump(R,open('results_h5c_h8.json','w'),indent=1,default=float); print(json.dumps(R,indent=1,default=float))
