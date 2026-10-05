import json, numpy as np
from collections import Counter
A=json.load(open("analysis.json")); P=A["pairs"]; S=A["summary"]; R=json.load(open("regimes.json"))
MODELS=("qwen3b","llama3b"); TASKS=("alpha","months","planets","numbers"); CONDS=("pressure","contamination","both")
def counts(models,cond,k,two=True):
    sub=[p for p in P if p["model"] in models and p["cond"]==cond]
    c=Counter(p[k+"_flag"] for p in sub); n=len(sub)-(c["NI"] if k=="dT" else 0)
    return dict(up=c["up"],down=c["down"],none=c["none"],ni=c["NI"],n=n,det=c["up"]+c["down"])
def auc(models,cond,k):
    sub=[p for p in P if p["model"] in models and p["cond"]==cond]; return float(np.mean([p["auc_"+k] for p in sub]))
def sensitivity(scale,models=MODELS,cond="pressure"):
    MARGIN=dict(H=0.10,conf=0.05,ECE=0.10,SE=0.50,dT=0.50); out={}
    for k in ("H","conf","ECE","SE","dT"):
        d=0;n=0
        for p in P:
            if p["model"] in models and p["cond"]==cond:
                if k=="dT" and p["dT_ni"]: continue
                n+=1; delta=p[k]-p[k+"_clean"]; mg=MARGIN[k]*scale
                if (delta>=mg and p[k]>p[k+"_hi"]) or (delta<=-mg and p[k]<p[k+"_lo"]): d+=1
        out[k]=(d,n)
    return out
def blind_spot():
    rows=[]
    for model in MODELS:
        for task in TASKS:
            sticky=[x for x in R if x["model"]==model and x["task"]==task and x["level"]=="sticky"][0]["m"]
            c=[x for x in S if x["model"]==model and x["task"]==task and x["m"]==sticky and x["T"]==0.15 and not x["press"] and not x["contam"]]
            if c: rows.append((model,task,sticky,c[0]))
    return rows
def h3():
    diffs=[]
    for model in MODELS:
        for task in TASKS:
            for T in (0.8,2.0):
                a=[p for p in P if p["model"]==model and p["task"]==task and p["T"]==T and p["cond"]=="pressure"]
                b=[p for p in P if p["model"]==model and p["task"]==task and p["T"]==T and p["cond"]=="both"]
                if a and b and not a[0]["dT_ni"] and not b[0]["dT_ni"]: diffs.append((model,task,T,b[0]["dT"]-a[0]["dT"]))
    return diffs
if __name__=="__main__":
    for models in (("qwen3b",),("llama3b",),MODELS):
        for cond in CONDS:
            print(models,cond,{k:counts(models,cond,k) for k in ("H","conf","ECE","SE","dT")})
    for sc in (0.5,1,2): print("sens",sc,sensitivity(sc))
    for r in blind_spot(): print(r[0],r[1],r[2],{k:round(float(r[3][k]),2) for k in ("lock","H","conf","SE","ECE","dT")},r[3]["ref_sat"])
    d=h3(); print("H3 diffs",[round(x[3],2) for x in d],"mean",np.mean([x[3] for x in d]),"n>0.5",sum(x[3]>=0.5 for x in d),"n<-0.5",sum(x[3]<=-0.5 for x in d))
    print(Counter((r["level"],r["cls"]) for r in R))
