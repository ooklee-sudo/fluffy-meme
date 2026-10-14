import pandas as pd, numpy as np, json
from collections import Counter
# final human labels for all 191 war-period keyword posts
def read(f): d=pd.read_excel(f,sheet_name='Coding'); d.columns=['item','text','cls','conf','notes']; return d.set_index('item')
def lab(s): return s.astype(str).str.strip().str.upper()
k61=pd.read_csv('human_coding_key_61.csv',dtype={'id':str}); k130=pd.read_csv('human_coding_key_130.csv',dtype={'id':str})
A61=read('/tmp/human61/coderA.xlsx'); B61=read('/tmp/human61/coderB.xlsx'); adj61=pd.read_excel('/tmp/adj/adj.xlsx',sheet_name='Adjudication'); adj61.columns=['item','text','cls','notes']
A130=read('/tmp/h130/coderA.xlsx'); B130=read('/tmp/h130/coderB.xlsx'); adj130=pd.read_excel('/tmp/adj130/adj.xlsx',sheet_name='Adjudication'); adj130.columns=['item','text','cls','notes']
def final(key,A,B,adj):
    key=key.copy(); key['hA']=key.item.map(lab(A.cls)); key['hB']=key.item.map(lab(B.cls)); ok=key.hA.isin(['ESC','DEESC','MIXED','OTHER'])&key.hB.isin(['ESC','DEESC','MIXED','OTHER'])
    key['cons']=np.where(ok&(key.hA==key.hB),key.hA,None); key['adj']=key.item.map(adj.set_index('item').cls.astype(str).str.strip().str.upper()); key['final']=key.cons; key.loc[key.cons.isna(),'final']=key.adj; key['source']=np.where(key.cons.notna(),'consensus','adjudicated'); return key
F61=final(k61,A61,B61,adj61); F130=final(k130,A130,B130,adj130)
H=pd.concat([F61[['id','model1','hA','hB','final','source']].assign(round=2),F130[['id','model1','hA','hB','final','source']].assign(round=3)]); H=H.reset_index(drop=True); H.to_csv('human_labels_191.csv',index=False)
R={'n':len(H),'final_dist':H.final.value_counts().to_dict(),'adjudicated_share':float((H.source=='adjudicated').mean())}
R['round3_final_dist']=F130.final.value_counts().to_dict()
def kappa(x,y):
    cats=sorted(set(x)|set(y)); n=len(x); po=np.mean([i==j for i,j in zip(x,y)]); pe=sum((Counter(x)[c]/n)*(Counter(y)[c]/n) for c in cats); return round(float((po-pe)/(1-pe)),3),round(float(po),3)
R['kappa_final_model1_all191']=kappa(H.final.tolist(),H.model1.tolist()); R['kappa_final_model1_round3']=kappa(F130.final.tolist(),F130.model1.tolist())
R['confusion_all191']=pd.crosstab(H.final,H.model1).to_dict()
# R3a recall: round 3 posts only (not selected by model as bar-having signals)
for m in ('OTHER','MIXED','ESC','DEESC'):
    s=F130[F130.model1==m]; R[f'round3_model_{m}']=dict(n=len(s),human=s.final.value_counts().to_dict())
s=F130[F130.model1.isin(['OTHER','MIXED'])]; R['recall_missed_signal_share']=dict(n=len(s),human_signal=int(s.final.isin(['ESC','DEESC']).sum()),share=float(s.final.isin(['ESC','DEESC']).mean()))
json.dump(R,open('results_human191.json','w'),indent=1,default=float); print(json.dumps(R,indent=1,default=float))
