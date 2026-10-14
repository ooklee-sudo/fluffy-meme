import pandas as pd, numpy as np, json
from collections import Counter
from scipy import stats
key=pd.read_csv('human_coding_key_61.csv',dtype={'id':str})
def read(f): d=pd.read_excel(f,sheet_name='Coding'); d.columns=['item','text','cls','conf','notes']; return d.set_index('item')
A=read('/tmp/human61/coderA.xlsx'); B=read('/tmp/human61/coderB.xlsx')
key['hA']=key.item.map(A.cls.astype(str).str.strip().str.upper()); key['hB']=key.item.map(B.cls.astype(str).str.strip().str.upper())
key['confA']=key.item.map(A.conf); key['confB']=key.item.map(B.conf)
R={'n':len(key),'missing_A':int(key.hA.isin(['NAN','NONE']).sum()),'missing_B':int(key.hB.isin(['NAN','NONE']).sum()),'class_dist':{'A':key.hA.value_counts().to_dict(),'B':key.hB.value_counts().to_dict(),'model1':key.model1.value_counts().to_dict()}}
def kappa(x,y):
    cats=sorted(set(x)|set(y)); n=len(x); po=np.mean([i==j for i,j in zip(x,y)]); pe=sum((Counter(x)[c]/n)*(Counter(y)[c]/n) for c in cats); return round(float((po-pe)/(1-pe)),3),round(float(po),3)
key['cons']=np.where(key.hA==key.hB,key.hA,None)
R['kappa_AB']=kappa(key.hA.tolist(),key.hB.tolist()); c=key[key.cons.notna()]; R['n_consensus']=len(c); R['n_disagree']=int(len(key)-len(c))
R['kappa_A_model1']=kappa(key.hA.tolist(),key.model1.tolist()); R['kappa_B_model1']=kappa(key.hB.tolist(),key.model1.tolist()); R['kappa_consensus_model1']=kappa(c.cons.tolist(),c.model1.tolist())
R['consensus_dist']=c.cons.value_counts().to_dict(); R['confusion_model1_vs_consensus']=pd.crosstab(c.cons,c.model1).to_dict()
# test-retest vs round 1
r1=pd.read_csv('human_coding_key.csv',dtype={'id':str}); 
def read1(f): d=pd.read_excel(f,sheet_name='Coding'); d.columns=['item','text','cls','conf','notes']; return d.set_index('item').cls.str.strip().str.upper()
a1=read1('/tmp/humancode/coderA.xlsx'); b1=read1('/tmp/humancode/coderB.xlsx'); r1['rA']=r1.item.map(a1); r1['rB']=r1.item.map(b1)
m=key.merge(r1[['id','rA','rB']],on='id'); R['retest']=dict(n=len(m),A_agree=float((m.hA==m.rA).mean()),B_agree=float((m.hB==m.rB).mean()),A_kappa=kappa(m.hA.tolist(),m.rA.tolist()),B_kappa=kappa(m.hB.tolist(),m.rB.tolist()),AB_round1_agree=float((m.rA==m.rB).mean()),AB_round2_agree=float((m.hA==m.hB).mean()))
# tick returns
src=open('analysis_5min.py').read().split("R={'n_posts'")[0]; exec(src)
K['id']=K['id'].astype(str); M=key.merge(K[['id','wid','cls','post5','post30','post60','pre30','week']],on='id',suffixes=('','_k'))
def sgn_of(l): return {'ESC':1,'DEESC':-1}.get(l,np.nan)
def run(lab,name):
    out={}
    for cl in ('DEESC','ESC'):
        s=M[M[lab]==cl].copy(); sg=sgn_of(cl); s['p30']=s.post30*0  # recompute directional with human sign
        # recompute from model sign: post30 is model-directional; convert to raw then apply label sign
        raw30=s.post30*s.model1.map(sgn_of); rawpre=s.pre30*s.model1.map(sgn_of); raw5=s.post5*s.model1.map(sgn_of)
        d30=sg*raw30; dpre=sg*rawpre; d5=sg*raw5; both=pd.DataFrame({'a':d30,'b':dpre}).dropna()
        o=dict(n=int(len(s)),mean5=float(d5.mean()) if len(s) else None,mean30=float(d30.mean()) if len(s) else None,median30=float(d30.median()) if len(s) else None,mean_pre30=float(dpre.mean()) if len(s) else None)
        if len(s)>=6: o['wilcoxon_post30_gt0']=float(stats.wilcoxon(d30.dropna(),alternative='greater').pvalue); o['wilcoxon_post_gt_pre']=float(stats.wilcoxon(both.a-both.b,alternative='greater').pvalue); o['paired_diff']=float((both.a-both.b).mean())
        out[cl]=o
    return out
R['H6_human_consensus_labels']=run('cons','human'); 
M['modlab']=M.model1; R['same_posts_model1_labels']=run('modlab','model1')
R['sign_flips']=dict(model_DEESC_to_human_ESC=int(((M.model1=='DEESC')&(M.cons=='ESC')).sum()),model_ESC_to_human_DEESC=int(((M.model1=='ESC')&(M.cons=='DEESC')).sum()),model_signal_to_human_nonsignal=int((M.model1.isin(['ESC','DEESC'])&M.cons.isin(['MIXED','OTHER'])).sum()),no_consensus=int(M.cons.isna().sum()))
# sensitivity: disagreements as MIXED => excluded from DEESC/ESC; and "either coder says DEESC"
M['either']=np.where((M.hA=='DEESC')|(M.hB=='DEESC'),'DEESC',np.where((M.hA=='ESC')|(M.hB=='ESC'),'ESC','X'))
R['sens_either_coder_DEESC']=run('either','either')['DEESC']
json.dump(R,open('results_human61.json','w'),indent=1,default=float); print(json.dumps(R,indent=1,default=float))
key[key.cons.isna()][['item','id','wid','model1','hA','hB']].to_csv('human61_disagreements.csv',index=False)
