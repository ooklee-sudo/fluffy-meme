import numpy as np, pandas as pd, json, os
import statsmodels.api as sm
from scipy import stats
rng=np.random.default_rng(20261014)
T=pd.read_csv('../hf/raw5m_duka/ticks_WTI.csv.gz'); tep=T.ep.values; mid=T.mid.values
def P(s):
    i=np.searchsorted(tep,s,side='right')-1
    if i<0 or s-tep[i]>600: return np.nan
    return mid[i]
F=pd.read_csv('frame_features.csv',dtype={'id':str}); K=F[F.keep].copy()
K['p0']=K.ep.map(P); K['p30']=(K.ep+1800).map(P); K['m30']=(K.ep-1800).map(P)
K['r30']=100*np.log(K.p30/K.p0); K['pre30']=100*np.log(K.p0/K.m30); K['absz']=K.r30.abs()/K.s30
K['year']=pd.to_datetime(K.ep,unit='s',utc=True).dt.year; K['day']=pd.to_datetime(K.ep,unit='s',utc=True).dt.date.astype(str)
R={'frame':len(F),'kept':len(K)}
V=K.dropna(subset=['r30','absz','Nc','U']); R['valid_windows']=int(len(V)); R['excluded_no_window']=int(len(K)-len(V)); R['valid_by_year']=V.groupby('year').size().to_dict()
def ols(df,cols):
    X=pd.concat([df[cols].reset_index(drop=True),pd.get_dummies(df.year,drop_first=True,dtype=float).reset_index(drop=True)],axis=1); X=sm.add_constant(X.astype(float))
    return sm.OLS(df.absz.values,X).fit(cov_type='cluster',cov_kwds={'groups':pd.factorize(df.day)[0]})
def one(f,n): c=f.params[n]; p=f.pvalues[n]; return dict(coef=float(c),se=float(f.bse[n]),p_two=float(p),p_one=float(p/2 if c>0 else 1-p/2))
f1=ols(V,['Nc']); f2=ols(V,['U']); V=V.assign(NcU=V.Nc*V.U); f3=ols(V,['Nc','U','NcU'])
R['HI1']=one(f1,'Nc'); R['HI2']=one(f2,'U'); R['HI3']=one(f3,'NcU'); R['joint_main']={n:one(f3,n) for n in ('Nc','U')}
ps=sorted([('HI1',R['HI1']['p_one']),('HI2',R['HI2']['p_one']),('HI3',R['HI3']['p_one'])],key=lambda x:x[1]); adj={}; m=3; run=0
for i,(n,p) in enumerate(ps): run=max(run,min(1,(m-i)*p)); adj[n]=run
R['holm_adjusted']=adj
f4=ols(V.dropna(subset=['Nt']),['Nt']); R['robust_Nt']=one(f4,'Nt'); R['mean_absz']=float(V.absz.mean()); R['median_absz']=float(V.absz.median())
# labels
labs={}
for c in ('1','2'):
    p=f'labels_coder{c}.json'
    if os.path.exists(p): labs[c]={k:v['cls'] for k,v in json.load(open(p)).items()}
if len(labs)==2:
    V['m1']=V.id.map(labs['1']); V['m2']=V.id.map(labs['2']); V['agreed']=np.where(V.m1==V.m2,V.m1,None)
    R['label_dist_model1']=V.m1.value_counts().to_dict(); R['agreed_dist']=V.agreed.value_counts().to_dict()
    hl=None
    if os.path.exists('human_labels_twitter.csv'): hl=pd.read_csv('human_labels_twitter.csv',dtype={'id':str}).set_index('id').final
    for name,col in (('agreed','agreed'),('model1','m1')):
        for cls,sg in (('DEESC',-1),('ESC',1)):
            s=V[V[col]==cls].copy(); s['dir30']=sg*s.r30; s['dirpre']=sg*s.pre30; o={'n':int(len(s))}
            if len(s)>=6:
                both=s[['dir30','dirpre']].dropna(); o.update(mean30=float(s.dir30.mean()),median30=float(s.dir30.median()),wilcoxon_gt0=float(stats.wilcoxon(s.dir30,alternative='greater').pvalue),mean_pre30=float(s.dirpre.mean()),paired_diff=float((both.dir30-both.dirpre).mean()),wilcoxon_post_gt_pre=float(stats.wilcoxon(both.dir30-both.dirpre,alternative='greater').pvalue))
            R[f'H10_{name}_{cls}']=o
    if hl is not None:
        V['hum']=V.id.map(hl)
        for cls,sg in (('DEESC',-1),('ESC',1)):
            s=V[V.hum==cls].copy(); s['dir30']=sg*s.r30; s['dirpre']=sg*s.pre30; o={'n':int(len(s))}
            if len(s)>=6:
                both=s[['dir30','dirpre']].dropna(); o.update(mean30=float(s.dir30.mean()),median30=float(s.dir30.median()),wilcoxon_gt0=float(stats.wilcoxon(s.dir30,alternative='greater').pvalue),mean_pre30=float(s.dirpre.mean()),paired_diff=float((both.dir30-both.dirpre).mean()),wilcoxon_post_gt_pre=float(stats.wilcoxon(both.dir30-both.dirpre,alternative='greater').pvalue))
            R[f'H10_human_{cls}']=o
# H9: Truth Social keyword posts, same scaling
w=pd.read_csv('../hf/rawd/DCOILWTICO.csv',index_col=0); w.index=pd.to_datetime(w.index); s=pd.to_numeric(w.iloc[:,0],errors='coerce'); s=s[s>0]; r=100*np.log(s/s.shift(1)).dropna()
H=pd.read_csv('../hf/human_labels_191.csv',dtype={'id':str}); a=pd.read_csv('../hf/raw/truth_archive.csv',dtype={'id':str}); a['ep']=pd.to_datetime(a.created_at,utc=True,format='ISO8601').map(lambda x:x.timestamp()); H=H.merge(a[['id','ep']],on='id').sort_values('ep').reset_index(drop=True)
H['keep']=H.ep.diff().fillna(1e9)>=3*3600; H=H[H.keep].copy()
def sd60(ep):
    dte=pd.Timestamp(ep,unit='s').normalize(); x=r[r.index<dte].iloc[-60:]; return float(x.std()) if len(x)>=48 else np.nan
H['s30']=[sd60(e)*np.sqrt(30/1380) for e in H.ep]; H['p0']=H.ep.map(P); H['p30']=(H.ep+1800).map(P); H['absz']=(100*np.log(H.p30/H.p0)).abs()/H.s30; Hv=H.dropna(subset=['absz'])
x=V.absz.values; y=Hv.absz.values; obs=x.mean()-y.mean(); pool=np.r_[x,y]; cnt=0
for _ in range(20000):
    q=rng.permutation(pool); cnt+= abs(q[:len(x)].mean()-q[len(x):].mean())>=abs(obs)
R['H9']=dict(n_twitter=len(x),n_truth=len(y),mean_twitter=float(x.mean()),mean_truth=float(y.mean()),diff=float(obs),perm_p_two=float((cnt+1)/20001),median_twitter=float(np.median(x)),median_truth=float(np.median(y)))
json.dump(R,open('results_twitter.json','w'),indent=1,default=float); print(json.dumps(R,indent=1,default=float))
