import sys, json
from core import *
name=sys.argv[1]; B=get_backend(name); out={}
for task in TASKS:
    items=TASKS[task]["items"]; res={}
    for m in (1,2,3,4,6,8,12,16,24,32,48,64):
        hist=history(task,m); z=B.logits(task,0,0,hist)
        res[m]={T:float(softmax(z,T)[2]) for T in (0.15,0.8,2.0)}
    sticky=next((m for m in res if res[m][0.15]<0.05),None)
    weak=max([m for m in res if sticky and m<sticky and res[m][0.15]>0.95],default=None) if sticky else None
    ms=sorted(res)
    strong=next((m for m in ms if sticky and m>=2*sticky),None)
    out[task]=dict(p_correct={str(m):v for m,v in res.items()},sticky=sticky,weak=weak,strong=strong)
    print(name,task,"weak",weak,"sticky",sticky,"strong",strong,{m:round(res[m][0.15],2) for m in (1,2,4,8,16,32,64)},flush=True)
json.dump(out,open(f"probe_{name}.json","w"),indent=1)
