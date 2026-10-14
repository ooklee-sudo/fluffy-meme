"""After both human coders fill their sheets: python3 -I eval_human.py coderA.xlsx coderB.xlsx"""
import sys,json,numpy as np,pandas as pd
from collections import Counter
key=pd.read_csv("human_coding_key.csv")
def read(f): d=pd.read_excel(f,sheet_name="Coding"); d.columns=["item","text","cls","conf","notes"]; return d.set_index("item").cls.str.strip().str.upper()
a=read(sys.argv[1]); b=read(sys.argv[2]); key["hA"]=key.item.map(a); key["hB"]=key.item.map(b)
def kappa(x,y):
    cats=sorted(set(x)|set(y)); n=len(x); po=np.mean([i==j for i,j in zip(x,y)]); pe=sum((Counter(x)[c]/n)*(Counter(y)[c]/n) for c in cats); return (po-pe)/(1-pe),po
k=key.dropna(subset=["hA","hB"]); out={"n":len(k)}
for nm,(u,v) in{"humanA-humanB":("hA","hB"),"humanA-model1":("hA","model1"),"humanB-model1":("hB","model1"),"humanA-model2":("hA","model2"),"humanB-model2":("hB","model2"),"model1-model2":("model1","model2")}.items():
    kk,po=kappa(k[u].tolist(),k[v].tolist()); out[nm]=dict(kappa=round(float(kk),3),agree=round(float(po),3))
agree=k[k.hA==k.hB]; out["human_agreed_n"]=len(agree)
out["model1_accuracy_vs_human_consensus"]=round(float((agree.model1==agree.hA).mean()),3); out["model2_accuracy_vs_human_consensus"]=round(float((agree.model2==agree.hA).mean()),3)
for cls in["ESC","DEESC"]:
    sub=agree[agree.hA==cls]; out[f"{cls}_precision_model1"]=round(float((sub.model1==cls).mean()),3) if len(sub) else None
json.dump(out,open("results_human_eval.json","w"),indent=1); print(json.dumps(out,indent=1))
