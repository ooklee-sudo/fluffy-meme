import sys, json, os, time
from core import *
name=sys.argv[1]; B=get_backend(name); probe=json.load(open(f"probe_{name}.json"))
t0=time.time()
for task in ("alpha","months","planets","numbers"):
    fn=f"cells_{name}_{task}.json"
    done=json.load(open(fn)) if os.path.exists(fn) else []
    key=lambda c:(c["press"],c["contam"],c["m"],c["T"])
    have={key(c) for c in done}
    pr=probe[task]; ms=[m for m in (pr["weak"],pr["sticky"],pr["strong"]) if m]
    jobs=[(0,0,m,T) for m in ms for T in (0.15,0.8,1.2,2.0,3.0)]
    jobs+=[(0,0,0,T) for T in (0.15,2.0)]
    if pr["sticky"]:
        jobs+=[(p,c,pr["sticky"],T) for (p,c) in ((1,0),(0,1),(1,1)) for T in (0.8,2.0)]
    for j in jobs:
        if j in have: continue
        c=run_cell(B,task,*j); done.append(c); json.dump(done,open(fn,"w"))
        acc=np.mean([s["ok"] for t in c["trajs"] for s in t])
        print(f"{time.time()-t0:6.0f}s {name} {task} p{j[0]}c{j[1]} m{j[2]} T{j[3]} acc={acc:.2f} cache={len(B.cache)}",flush=True)
print("DONE",name,flush=True)
