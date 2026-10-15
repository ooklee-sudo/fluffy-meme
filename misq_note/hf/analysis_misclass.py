"""ANALYSIS_PLAN_MISCLASS_THEORY.md"""
import numpy as np, pandas as pd, json
rng=np.random.default_rng(20261014)
C=['ESC','DEESC','MIXED','OTHER']
L=pd.read_csv('third_coder_labels.csv',dtype={'id':str})
T=pd.read_csv('raw5m_duka/ticks_WTI.csv.gz'); tep=T.ep.values; mid=T.mid.values
def P(s):
    i=np.searchsorted(tep,s,side='right')-1
    return np.nan if i<0 or s-tep[i]>600 else mid[i]
a=pd.read_csv('raw/truth_archive.csv',dtype={'id':str}); a['ep']=pd.to_datetime(a.created_at,utc=True,format='ISO8601').map(lambda x:x.timestamp())
H=L.merge(a[['id','ep']],on='id').sort_values('ep').reset_index(drop=True); H['gap']=H.ep.diff().fillna(1e9); H['day']=pd.to_datetime(H.ep,unit='s',utc=True).dt.date.astype(str)
H['r30']=100*np.log(H.ep.add(1800).map(P)/H.ep.map(P))
isE=(H.gap>=3*3600)&H.r30.notna(); E=H[isE].copy(); V=H[~isE].copy()
print(len(E),len(V))
SETS={'model1':'model1','v2_majority':'v2_maj','v2_opus':None,'v2_sonnet':None,'v2_haiku':None,'v2_sonnet_repeat':None}
M=pd.read_csv('model_v2_labels_191.csv',dtype={'id':str}).set_index('id')
for nm,c in (('v2_opus','v2_run1'),('v2_sonnet','v2_run2'),('v2_haiku','v2_run3'),('v2_sonnet_repeat','v2_run4')):
    H[nm]=H.id.map(M[c]); 
H['v2_majority']=H.v2_maj; H['model1']=H.model1
E=H[isE].copy(); V=H[~isE].copy()
def Qmat(V,lab,truth,sm=0.5):
    Q=np.zeros((4,4)); 
    for i,c in enumerate(C):
        sub=V[V[lab]==c]
        for k,kk in enumerate(C): Q[i,k]=(sub[truth]==kk).sum()+sm
        Q[i]/=Q[i].sum()
    return Q
def stats_(E,V,lab,truth):
    Q=Qmat(V,lab,truth); gm=E.r30.mean()
    m=np.array([E[E[lab]==c].r30.mean() if (E[lab]==c).sum()>=3 else gm for c in C])
    mu=np.array([E[E[truth]==c].r30.mean() if (E[truth]==c).sum()>=3 else gm for c in C])
    pred=Q@mu; 
    try: corr=np.linalg.solve(Q,m)
    except Exception: corr=np.full(4,np.nan)
    return Q,m,mu,pred,corr
def run(lab,truth='final',B=2000):
    Q,m,mu,pred,corr=stats_(E,V,lab,truth); days=E.day.unique(); byday={d:E[E.day==d] for d in days}
    boots=[]
    for _ in range(B):
        Eb=pd.concat([byday[d] for d in rng.choice(days,len(days))]); Vb=V.sample(len(V),replace=True,random_state=int(rng.integers(1e9)))
        try:
            Qb,mb,mub,pb,cb=stats_(Eb,Vb,lab,truth); boots.append(np.r_[mb-pb,cb,mub])
        except Exception: pass
    boots=np.array(boots)
    o=dict(n_events=int(len(E)),Q=Q.round(3).tolist(),cond=float(np.linalg.cond(Q)),obs_by_label=dict(zip(C,m.round(3))),pred_by_label=dict(zip(C,pred.round(3))),human_class_mean=dict(zip(C,mu.round(3))),corrected=dict(zip(C,corr.round(3))))
    ci=lambda x:[float(np.percentile(x,2.5)),float(np.percentile(x,97.5))]
    o['diff_obs_minus_pred']={c:dict(diff=float(m[i]-pred[i]),ci=ci(boots[:,i])) for i,c in enumerate(C[:2])}
    o['corrected_ci']={c:ci(boots[:,4+i]) for i,c in enumerate(C[:2])}
    # directional: ESC sign +, DEESC sign -
    o['directional']=dict(ESC=dict(observed=float(m[0]),predicted=float(pred[0]),corrected=float(corr[0]),human=float(mu[0])),DEESC=dict(observed=float(-m[1]),predicted=float(-pred[1]),corrected=float(-corr[1]),human=float(-mu[1])))
    # T3 decomposition for ESC and DEESC labels
    dec={}
    for i,c in enumerate(C[:2]):
        sg=1 if c=='ESC' else -1; dec[c]={kk:float(sg*Q[i,k]*mu[k]) for k,kk in enumerate(C)}; dec[c]['true_class_share_Q']=float(Q[i,i])
    o['decomposition']=dec
    return o
R={'event_n':int(len(E)),'validation_n':int(len(V))}
for nm in SETS: R[nm]=run(nm)
R['robust_v3']={nm:run(nm,truth='v3') for nm in ('model1','v2_majority')}
# in-sample Q (all 191)
def insample(lab,truth='final'):
    Qa=Qmat(H,lab,truth); gm=E.r30.mean(); m=np.array([E[E[lab]==c].r30.mean() if (E[lab]==c).sum()>=3 else gm for c in C]); corr=np.linalg.solve(Qa,m); return dict(corrected={c:float(corr[i]) for i,c in enumerate(C[:2])})
R['insample_Q']={nm:insample(nm) for nm in SETS}
json.dump(R,open('results_misclass.json','w'),indent=1,default=float)
print('human directional benchmark: ESC',round(E[E.final=='ESC'].r30.mean(),3),'DEESC',round(-E[E.final=='DEESC'].r30.mean(),3))
for nm in SETS:
    d=R[nm]['directional']; df=R[nm]['diff_obs_minus_pred']
    print(nm,'ESC obs/pred/corr/human',[round(d['ESC'][k],2) for k in ('observed','predicted','corrected','human')],'diff CI',[round(x,2) for x in df['ESC']['ci']],'| DEESC',[round(d['DEESC'][k],2) for k in ('observed','predicted','corrected','human')],'diff CI',[round(x,2) for x in df['DEESC']['ci']],'| cond',round(R[nm]['cond'],1),'corrCI ESC',[round(x,2) for x in R[nm]['corrected_ci']['ESC']])
print(json.dumps(R['model1']['decomposition'],indent=0)); print(json.dumps(R['v2_majority']['decomposition'],indent=0))
print({k:{kk:round(vv,2) for kk,vv in v['corrected'].items()} for k,v in R['insample_Q'].items()})
