import numpy as np, pandas as pd, json, os
import statsmodels.api as sm
from scipy import stats
T=pd.read_csv('../hf/raw5m_duka/ticks_SPX.csv.gz'); tep=T.ep.values; mid=T.mid.values
def P(s):
    i=np.searchsorted(tep,s,side='right')-1
    if i<0 or s-tep[i]>600: return np.nan
    return mid[i]
F=pd.read_csv('frame_features_tariff.csv',dtype={'id':str}); m1=json.load(open('labels_tariff_1.json')); m2=json.load(open('labels_tariff_2.json'))
F['c1']=F.id.map(lambda i:m1[i]['cls']); F['c2']=F.id.map(lambda i:m2[i]['cls']); F['agreed']=np.where((F.c1==F.c2)&F.c1.isin(['ESC','DEESC']),F.c1,None)
F=F.sort_values('ep').reset_index(drop=True)
# regime variable R from labels only (30 days before, agreed ESC/DEESC, excluding the tweet itself)
ag=F[F.agreed.notna()]; aep=ag.ep.values; asg=np.where(ag.agreed.values=='ESC',1,-1)
def R_of(ep):
    lo=np.searchsorted(aep,ep-30*86400,side='left'); hi=np.searchsorted(aep,ep,side='left'); x=asg[lo:hi]
    return (x.sum()/len(x)) if len(x)>=3 else np.nan
F['R']=F.ep.map(R_of)
K=F[F.keep].copy(); K['p0']=K.ep.map(P); K['p30']=(K.ep+1800).map(P); K['m30']=(K.ep-1800).map(P)
K['r30']=100*np.log(K.p30/K.p0); K['pre30']=100*np.log(K.p0/K.m30); K['absz']=K.r30.abs()/K.s30
K['year']=pd.to_datetime(K.ep,unit='s',utc=True).dt.year; K['day']=pd.to_datetime(K.ep,unit='s',utc=True).dt.date.astype(str)
Rr={'frame':len(F),'kept':len(K)}; V=K.dropna(subset=['r30','absz','Nc','U']); Rr['valid_windows']=int(len(V)); Rr['excluded_no_window']=int(len(K)-len(V)); Rr['valid_by_year']=V.groupby('year').size().to_dict()
def ols(df,cols,y='absz'):
    X=pd.concat([df[cols].reset_index(drop=True),pd.get_dummies(df.year,drop_first=True,dtype=float).reset_index(drop=True)],axis=1); X=sm.add_constant(X.astype(float))
    return sm.OLS(df[y].values,X).fit(cov_type='cluster',cov_kwds={'groups':pd.factorize(df.day)[0]})
def one(f,n): c=f.params[n]; p=f.pvalues[n]; return dict(coef=float(c),se=float(f.bse[n]),p_two=float(p),p_one=float(p/2 if c>0 else 1-p/2))
f1=ols(V,['Nc']); f2=ols(V,['U']); V=V.assign(NcU=V.Nc*V.U); f3=ols(V,['Nc','U','NcU'])
Rr['HI1']=one(f1,'Nc'); Rr['HI2']=one(f2,'U'); Rr['HI3']=one(f3,'NcU'); Rr['joint_main']={n:one(f3,n) for n in ('Nc','U')}
ps=sorted([('HI1',Rr['HI1']['p_one']),('HI2',Rr['HI2']['p_one']),('HI3',Rr['HI3']['p_one'])],key=lambda x:x[1]); adj={}; run=0
for i,(n,p) in enumerate(ps): run=max(run,min(1,(3-i)*p)); adj[n]=run
Rr['holm_adjusted']=adj; f4=ols(V.dropna(subset=['Nt']),['Nt']); Rr['robust_Nt']=one(f4,'Nt'); Rr['mean_absz']=float(V.absz.mean()); Rr['median_absz']=float(V.absz.median())
# H10 (agreed labels): DEESC -> +r ; ESC -> -r
Rr['agreed_dist']=V.agreed.value_counts().to_dict()
for cls,sg in (('DEESC',1),('ESC',-1)):
    s=V[V.agreed==cls].copy(); s['dir30']=sg*s.r30; s['dirpre']=sg*s.pre30; o={'n':int(len(s))}
    if len(s)>=6:
        both=s[['dir30','dirpre']].dropna(); o.update(mean30=float(s.dir30.mean()),median30=float(s.dir30.median()),wilcoxon_gt0=float(stats.wilcoxon(s.dir30,alternative='greater').pvalue),mean_pre30=float(s.dirpre.mean()),paired_diff=float((both.dir30-both.dirpre).mean()),wilcoxon_post_gt_pre=float(stats.wilcoxon(both.dir30-both.dirpre,alternative='greater').pvalue))
    Rr[f'H10_agreed_{cls}']=o
# H12: dir30 = alpha_class + beta * (s*R)
S=V[V.agreed.notna()&V.R.notna()].copy(); S['s']=np.where(S.agreed=='DEESC',1,-1); S['dir30']=np.where(S.agreed=='DEESC',S.r30,-S.r30); S['sR']=S.s*S.R; S['deesc']=(S.s==1).astype(float)
X=sm.add_constant(S[['sR','deesc']].astype(float)); fh=sm.OLS(S.dir30.values,X).fit(cov_type='cluster',cov_kwds={'groups':pd.factorize(S.day)[0]})
c=fh.params['sR']; p=fh.pvalues['sR']; Rr['H12']=dict(n=int(len(S)),beta=float(c),se=float(fh.bse['sR']),p_two=float(p),p_one=float(p/2 if c>0 else 1-p/2),n_DEESC=int((S.s==1).sum()),n_ESC=int((S.s==-1).sum()),R_mean=float(S.R.mean()),R_sd=float(S.R.std()))
# terciles of s*R (aligned vs opposed): sR high = message opposes regime
S['terc']=pd.qcut(S.sR.rank(method='first'),3,labels=['aligned','middle','opposed']); Rr['H12_terciles']=S.groupby(['terc','agreed']).dir30.agg(['count','mean']).round(3).reset_index().astype(str).values.tolist()
json.dump(Rr,open('results_tariff.json','w'),indent=1,default=float); print(json.dumps(Rr,indent=1,default=float))
