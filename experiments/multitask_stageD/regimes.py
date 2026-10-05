import json, numpy as np
from collections import defaultdict
def classify(rows):
    rows=sorted(rows,key=lambda r:r["T"]); T=[r["T"] for r in rows]; a=np.array([r["acc"] for r in rows]); se=np.array([r["acc_se"] for r in rows])
    k=int(a.argmax()); lo,hi=a[0],a[-1]
    if a.max()<0.10: return "floor",T[k],a[k]
    def sig(i,j): return abs(a[i]-a[j])>=0.10 and abs(a[i]-a[j])>=2*np.hypot(se[i],se[j])
    if 0<k<len(a)-1 and sig(k,0) and sig(k,len(a)-1): return "interior peak",T[k],a[k]
    if k==0 and sig(0,len(a)-1): return "decline",T[k],a[k]
    if k==len(a)-1 and sig(k,0): return "rise",T[k],a[k]
    if 0<k<len(a)-1 and sig(k,0) and not sig(k,len(a)-1): return "rise then plateau",T[k],a[k]
    if 0<k<len(a)-1 and sig(k,len(a)-1) and not sig(k,0): return "decline",T[k],a[k]
    return "flat",T[k],a[k]
def main():
    A=json.load(open("analysis.json"))["summary"]; out=[]
    for model in ("qwen3b","llama3b","qwen7b"):
        P=json.load(open(f"probe_{model}.json")) if __import__("os").path.exists(f"probe_{model}.json") else None
        if not P: continue
        for task in ("alpha","months","planets","numbers"):
            for lvl in ("weak","sticky","strong"):
                m=P[task][lvl]
                if not m: continue
                rows=[x for x in A if x["model"]==model and x["task"]==task and x["m"]==m and not x["press"] and not x["contam"]]
                if len(rows)<4: continue
                c,Tk,ak=classify(rows); out.append(dict(model=model,task=task,level=lvl,m=m,cls=c,Tpeak=Tk,accpeak=float(ak),Tmax=max(r["T"] for r in rows)))
    json.dump(out,open("regimes.json","w"),indent=1,default=float)
    for o in out: print(o["model"],o["task"],o["level"],o["m"],o["cls"],o["Tpeak"],round(o["accpeak"],2),"Tmax",o["Tmax"])
if __name__=="__main__": main()
