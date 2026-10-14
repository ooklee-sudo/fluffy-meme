import pandas as pd, numpy as np, json
from collections import Counter
from scipy import stats
src=open('analysis_human61.py').read().split("R['H6_human_consensus_labels']")[0]
exec(src)                         # rebuilds key (hA,hB,cons), M, K (tick returns), run(), R (round-2 results)
adj=pd.read_excel('/tmp/adj/adj.xlsx',sheet_name='Adjudication'); adj.columns=['item','text','cls','notes']; adj['cls']=adj.cls.astype(str).str.strip().str.upper()
key['final']=key.cons; key.loc[key.cons.isna(),'final']=key.item.map(adj.set_index('item').cls)
M['final']=M.id.map(key.set_index('id').final)
F={'final_dist':key.final.value_counts().to_dict(),'adjudicated':adj.cls.value_counts().to_dict()}
F['kappa_final_model1']=kappa(key.final.tolist(),key.model1.tolist())
F['confusion_model1_vs_final']=pd.crosstab(key.final,key.model1).to_dict()
M['final']=M.final.astype(object)
F['H6_final_human_labels']=run('final','human_final')
F['same_posts_model1']=run('model1','model1')
F['flips']=dict(model_DEESC_to_human_ESC=int(((M.model1=='DEESC')&(M.final=='ESC')).sum()),model_ESC_to_human_DEESC=int(((M.model1=='ESC')&(M.final=='DEESC')).sum()),model_signal_to_human_MIXED_or_OTHER=int((M.model1.isin(['ESC','DEESC'])&M.final.isin(['MIXED','OTHER'])).sum()))
# sensitivity: MIXED treated as DEESC-leaning? not pre-registered; report DEESC+MIXED pooled as exploratory
json.dump(F,open('results_human61_final.json','w'),indent=1,default=float); print(json.dumps(F,indent=1,default=float))
