import pandas as pd, numpy as np, json
from collections import Counter
from scipy import stats
import statsmodels.api as sm
exec(open('analysis_tariff.py').read().split("Rr={'frame'")[0])   # F,K with r30, pre30, R (labels only), day, etc.
def kappa(x,y):
    cats=sorted(set(x)|set(y)); n=len(x); po=np.mean([i==j for i,j in zip(x,y)]); pe=sum((Counter(x)[c]/n)*(Counter(y)[c]/n) for c in cats); return round((po-pe)/(1-pe),3),round(po,3)
def read(f): d=pd.read_excel(f,sheet_name='Coding'); d.columns=['item','text','cls','conf','notes']; d['cls']=d.cls.astype(str).str.strip().str.upper(); return d.set_index('item').cls
A=read('/tmp/h_tar/coderA.xlsx'); B=read('/tmp/h_tar/coderB.xlsx'); adj=pd.read_excel('/tmp/adjt/adj.xlsx',sheet_name='Adjudication'); adj.columns=['item','text','cls','notes']; adj['cls']=adj.cls.astype(str).str.strip().str.upper()
key=pd.read_csv('human_key_tariff.csv',dtype={'id':str}); key['hA']=key.item.map(A); key['hB']=key.item.map(B); key['cons']=np.where(key.hA==key.hB,key.hA,None)
key['adj']=key.item.map(adj.set_index('item').cls); key['final']=key.cons; key.loc[key.cons.isna(),'final']=key.adj
R={'adjudicated':adj.cls.value_counts().to_dict(),'final_dist':key.final.value_counts().to_dict(),'n':len(key)}
R['kappa_final_model1']=kappa(key.final.tolist(),key.c1.tolist()); R['kappa_final_model2']=kappa(key.final.tolist(),key.c2.tolist())
ag=key[key.c1.isin(['ESC','DEESC'])&(key.c1==key.c2)]; R['model_agreed_signals']=dict(n=len(ag),final_same=int((ag.final==ag.c1).sum()),final_OTHER=int((ag.final=='OTHER').sum()),final_opposite=int(((ag.c1=='ESC')&(ag.final=='DEESC')|(ag.c1=='DEESC')&(ag.final=='ESC')).sum()))
oth=key[(key.c1=='OTHER')&(key.c2=='OTHER')]; R['model_both_other']=dict(n=len(oth),human_signal=int(oth.final.isin(['ESC','DEESC']).sum()))
key.to_csv('human_labels_tariff_final.csv',index=False)
H=key[['id','final']].merge(K[['id','r30','pre30','R','day','agreed']],on='id',how='left')
for cls,sg in (('DEESC',1),('ESC',-1)):
    s=H[(H.final==cls)&H.r30.notna()].copy(); s['dir30']=sg*s.r30; s['dirpre']=sg*s.pre30; o={'n_labelled':int((H.final==cls).sum()),'n':int(len(s))}
    if len(s)>=6:
        both=s[['dir30','dirpre']].dropna(); o.update(mean30=float(s.dir30.mean()),median30=float(s.dir30.median()),wilcoxon_gt0=float(stats.wilcoxon(s.dir30,alternative='greater').pvalue),mean_pre30=float(s.dirpre.mean()),paired_diff=float((both.dir30-both.dirpre).mean()),wilcoxon_post_gt_pre=float(stats.wilcoxon(both.dir30-both.dirpre,alternative='greater').pvalue))
    R[f'H10_human_{cls}']=o
S=H[H.final.isin(['ESC','DEESC'])&H.r30.notna()&H.R.notna()].copy(); S['s']=np.where(S.final=='DEESC',1,-1); S['dir30']=np.where(S.final=='DEESC',S.r30,-S.r30); S['sR']=S.s*S.R; S['deesc']=(S.s==1).astype(float)
o={'n':int(len(S))}
if len(S)>=10:
    X=sm.add_constant(S[['sR','deesc']].astype(float)); fh=sm.OLS(S.dir30.values,X).fit(cov_type='cluster',cov_kwds={'groups':pd.factorize(S.day)[0]}); c=fh.params['sR']; p=fh.pvalues['sR']
    o.update(beta=float(c),se=float(fh.bse['sR']),p_two=float(p),p_one=float(p/2 if c>0 else 1-p/2))
R['H12_human']=o; R['primary_criterion_H12_n_ge_40']=bool(len(S)>=40)
json.dump(R,open('results_tariff_human_final.json','w'),indent=1,default=float); print(json.dumps(R,indent=1,default=float))
