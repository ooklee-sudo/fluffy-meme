import pandas as pd, numpy as np, json, re
from collections import Counter
key=pd.read_csv('human_coding_key.csv',dtype={'id':str})
def read(f): d=pd.read_excel(f,sheet_name='Coding'); d.columns=['item','text','cls','conf','notes']; return d.set_index('item')
A=read('/tmp/humancode/coderA.xlsx'); B=read('/tmp/humancode/coderB.xlsx')
key['hA']=key.item.map(A.cls.str.strip().str.upper()); key['hB']=key.item.map(B.cls.str.strip().str.upper()); key['confA']=key.item.map(A.conf); key['confB']=key.item.map(B.conf)
key['cons']=np.where(key.hA==key.hB,key.hA,None)
def kappa(x,y):
    cats=sorted(set(x)|set(y)); n=len(x); po=np.mean([i==j for i,j in zip(x,y)]); pe=sum((Counter(x)[c]/n)*(Counter(y)[c]/n) for c in cats); return float((po-pe)/(1-pe)),float(po)
def col3(s): return s.map(lambda v:v if v in('ESC','DEESC') else 'NONSIG')
def col2(s): return s.map(lambda v:'SIG' if v in('ESC','DEESC') else 'NONSIG')
R={}
for nm,f in (('4class',lambda s:s),('3class',col3),('2class',col2)):
    R[nm]={}
    for a,b in (('hA','hB'),('hA','model1'),('hB','model1'),('hA','model2'),('hB','model2'),('model1','model2')):
        k,po=kappa(f(key[a]).tolist(),f(key[b]).tolist()); R[nm][f'{a}-{b}']=dict(kappa=round(k,3),agree=round(po,3))
    c=key[key.cons.notna()]
    for m in ('model1','model2'):
        k,po=kappa(f(c.cons).tolist(),f(c[m]).tolist()); R[nm][f'consensus-{m}']=dict(kappa=round(k,3),agree=round(po,3),n=len(c))
c=key[key.cons.notna()]
R['confusion_model1_vs_consensus']=pd.crosstab(c.cons,c.model1).to_dict(); R['confusion_model2_vs_consensus']=pd.crosstab(c.cons,c.model2).to_dict()
for m in ('model1','model2'):
    for cl in ('ESC','DEESC'):
        pr=(c[c[m]==cl].cons==cl).mean() if (c[m]==cl).any() else np.nan; rc=(c[c.cons==cl][m]==cl).mean() if (c.cons==cl).any() else np.nan
        R[f'{m}_{cl}']=dict(model_n=int((c[m]==cl).sum()),precision=round(float(pr),3),human_n=int((c.cons==cl).sum()),recall=round(float(rc),3))
W=c[c['sample']=='W']
for m in ('model1','model2'):
    for cl in ('ESC','DEESC'):
        R[f'W_{m}_{cl}']=dict(model_n=int((W[m]==cl).sum()),precision=round(float((W[W[m]==cl].cons==cl).mean()),3) if (W[m]==cl).any() else None)
R['W_n_consensus']=len(W); R['W_kappa_4class_consensus_model1']=round(kappa(W.cons.tolist(),W.model1.tolist())[0],3)
# H3 disagreements
a=pd.read_csv('raw/truth_archive.csv',dtype={'id':str}); txt=a.set_index('id').content.fillna('')
key['emptytxt']=key.id.map(lambda i:len(re.sub(r'https?://\S+','',re.sub(r'^\s*RT:?','',txt.get(i,''))).strip())<20)
dis=key[(key.cons.notna())&(key.cons!=key.model1)]
R['H3']=dict(n_disagree_model1_vs_consensus=int(len(dis)),cells=Counter(zip(dis.model1,dis.cons)).most_common(8),share_empty_text=float(dis.emptytxt.mean()),share_with_MIXED=float(((dis.model1=='MIXED')|(dis.cons=='MIXED')).mean()))
R['H3']['cells']=[[list(k),v] for k,v in R['H3']['cells']]
R['human_class_distribution']=dict(A=key.hA.value_counts().to_dict(),B=key.hB.value_counts().to_dict(),model1=key.model1.value_counts().to_dict(),model2=key.model2.value_counts().to_dict())
R['human_conf']=dict(A_conf2=float((key.confA==2).mean()),B_conf2=float((key.confB==2).mean()))
# H4 overlap with 61 tick-analysis posts
t=pd.read_csv('qual/wire_cases_KEY.csv',dtype={'id':str}); ov=t.merge(key[['id','hA','hB','cons','model1','model2']],on='id')
R['H4']=dict(n_overlap=int(len(ov)),rows=ov[['wid','cls','hA','hB','cons','model1']].astype(str).values.tolist())
json.dump(R,open('results_human_detail.json','w'),indent=1,default=float); print(json.dumps(R,indent=1,default=float))
