import numpy as np, pandas as pd, json
from scipy import stats
T=pd.read_csv('raw5m_duka/ticks_WTI.csv.gz'); tep=T.ep.values; mid=T.mid.values; spr=T.spread.values
def mk(maxage):
    def P(s):
        i=np.searchsorted(tep,s,side='right')-1
        return np.nan if i<0 or s-tep[i]>maxage else mid[i]
    return P
H=pd.read_csv('human_labels_191.csv',dtype={'id':str}); a=pd.read_csv('raw/truth_archive.csv',dtype={'id':str}); a['ep']=pd.to_datetime(a.created_at,utc=True,format='ISO8601').map(lambda x:x.timestamp())
H=H.merge(a[['id','ep']],on='id').sort_values('ep').reset_index(drop=True); H['gap']=H.ep.diff().fillna(1e9)
H['day']=pd.to_datetime(H.ep,unit='s',utc=True).dt.date.astype(str)
def cell(k,sgn_col='sgn',win=30,maxage=600):
    P=mk(maxage); out={}
    for c in ('DEESC','ESC'):
        s=k[k.lab==c].copy(); w=win*60
        s['p0']=s.ep.map(P); s['pp']=(s.ep+w).map(P); s['pm']=(s.ep-w).map(P)
        s['post']=s.sgn*100*np.log(s.pp/s.p0); s['pre']=s.sgn*100*np.log(s.p0/s.pm)
        v=s.dropna(subset=['post']); b=v.dropna(subset=['pre']); o=dict(n=int(len(v)),n_paired=int(len(b)))
        if len(v)>=6:
            o.update(mean=float(v.post.mean()),median=float(v.post.median()),p_post_gt0=float(stats.wilcoxon(v.post,alternative='greater').pvalue),trim10=float(stats.trim_mean(v.post,0.1)))
            if len(b)>=6:
                d=b.post-b.pre; o.update(mean_pre=float(b.pre.mean()),paired=float(d.mean()),p_post_gt_pre=float(stats.wilcoxon(d,alternative='greater').pvalue))
        out[c]=o
    return out,k
def sample(gap_h=3,label_col='final',only_consensus=False,exclude_days=()):
    d=H.copy(); d['lab']=d[label_col]
    if only_consensus: d=d[d.source=='consensus']
    keep=(d.gap>=gap_h*3600) if gap_h>0 else np.ones(len(d),bool)
    k=d[keep&d.lab.isin(['ESC','DEESC'])].copy(); k['sgn']=np.where(k.lab=='ESC',1,-1)
    if exclude_days: k=k[~k.day.isin(exclude_days)]
    return k
R={}
R['V0_baseline']=cell(sample())[0]
for g in (0,1,2,6): R[f'V1_cluster_{g}h']=cell(sample(gap_h=g))[0]
R['V2_consensus_only']=cell(sample(only_consensus=True))[0]
for w in (5,15,30,60): R[f'V3_window_{w}min']=cell(sample(),win=w)[0]
for m in (120,300,600): R[f'V4_stale_{m//60}min']=cell(sample(),maxage=m)[0]
R['V5_drop_big_days']=cell(sample(exclude_days=('2026-03-23','2026-04-07')))[0]
# big days present?
k0=sample(); R['V5_events_on_big_days']={d:int(((k0.day==d)).sum()) for d in ('2026-03-23','2026-04-07')}
# leave-one-event-out
P=mk(600)
for c in ('DEESC','ESC'):
    s=k0[k0.lab==c].copy(); s['post']=s.sgn*100*np.log(s.ep.add(1800).map(P)/s.ep.map(P)); v=s.dropna(subset=['post']).post.values
    loo=[np.delete(v,i).mean() for i in range(len(v))]; R.setdefault('V5_leave_one_out',{})[c]=dict(min=float(min(loo)),max=float(max(loo)),full=float(v.mean()),top3_share_of_sum=float(np.sort(v)[-3:].sum()/v.sum()),largest=[float(x) for x in np.sort(v)[-3:]])
# V6 spreads
k=k0.copy(); idx=[np.searchsorted(tep,e,side='right')-1 for e in k.ep]; k['spread']=spr[idx]; k['p0']=k.ep.map(P); k['post_abs']=(k.ep+1800).map(P)-k.p0
R['V6_spread']=dict(median_spread=float(np.nanmedian(k.spread)),median_price=float(np.nanmedian(k.p0)),median_abs_move_30=float(np.nanmedian(np.abs(k.post_abs))),ratio_median_move_to_spread=float(np.nanmedian(np.abs(k.post_abs))/np.nanmedian(k.spread)))
# reconciliation
d=H.copy(); d['lab']=d.final; keep=d.gap>=3*3600; ks=d[keep&d.lab.isin(['ESC','DEESC'])].copy(); ks['sgn']=np.where(ks.lab=='ESC',1,-1)
ks['p0']=ks.ep.map(P); ks['p30']=(ks.ep+1800).map(P); ks['m60']=(ks.ep-3600).map(P)
rec=dict(all_posts=len(d),after_3h_filter=int(keep.sum()),signal_human=dict(ks.lab.value_counts()),valid_post30={c:int(ks[(ks.lab==c)].p30.notna().sum()&1 and ks[(ks.lab==c)&ks.p30.notna()&ks.p0.notna()].shape[0]) for c in ('DEESC','ESC')},valid_post30_and_pre60={c:int(ks[(ks.lab==c)&ks.p30.notna()&ks.p0.notna()&ks.m60.notna()].shape[0]) for c in ('DEESC','ESC')},dropped_for_no_window={c:int(ks[(ks.lab==c)&(ks.p30.isna()|ks.p0.isna())].shape[0]) for c in ('DEESC','ESC')})
ks['wk']=pd.to_datetime(ks.ep,unit='s',utc=True).dt.dayofweek>=5; rec['signal_dropped_weekend_share']=float(ks[ks.p30.isna()|ks.p0.isna()].wk.mean()); rec['signal_all_weekend_share']=float(ks.wk.mean())
R['reconciliation']=rec
json.dump(R,open('results_robust_headline.json','w'),indent=1,default=float)
# summary
rows=[]
for k_,v in R.items():
    if isinstance(v,dict) and 'DEESC' in v:
        for c in ('DEESC','ESC'):
            o=v[c]; rows.append((k_,c,o.get('n'),round(o.get('mean',np.nan),2),round(o.get('median',np.nan),2),round(o.get('p_post_gt0',np.nan),4),round(o.get('mean_pre',np.nan),2),round(o.get('paired',np.nan),2),round(o.get('p_post_gt_pre',np.nan),3)))
print(pd.DataFrame(rows,columns=['variant','cls','n','mean','median','p>0','pre','paired','p post>pre']).to_string(index=False))
print(json.dumps({k:R[k] for k in ('V5_events_on_big_days','V5_leave_one_out','V6_spread','reconciliation')},indent=1,default=float))
