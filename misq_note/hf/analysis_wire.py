import json, pandas as pd, numpy as np
from scipy import stats
rng=np.random.default_rng(20261014)
W={}
for f in 'ABCD': W.update(json.load(open(f'qual/wire_{f}.json')))
K=pd.read_csv('qual/wire_cases_KEY.csv'); K['cl']=K.wid.map(lambda w:W[w]['class'])
K['sgn']=np.where(K.cls=='ESC',1,-1); K['e']=K.sgn*K.oil
LINK=['W39','W40','W41','W42','W43','W52','W59']; REPOST=['W08','W27']
K['aux']=np.where(K.wid.isin(LINK),'LINK',np.where(K.wid.isin(REPOST),'REPOST','TEXT'))
def perm(x,y,B=20000):
    obs=x.mean()-y.mean(); pool=np.r_[x,y]; c=0
    for _ in range(B):
        q=rng.permutation(pool); c+= q[:len(x)].mean()-q[len(x):].mean()>=obs
    return dict(diff=float(obs),perm_p_greater=float((c+1)/(B+1)))
R={'counts':K.cl.value_counts().to_dict(),'by_direction':pd.crosstab(K.cl,K.cls).to_dict(),'by_aux':pd.crosstab(K.cl,K.aux).to_dict()}
R['mean_median_by_class']=K.groupby('cl').e.agg(['count','mean','median']).round(3).to_dict('index')
pf=K[K.cl=='POST_FIRST'].e.values; of=K[K.cl=='OTHER_FIRST'].e.values
R['W1_all']=dict(n_pf=len(pf),n_of=len(of),mean_pf=float(pf.mean()),mean_of=float(of.mean()),median_pf=float(np.median(pf)),median_of=float(np.median(of)),mw_p=float(stats.mannwhitneyu(pf,of,alternative='greater').pvalue),**perm(pf,of))
for c in ('DEESC','ESC'):
    x=K[(K.cl=='POST_FIRST')&(K.cls==c)].e.values; y=K[(K.cl=='OTHER_FIRST')&(K.cls==c)].e.values
    R[f'W1_{c}']=dict(n_pf=len(x),n_of=len(y),mean_pf=float(x.mean()) if len(x) else None,mean_of=float(y.mean()) if len(y) else None)
    if len(x)>=3 and len(y)>=3: R[f'W1_{c}'].update(perm(x,y))
a=K[K.cl.isin(['POST_FIRST','SIMULTANEOUS'])].e.values; R['expl_PF_plus_SIM_vs_OF']=dict(n_a=len(a),mean_a=float(a.mean()),**perm(a,of))
of_txt=K[(K.cl=='OTHER_FIRST')&(K.aux=='TEXT')].e.values; R['expl_PF_vs_OF_textonly']=dict(n_of=len(of_txt),mean_of=float(of_txt.mean()),**perm(pf,of_txt))
R['expl_OF_by_aux']=K[K.cl=='OTHER_FIRST'].groupby('aux').e.agg(['count','mean']).round(2).to_dict('index')
json.dump(R,open('results_wire.json','w'),indent=1,default=float); print(json.dumps(R,indent=1,default=float))
