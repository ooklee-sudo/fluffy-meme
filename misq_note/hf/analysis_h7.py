import numpy as np, pandas as pd, json
from scipy import stats
rng=np.random.default_rng(20261014)
T=pd.read_csv('raw5m_duka/ticks_WTI.csv.gz'); tep=T.ep.values; mid=T.mid.values
def P(s):
    i=np.searchsorted(tep,s,side='right')-1
    if i<0 or s-tep[i]>600: return np.nan
    return mid[i]
H=pd.read_csv('human_labels_191.csv',dtype={'id':str}); a=pd.read_csv('raw/truth_archive.csv',dtype={'id':str}); a['ep']=pd.to_datetime(a.created_at,utc=True,format='ISO8601').map(lambda x:x.timestamp())
H=H.merge(a[['id','ep']],on='id').sort_values('ep').reset_index(drop=True)
def build(label_col):
    d=H.copy(); d['lab']=d[label_col]; d['gap']=d.ep.diff().fillna(1e9); d['keep']=d.gap>=3*3600
    k=d[d.keep&d.lab.isin(['ESC','DEESC'])].copy(); k['sgn']=np.where(k.lab=='ESC',1,-1)
    k['p0']=k.ep.map(P); k['p30']=(k.ep+1800).map(P); k['m30']=(k.ep-1800).map(P); k['p5']=(k.ep+300).map(P)
    k['post30']=k.sgn*100*np.log(k.p30/k.p0); k['pre30']=k.sgn*100*np.log(k.p0/k.m30); k['post5']=k.sgn*100*np.log(k.p5/k.p0)
    k['week']=pd.to_datetime(k.ep,unit='s',utc=True).dt.isocalendar().week.values
    return d,k
def bb(x,wk,B=10000):
    ws=np.unique(wk); g={w:x[wk==w] for w in ws}; o=[np.concatenate([g[w] for w in rng.choice(ws,len(ws))]).mean() for _ in range(B)]; return [float(np.percentile(o,2.5)),float(np.percentile(o,97.5))]
R={}
for name,col in (('human','final'),('model1','model1')):
    d,k=build(col); R[name]=dict(n_posts=len(d),kept_by_filter=int(d.keep.sum()),signal_after_filter=dict(k.lab.value_counts()),window_covered={c:int(k[k.lab==c].post30.notna().sum()) for c in ('DEESC','ESC')})
    for c in ('DEESC','ESC'):
        s=k[(k.lab==c)&k.post30.notna()]; o={'n':int(len(s))}
        if len(s)>=6:
            both=s[['post30','pre30']].dropna()
            o.update(mean5=float(s.post5.mean()),mean30=float(s.post30.mean()),median30=float(s.post30.median()),wilcoxon_post30_gt0=float(stats.wilcoxon(s.post30,alternative='greater').pvalue),week_block_CI=bb(s.post30.values,s.week.values),
                     mean_pre30=float(s.pre30.mean()),n_paired=int(len(both)),paired_diff=float((both.post30-both.pre30).mean()),wilcoxon_post_gt_pre=float(stats.wilcoxon(both.post30-both.pre30,alternative='greater').pvalue))
        R[name][c]=o
R['primary_criterion_met_n_DEESC_ge_20']=bool(R['human']['DEESC'].get('n',0)>=20)
json.dump(R,open('results_h7.json','w'),indent=1,default=float); print(json.dumps(R,indent=1,default=float))
