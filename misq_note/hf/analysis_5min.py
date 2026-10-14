import numpy as np, pandas as pd, json
from scipy import stats
rng=np.random.default_rng(20261014)
T=pd.read_csv('raw5m_duka/ticks_WTI.csv.gz'); tep=T.ep.values; mid=T.mid.values
MAXAGE=600
def P(s):
    i=np.searchsorted(tep,s,side='right')-1
    if i<0 or s-tep[i]>MAXAGE: return np.nan
    return mid[i]
o=pd.read_csv('post_reactions_oil_coded.csv'); o['t']=pd.to_datetime(o.t,utc=True,format='ISO8601'); o['ep']=o.t.map(lambda x:x.timestamp())
a=pd.read_csv('raw/truth_archive.csv',dtype={'id':str}); a['t']=pd.to_datetime(a.created_at,utc=True,format='ISO8601'); a['ep']=a.t.map(lambda x:x.timestamp())
K=pd.read_csv('qual/wire_cases_KEY.csv'); K['ep']=pd.to_datetime(K.t,utc=True,format='ISO8601').map(lambda x:x.timestamp())   # the 61 signal posts
K['sgn']=np.where(K.cls=='ESC',1,-1)
W=json.load(open('results_wire.json')) if False else None
cls={}
for f in 'ABCD': cls.update({k:v['class'] for k,v in json.load(open(f'qual/wire_{f}.json')).items()})
K['src']=K.wid.map(cls)
DL=[5,15,30,60,120]
for D in DL:
    K[f'post{D}']=[s*100*np.log(P(e+D*60)/P(e)) for s,e in zip(K.sgn,K.ep)]
    K[f'pre{D}']=[s*100*np.log(P(e)/P(e-D*60)) for s,e in zip(K.sgn,K.ep)]
K['week']=pd.to_datetime(K.ep,unit='s',utc=True).dt.isocalendar().week.values
K['open_at_post']=[not np.isnan(P(e)) for e in K.ep]
R={'n_posts':len(K),'by_class':K.cls.value_counts().to_dict(),'market_open_at_post':int(K.open_at_post.sum())}
def bb(x,wk,B=20000):
    ws=np.unique(wk); g={w:x[wk==w] for w in ws}; out=[np.concatenate([g[w] for w in rng.choice(ws,len(ws))]).mean() for _ in range(B)]; return [float(np.percentile(out,2.5)),float(np.percentile(out,97.5))]
for c in ('DEESC','ESC'):
    s=K[K.cls==c]; R[c]={}
    for D in DL:
        post=s[f'post{D}'].dropna(); pre=s[f'pre{D}'].dropna(); both=s[[f'post{D}',f'pre{D}']].dropna()
        d=dict(n_post=int(len(post)),mean_post=float(post.mean()) if len(post) else None,median_post=float(post.median()) if len(post) else None,
               wilcoxon_p_post_gt0=float(stats.wilcoxon(post,alternative='greater').pvalue) if len(post)>5 else None,
               n_pre=int(len(pre)),mean_pre=float(pre.mean()) if len(pre) else None,
               n_paired=int(len(both)),mean_paired_diff=float((both[f'post{D}']-both[f'pre{D}']).mean()) if len(both) else None,
               wilcoxon_p_post_gt_pre=float(stats.wilcoxon(both[f'post{D}']-both[f'pre{D}'],alternative='greater').pvalue) if len(both)>5 else None)
        if len(post)>5: d['week_block_CI_post']=bb(post.values,s.loc[post.index,'week'].values,5000)
        R[c][D]=d
# H5c placebo (DEESC, 30 min)
coded=pd.concat([pd.DataFrame(json.load(open('posts_coded.json'))),pd.DataFrame(json.load(open('posts_ext_coder1.json')))]).drop_duplicates('id').merge(a[['id','ep']],on='id').ep.values
dee=K[(K.cls=='DEESC')&K.post30.notna()]; obs=dee.post30.mean(); sims=[]
cands=[]
for r in dee.itertuples():
    base=np.floor(r.ep/3600)*3600; wk_ev=pd.Timestamp(r.ep,unit='s',tz='UTC').weekday()>=5; cs=[]
    for dd in (-3,-2,-1,1,2,3):
        for _ in range(60):
            s=base+dd*86400+rng.uniform(0,3600)
            if (pd.Timestamp(s,unit='s',tz='UTC').weekday()>=5)!=wk_ev: continue
            if np.min(np.abs(coded-s))<=7200: continue
            p0=P(s); p1=P(s+1800)
            if np.isnan(p0) or np.isnan(p1): continue
            cs.append(r.sgn*100*np.log(p1/p0))
    cands.append(np.array(cs))
ok=[c for c in cands if len(c)>0]; R['H5c']=dict(events_with_pool=len(ok),mean_pool=float(np.mean([len(c) for c in ok])) if ok else 0,observed=float(obs))
if ok:
    sims=np.array([np.mean([rng.choice(c) for c in ok]) for _ in range(10000)]); R['H5c'].update(placebo_mean=float(sims.mean()),placebo_p95=float(np.percentile(sims,95)),share_ge_observed=float((sims>=obs).mean()))
# validation
Y=pd.read_csv('raw2y/CL_1h.csv'); Y=Y[Y.t>=1772323200]; v=[]
for r in Y.itertuples():
    p0=P(r.t); p1=P(r.t+3600)
    if not(np.isnan(p0) or np.isnan(p1)): v.append((100*np.log(p1/p0),100*np.log(r.close/r.open)))
v=np.array(v); R['validation_hourly']=dict(n=int(len(v)),corr=float(np.corrcoef(v[:,0],v[:,1])[0,1]) if len(v)>10 else None)
# two-hour from bar open on ticks, DEESC
two=[]
for r in K[K.cls=='DEESC'].itertuples():
    bo=np.floor(r.ep/3600)*3600; p0=P(bo); p1=P(bo+7200)
    if not(np.isnan(p0) or np.isnan(p1)): two.append(-100*np.log(p1/p0))
R['two_hour_from_bar_open_DEESC_ticks']=dict(n=len(two),mean=float(np.mean(two)) if two else None)
# heterogeneity by first-source class (post30, DEESC+ESC pooled directional)
R['post30_by_source_class']=K.groupby('src').post30.agg(['count','mean']).round(3).to_dict('index')
R['closed_market_posts']=K[~K.open_at_post][['wid','cls','t']].astype(str).values.tolist()
json.dump(R,open('results_5min.json','w'),indent=1,default=float); print(json.dumps(R,indent=1,default=float))
