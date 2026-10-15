"""ANALYSIS_PLAN_THIRD_CODER.md"""
import numpy as np, pandas as pd, json, openpyxl
from scipy import stats
from sklearn.metrics import cohen_kappa_score as ck
rng=np.random.default_rng(20261014)
ws=openpyxl.load_workbook('third_coder_returned.xlsx')['Coding']
r=pd.DataFrame(list(ws.iter_rows(min_row=2,values_only=True)),columns=['item','text','cls','conf','notes']); r=r[r.item.notna()]; r['third']=r.cls.str.upper().str.strip()
key=pd.read_csv('third_coder_key_PRIVATE.csv',dtype={'id':str}); r['item']=r.item.astype(int)
K=key.merge(r[['item','third','conf']],on='item')
L=pd.read_csv('model_v2_labels_191.csv',dtype={'id':str}); L=L.merge(K[['id','third','kind']],on='id',how='left')
R={}
adj=L[L.kind=='adjudicated']; ctl=L[L.kind=='control']
hh=pd.read_csv('human_labels_191.csv',dtype={'id':str})[['id','hA','hB']]; L=L.merge(hh,on='id',how='left'); adj=L[L.kind=='adjudicated']; ctl=L[L.kind=='control']
# 1 agreement
def kap(a,b): return float(ck(a,b))
R['agreement']=dict(n_adjudicated=int(len(adj)),n_controls=int(len(ctl)),
 third_vs_A=kap(adj.dropna(subset=['hA']).third,adj.dropna(subset=['hA']).hA),third_vs_B=kap(adj.dropna(subset=['hB']).third,adj.dropna(subset=['hB']).hB),A_vs_B_on_adjudicated=kap(adj.dropna(subset=['hA','hB']).hA,adj.dropna(subset=['hA','hB']).hB),
 third_vs_investigator_adjudicated=kap(adj.third,adj.final),agree_rate_third_vs_investigator=float((adj.third==adj.final).mean()),
 controls_kappa_third_vs_consensus=kap(ctl.third,ctl.final),controls_agree_rate=float((ctl.third==ctl.final).mean()))
R['agreement']['third_class_counts_adjudicated']=adj.third.value_counts().to_dict(); R['agreement']['investigator_class_counts_adjudicated']=adj.final.value_counts().to_dict()
# 2 v3 final
def v3(row):
    if row.kind!='adjudicated': return row.final
    votes=[x for x in (row.hA,row.hB,row.third) if isinstance(x,str)]; c=pd.Series(votes).value_counts()
    if c.iloc[0]>=2: return c.index[0]
    return 'MIXED' if 'MIXED' in votes else 'OTHER'
L['v3']=L.apply(v3,axis=1); L['third_only']=np.where(L.kind=='adjudicated',L.third,L.final)
ch=L[L.v3!=L.final]; R['changes']=dict(n_changed=int(len(ch)),from_to=ch.groupby(['final','v3']).size().reset_index().values.tolist(),final_counts_investigator=L.final.value_counts().to_dict(),final_counts_v3=L.v3.value_counts().to_dict(),third_only_counts=L.third_only.value_counts().to_dict())
tie_all=L[(L.kind=='adjudicated')&L.apply(lambda x:len({x.hA,x.hB,x.third})==3,axis=1)]; R['changes']['n_all_three_differ']=int(len(tie_all))
# adjudication split under v3: items in final class decided with third coder
for c in ('ESC','DEESC'):
    s=L[L.v3==c]; R['changes'][f'{c}_v3_total']=int(len(s)); R['changes'][f'{c}_v3_from_adjudicated_items']=int((s.kind=='adjudicated').sum()); R['changes'][f'{c}_v3_third_in_majority']=int(((s.kind=='adjudicated')&(s.third==s.v3)).sum())
# ticks
T=pd.read_csv('raw5m_duka/ticks_WTI.csv.gz'); tep=T.ep.values; mid=T.mid.values
def P(s):
    i=np.searchsorted(tep,s,side='right')-1
    return np.nan if i<0 or s-tep[i]>600 else mid[i]
a=pd.read_csv('raw/truth_archive.csv',dtype={'id':str}); a['ep']=pd.to_datetime(a.created_at,utc=True,format='ISO8601').map(lambda x:x.timestamp())
H=L.merge(a[['id','ep']],on='id').sort_values('ep').reset_index(drop=True); H['gap']=H.ep.diff().fillna(1e9); H['day']=pd.to_datetime(H.ep,unit='s',utc=True).dt.date.astype(str)
H['p0']=H.ep.map(P); H['p30']=(H.ep+1800).map(P); H['r30']=100*np.log(H.p30/H.p0)
E=H[(H.gap>=3*3600)&H.r30.notna()].copy()
def dcb(v,days,B=10000,stat=np.mean):
    ud=np.unique(days); g={u:v[days==u] for u in ud}; o=[stat(np.concatenate([g[u] for u in rng.choice(ud,len(ud))])) for _ in range(B)]; return [float(np.percentile(o,2.5)),float(np.percentile(o,97.5))]
def summ(col):
    o={}
    for c in ('DEESC','ESC'):
        s=E[E[col]==c]; sg=1 if c=='ESC' else -1; v=(sg*s.r30).values
        if len(v)>=6: o[c]=dict(n=int(len(v)),mean=float(v.mean()),median=float(np.median(v)),p_two=float(stats.wilcoxon(v).pvalue),mean_ci=dcb(v,s.day.values),median_ci=dcb(v,s.day.values,stat=np.median),n_days=int(s.day.nunique()))
        else: o[c]=dict(n=int(len(v)))
    return o
R['headline']={'investigator_final':summ('final'),'v3_final':summ('v3'),'third_only':summ('third_only')}
# consensus-only (unchanged items) for reference: items with kind!=adjudicated keep label else OTHER
H['cons_only']=np.where(H.kind=='adjudicated','OTHER',H.final); E['cons_only']=H.loc[E.index,'cons_only'] if False else E.index.map(lambda i:H.loc[i,'cons_only'])
R['headline']['consensus_only']=summ('cons_only')
# 3 label sets vs v3
def prf(pred,true,c): 
    tp=((pred==c)&(true==c)).sum(); return dict(precision=float(tp/max((pred==c).sum(),1)),recall=float(tp/max((true==c).sum(),1)),n_pred=int((pred==c).sum()),n_true=int((true==c).sum()))
R['model_vs_v3']={nm:dict(kappa=float(ck(L.v3,L[c])),ESC=prf(L[c],L.v3,'ESC'),DEESC=prf(L[c],L.v3,'DEESC')) for nm,c in (('model1','model1'),('v2_majority','v2_maj'),('investigator_final','final'))}
R['model_vs_final_for_ref']={nm:float(ck(L.final,L[c])) for nm,c in (('model1','model1'),('v2_majority','v2_maj'))}
R['label_sets']={}
for nm,col in (('v3_final','v3'),('model1','model1'),('v2_majority','v2_maj'),('investigator_final','final')): R['label_sets'][nm]=summ(col)
days=E.day.unique(); byday={x:E[E.day==x] for x in days}
def cm(df,col,c):
    s=df[df[col]==c]; sg=1 if c=='ESC' else -1; return (sg*s.r30).mean() if len(s) else np.nan
R['diff_v3_minus']={}
for nm,col in (('model1','model1'),('v2_majority','v2_maj')):
    o={}
    for c in ('DEESC','ESC'):
        obs=cm(E,'v3',c)-cm(E,col,c); b=[]
        for _ in range(10000):
            s=pd.concat([byday[x] for x in rng.choice(days,len(days))]); b.append(cm(s,'v3',c)-cm(s,col,c))
        b=np.array(b); b=b[~np.isnan(b)]; o[c]=dict(diff=float(obs),ci=[float(np.percentile(b,2.5)),float(np.percentile(b,97.5))],p_two=float(min(1,2*min((b<=0).mean(),(b>=0).mean()))))
    R['diff_v3_minus'][nm]=o
L[['id','round','kind','hA','hB','final','third','v3','third_only','model1','v2_maj']].to_csv('third_coder_labels.csv',index=False)
json.dump(R,open('results_third_coder.json','w'),indent=1,default=float)
print(json.dumps({k:R[k] for k in ('agreement','changes')},indent=1,default=float))
for k in ('headline','model_vs_v3','diff_v3_minus'): print(k); print(json.dumps(R[k],indent=0,default=float)[:3500])
