"""Parts B and C of ANALYSIS_PLAN_V2RELABEL.md."""
import numpy as np, pandas as pd, json, os, glob
from scipy import stats
from sklearn.metrics import cohen_kappa_score as ck
rng=np.random.default_rng(20261014)
SP='/tmp/claude-0/-home-user-fluffy-meme/e148143b-8414-5fbc-b45d-5e7b108b6daf/scratchpad/'
MODELS={1:'opus',2:'sonnet',3:'haiku',4:'sonnet (repeat)'}
H=pd.read_csv('human_labels_191.csv',dtype={'id':str})
L={}
for r in (1,2,3,4):
    f=SP+f'relabel/output_run{r}.json'
    if not os.path.exists(f): continue
    o=json.load(open(f)); key=json.load(open(SP+f'private/key_run{r}_PRIVATE.json'))
    m={key[i]:v['cls'] for i,v in o.items()}; conf={key[i]:v['conf'] for i,v in o.items()}; L[r]=pd.Series(m)
assert set(L)=={1,2,3,4},set(L)
D=H.set_index('id').copy()
for r in L: D[f'v2_run{r}']=L[r]
order=[1,2,3,4]
def maj(row):
    c=row[[f'v2_run{r}' for r in order]].value_counts(); top=c[c==c.max()].index.tolist()
    if len(top)==1: return top[0]
    return row['v2_run1'] if row['v2_run1'] in top else top[0]   # ties: the largest run (opus)
D['v2_maj']=D.apply(maj,axis=1)
ties=int(D.apply(lambda r:(r[[f'v2_run{x}' for x in order]].value_counts()==r[[f'v2_run{x}' for x in order]].value_counts().max()).sum()>1,axis=1).sum())
R={'ties_in_majority':ties}
def boot_kappa(a,b,B=2000):
    n=len(a); ks=[ck(a.iloc[i],b.iloc[i]) for i in (rng.integers(0,n,n) for _ in range(B))]; return [float(np.percentile(ks,2.5)),float(np.percentile(ks,97.5))]
def ac1(a,b):
    cats=sorted(set(a)|set(b)); n=len(a); po=(a.values==b.values).mean(); pi=np.array([((a==c).mean()+(b==c).mean())/2 for c in cats]); pe=(pi*(1-pi)).sum()/(len(cats)-1); return float((po-pe)/(1-pe))
def prf(pred,true,cls):
    tp=((pred==cls)&(true==cls)).sum(); return dict(precision=float(tp/max((pred==cls).sum(),1)),recall=float(tp/max((true==cls).sum(),1)),n_pred=int((pred==cls).sum()),n_true=int((true==cls).sum()))
cols={'model1_original':'model1','v2_opus':'v2_run1','v2_sonnet':'v2_run2','v2_haiku':'v2_run3','v2_sonnet_repeat':'v2_run4','v2_majority':'v2_maj'}
R['agreement']={}
for name,c in cols.items():
    o={}
    for scope,mask in (('all191',D['round'].isin([2,3])),('round2',D['round']==2),('round3',D['round']==3)):
        d=D[mask]; o[scope]=dict(kappa=float(ck(d.final,d[c])),ac1=ac1(d.final,d[c]),acc=float((d.final==d[c]).mean()),ESC=prf(d[c],d.final,'ESC'),DEESC=prf(d[c],d.final,'DEESC'))
        if scope=='all191': o[scope]['kappa_ci']=boot_kappa(d.final.reset_index(drop=True),d[c].reset_index(drop=True))
    R['agreement'][name]=o
# inter-run kappas
R['inter_run_kappa']={f'{a}-{b}':float(ck(D[f'v2_run{a}'],D[f'v2_run{b}'])) for a in order for b in order if a<b}
# human-human reference
dd=H.dropna(subset=['hA','hB']); R['human_human_kappa_all']=float(ck(dd.hA,dd.hB))
# C: event-study on the same events
T=pd.read_csv('raw5m_duka/ticks_WTI.csv.gz'); tep=T.ep.values; mid=T.mid.values
def P(s):
    i=np.searchsorted(tep,s,side='right')-1
    return np.nan if i<0 or s-tep[i]>600 else mid[i]
a=pd.read_csv('raw/truth_archive.csv',dtype={'id':str}); a['ep']=pd.to_datetime(a.created_at,utc=True,format='ISO8601').map(lambda x:x.timestamp())
D=D.reset_index().merge(a[['id','ep']],on='id').sort_values('ep').reset_index(drop=True); D['gap']=D.ep.diff().fillna(1e9); D['day']=pd.to_datetime(D.ep,unit='s',utc=True).dt.date.astype(str)
D['p0']=D.ep.map(P); D['p30']=(D.ep+1800).map(P); D['r30']=100*np.log(D.p30/D.p0)
E=D[(D.gap>=3*3600)&D.r30.notna()].copy()   # union sample: filter + valid window, any label
R['union_events']=int(len(E))
sch={'human':'final','model1':'model1','v2_majority':'v2_maj','v2_opus':'v2_run1','v2_sonnet':'v2_run2','v2_haiku':'v2_run3','v2_sonnet_repeat':'v2_run4'}
def cls_mean(df,col,c):
    s=df[df[col]==c]; sg=1 if c=='ESC' else -1; return (sg*s.r30).mean() if len(s)>0 else np.nan
R['label_sets']={}
for nm,col in sch.items():
    o={}
    for c in ('DEESC','ESC'):
        s=E[E[col]==c]; v=(1 if c=='ESC' else -1)*s.r30.values
        o[c]=dict(n=int(len(v)),mean=float(v.mean()) if len(v) else None,median=float(np.median(v)) if len(v) else None,p_two=float(stats.wilcoxon(v).pvalue) if len(v)>=6 else None)
    R['label_sets'][nm]=o
# paired day-cluster bootstrap differences in class mean: human minus other label set
days=E.day.unique(); byday={d:E[E.day==d] for d in days}
def bdiff(colA,colB,c,B=10000):
    out=[]
    for _ in range(B):
        s=pd.concat([byday[d] for d in rng.choice(days,len(days))]); out.append(cls_mean(s,colA,c)-cls_mean(s,colB,c))
    out=np.array(out); out=out[~np.isnan(out)]; return out
R['difference_human_minus']={}
for nm in ('model1','v2_majority','v2_opus','v2_sonnet','v2_haiku','v2_sonnet_repeat'):
    o={}
    for c in ('DEESC','ESC'):
        obs=cls_mean(E,'final',c)-cls_mean(E,sch[nm],c); b=bdiff('final',sch[nm],c,B=4000)
        o[c]=dict(diff=float(obs),ci=[float(np.percentile(b,2.5)),float(np.percentile(b,97.5))],p_two=float(min(1,2*min((b<=0).mean(),(b>=0).mean()))))
    R['difference_human_minus'][nm]=o
# decision-rule quantities
mj=R['agreement']['v2_majority']['all191']; R['decision']=dict(kappa=mj['kappa'],esc_precision=mj['ESC']['precision'],rule_prompt_problem=bool(mj['kappa']>=0.60 and mj['ESC']['precision']>=0.70))
# label counts
R['counts']={nm:E_ for nm,E_ in ((n,D[c].value_counts().to_dict()) for n,c in (('human','final'),('model1','model1'),('v2_majority','v2_maj'),('opus','v2_run1'),('sonnet','v2_run2'),('haiku','v2_run3'),('sonnet_repeat','v2_run4')))}
D[['id','round','model1','final','source','v2_run1','v2_run2','v2_run3','v2_run4','v2_maj']].to_csv('model_v2_labels_191.csv',index=False)
json.dump(R,open('results_v2relabel.json','w'),indent=1,default=float)
print(json.dumps({k:R[k] for k in ('counts','inter_run_kappa','human_human_kappa_all','decision','union_events')},indent=1,default=float))
rows=[]
for nm,o in R['agreement'].items(): rows.append((nm,round(o['all191']['kappa'],3),round(o['all191']['ac1'],3),round(o['round2']['kappa'],3),round(o['round3']['kappa'],3),round(o['all191']['ESC']['precision'],2),round(o['all191']['ESC']['recall'],2),round(o['all191']['DEESC']['precision'],2),round(o['all191']['DEESC']['recall'],2)))
print(pd.DataFrame(rows,columns=['labels','kappa191','AC1','k_r2','k_r3','ESC prec','ESC rec','DEESC prec','DEESC rec']).to_string(index=False))
print(json.dumps(R['label_sets'],indent=0,default=float)[:2500]); print(json.dumps(R['difference_human_minus'],indent=0,default=float))
