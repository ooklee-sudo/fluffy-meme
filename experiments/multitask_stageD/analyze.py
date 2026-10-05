import json, glob, os, numpy as np
from core import TASKS, softmax
TG=np.geomspace(0.02,20,240)
MODELS=["qwen3b","llama3b","qwen7b"]; TASKN=["alpha","months","planets","numbers"]
rng=np.random.default_rng(7)

def traj_ll(c):
    """per-trajectory log-likelihood over the T grid (traj x grid) under the clean-context reference"""
    out=np.zeros((len(c["trajs"]),len(TG)))
    for i,t in enumerate(c["trajs"]):
        for s in t:
            v=np.array(s["v"]); 
            Z=v[None,:]/TG[:,None]; Z=Z-Z.max(1,keepdims=True); lp=Z-np.log(np.exp(Z).sum(1,keepdims=True))
            out[i]+=lp[:,s["y"]]
    return out
def teff_from(LL,idx):
    ll=LL[idx].sum(0); return float(TG[ll.argmax()])
def ece(py,ok,nb=5):
    py=np.array(py); ok=np.array(ok,float); e=0.0
    for b in range(nb):
        lo,hi=b/nb,(b+1)/nb
        m=(py>=lo)&((py<hi) if b<nb-1 else (py<=hi))
        if m.sum(): e+=m.mean()*abs(ok[m].mean()-py[m].mean())
    return float(e)
def sem_entropy(c):
    from collections import Counter
    cnt=Counter(tuple(s["y"] for s in t) for t in c["trajs"]); n=sum(cnt.values())
    p=np.array(list(cnt.values()))/n; return float(-(p*np.log(p)).sum())
def indicators(c,LL,idx=None):
    tr=c["trajs"] if idx is None else [c["trajs"][i] for i in idx]
    steps=[s for t in tr for s in t]
    d=dict(acc=np.mean([s["ok"] for s in steps]),
           H=np.mean([s["ent"] for s in steps]),
           conf=np.mean([s["py"] for s in steps]),
           ECE=ece([s["py"] for s in steps],[s["ok"] for s in steps]))
    cc=dict(c); cc["trajs"]=tr; d["SE"]=sem_entropy(cc)
    ii=np.arange(len(c["trajs"])) if idx is None else np.array(idx)
    d["Teff"]=teff_from(LL,ii); d["dT"]=d["Teff"]-c["T"]
    return d
def cellsum(c,LL):
    d=indicators(c,LL); steps=[s for t in c["trajs"] for s in t]
    pt=[np.mean([s['ok'] for s in t]) for t in c['trajs']]; d['acc_se']=float(np.std(pt,ddof=1)/np.sqrt(len(pt)))
    d.update(strict=np.mean([int(len(t)==6 and all(s["ok"] for s in t) and t[0]["y"]==2) for t in c["trajs"]]),
             lock=np.mean([s["lock"] for s in steps]),rep=np.mean([s["rep"] for s in steps]))
    # not identified if the reference is saturated on the chosen items
    refp=[]
    for t in c["trajs"]:
        for s in t:
            v=np.array(s["v"]); refp.append(softmax(v,c["T"])[s["y"]])
    d["ref_sat"]=bool(np.mean(refp)>0.999 or d["Teff"]<=TG[0]*1.001)
    return d
def ci_boot(c,LL,B=300):
    n=len(c["trajs"]); res={k:[] for k in ("H","conf","ECE","SE","dT")}
    for _ in range(B):
        idx=rng.integers(0,n,n); d=indicators(c,LL,idx)
        for k in res: res[k].append(d[k])
    return {k:(float(np.percentile(v,2.5)),float(np.percentile(v,97.5))) for k,v in res.items()}

MARGIN=dict(H=0.10,conf=0.05,ECE=0.10,SE=0.50,dT=0.50)
def auc2(x,y):
    """two-sided AUROC (Mann-Whitney U / (n*m)), ties count one half"""
    x=np.asarray(x,float); y=np.asarray(y,float)
    gt=(x[:,None]>y[None,:]).sum()+0.5*(x[:,None]==y[None,:]).sum()
    a=gt/(len(x)*len(y)); return float(max(a,1-a))
def main():
    allcells={}; summary=[]; pairs=[]
    for mname in MODELS:
        for task in TASKN:
            fn=f"cells_{mname}_{task}.json"
            if not os.path.exists(fn): continue
            cells=json.load(open(fn)); LLs=[traj_ll(c) for c in cells]
            by={(c["press"],c["contam"],c["m"],c["T"]):(c,L) for c,L in zip(cells,LLs)}
            pr=json.load(open(f"probe_{mname}.json"))[task]
            for (p,cn,m,T),(c,L) in by.items():
                d=cellsum(c,L); d.update(model=mname,task=task,press=p,contam=cn,m=m,T=T,N=c["N"]); summary.append(d)
            sticky=pr["sticky"]
            if sticky:
                for T in (0.8,2.0):
                    base=by.get((0,0,sticky,T))
                    if not base: continue
                    ci=ci_boot(*base); bd=cellsum(*base)
                    for (p,cn,name) in ((1,0,"pressure"),(0,1,"contamination"),(1,1,"both")):
                        o=by.get((p,cn,sticky,T))
                        if not o: continue
                        od=cellsum(*o); rec=dict(model=mname,task=task,T=T,m=sticky,cond=name)
                        for k in ("H","conf","ECE","SE","dT"):
                            rec[k]=od[k]; rec[k+"_clean"]=bd[k]
                            delta=od[k]-bd[k]; mg=MARGIN[k]
                            if k=="dT" and (bd["ref_sat"] or od["ref_sat"]): fl="NI"
                            elif delta>=mg and od[k]>ci[k][1]: fl="up"
                            elif delta<=-mg and od[k]<ci[k][0]: fl="down"
                            else: fl="none"
                            rec[k+"_flag"]=fl; rec[k+"_lo"]=ci[k][0]; rec[k+"_hi"]=ci[k][1]; rec[k+"_ni"]=bool(k=="dT" and (bd["ref_sat"] or od["ref_sat"]))
                            rec["clean_sat"]=bool(bd["ref_sat"]); rec["dist_sat"]=bool(od["ref_sat"])
                        # trajectory-level separability (two-sided AUROC) pressured vs clean
                        cb,Lb=base; co,Lo=o
                        def per(c,L):
                            r={"H":[],"conf":[],"gap":[],"Teff":[]}
                            for i,t in enumerate(c["trajs"]):
                                r["H"].append(np.mean([s["ent"] for s in t])); r["conf"].append(np.mean([s["py"] for s in t]))
                                r["gap"].append(abs(np.mean([s["py"] for s in t])-np.mean([s["ok"] for s in t])))
                                r["Teff"].append(float(TG[L[i].argmax()]))
                            return r
                        pb,po=per(cb,Lb),per(co,Lo)
                        for k in pb: rec["auc_"+k]=auc2(po[k],pb[k])
                        pairs.append(rec)
    json.dump(dict(summary=summary,pairs=pairs),open("analysis.json","w"),indent=1,default=float)
    print(len(summary),"cells",len(pairs),"pairs")
if __name__=="__main__": main()
