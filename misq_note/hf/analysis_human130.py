import pandas as pd, numpy as np, json
from collections import Counter
key=pd.read_csv('human_coding_key_130.csv',dtype={'id':str})
def read(f): d=pd.read_excel(f,sheet_name='Coding'); d.columns=['item','text','cls','conf','notes']; return d.set_index('item')
A=read('/tmp/h130/coderA.xlsx'); B=read('/tmp/h130/coderB.xlsx')
key['hA']=key.item.map(A.cls.astype(str).str.strip().str.upper()); key['hB']=key.item.map(B.cls.astype(str).str.strip().str.upper())
R={'n':len(key),'items_A':int(len(A)),'items_B':int(len(B)),'missing_A':int((~key.hA.isin(['ESC','DEESC','MIXED','OTHER'])).sum()),'missing_B':int((~key.hB.isin(['ESC','DEESC','MIXED','OTHER'])).sum()),
   'dist':{'A':key.hA.value_counts().to_dict(),'B':key.hB.value_counts().to_dict(),'model1':key.model1.value_counts().to_dict()}}
def kappa(x,y):
    cats=sorted(set(x)|set(y)); n=len(x); po=np.mean([i==j for i,j in zip(x,y)]); pe=sum((Counter(x)[c]/n)*(Counter(y)[c]/n) for c in cats); return round(float((po-pe)/(1-pe)),3),round(float(po),3)
ok=key.hA.isin(['ESC','DEESC','MIXED','OTHER'])&key.hB.isin(['ESC','DEESC','MIXED','OTHER']); R['n_both_coded']=int(ok.sum()); R['kappa_AB']=kappa(key[ok].hA.tolist(),key[ok].hB.tolist()); key['cons']=np.where(ok&(key.hA==key.hB),key.hA,None); c=key[key.cons.notna()]
R['n_consensus']=len(c); R['n_disagree']=int(len(key)-len(c)); okA=key.hA.isin(['ESC','DEESC','MIXED','OTHER']); R['kappa_A_model1']=kappa(key[okA].hA.tolist(),key[okA].model1.tolist()); R['kappa_B_model1']=kappa(key.hB.tolist(),key.model1.tolist()); R['kappa_cons_model1']=kappa(c.cons.tolist(),c.model1.tolist())
R['consensus_dist']=c.cons.value_counts().to_dict(); R['confusion_model1_vs_consensus']=pd.crosstab(c.cons,c.model1).to_dict()
key[key.cons.isna()][['item','id','model1','hA','hB']].to_csv('human130_disagreements.csv',index=False)
json.dump(R,open('results_human130_prelim.json','w'),indent=1,default=float); print(json.dumps(R,indent=1,default=float))
