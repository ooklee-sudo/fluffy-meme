from lib import *
import json, sys, os, lib
NC=lambda: len(lib._cache)
H=6                       # free (sampled) steps after the planted prefix
OUT=os.environ.get("OUT","results_qwen3b.json")
rng_master=np.random.SeedSequence(20261004)
TG=np.geomspace(0.02,20,240)
def succ(c): return LET[(LET.index(c)+1)%26]

def run_traj(press,contam,m,T,rng,compounding=True):
    """history = A B + m planted B's (m=0: A B only). Returns per-step records."""
    hist=["A","B"]+["B"]*m if m>0 else ["A","B"]
    recs=[]
    for s in range(H):
        gold_hist=list(LET[:len(hist)]) if not compounding else hist
        ctx=gold_hist
        z=logits(press,contam,ctx)            # sampling logits (with pressure/contam text)
        v=logits(0,0,ctx)                     # clean-context reference, same history
        p=softmax(z,T); y=rng.choice(26,p=p)
        prev=ctx[-1]; target=succ(prev)
        recs.append(dict(y=int(y),ok=int(LET[y]==target),lock=int(LET[y]=="B" and m>0),
                         rep=int(LET[y]==prev),H=float(-(p*np.log(p+1e-12)).sum()),
                         v=v.copy()))
        if compounding: hist=hist+[LET[y]]
        else: hist=hist+[LET[y]]   # kept for bookkeeping; context uses gold prefix
    return recs

def teff(recs):
    ys=np.array([r["y"] for r in recs]); V=np.stack([r["v"] for r in recs])
    best=None; ll=[]
    for t in TG:
        Z=V/t; Z=Z-Z.max(1,keepdims=True); lp=Z-np.log(np.exp(Z).sum(1,keepdims=True))
        ll.append(lp[np.arange(len(ys)),ys].sum())
    ll=np.array(ll); i=int(ll.argmax())
    flat=bool(ll.max()-ll.min()<1.0)       # likelihood nearly flat -> T not identified
    return float(TG[i]),float(ll[i]/len(ys)),flat

def cell(press,contam,m,T,N,compounding=True,seed=0):
    ss=rng_master.spawn(1)[0]; rng=np.random.default_rng(ss)
    allrecs=[]; accs=[]; strict=[]
    for n in range(N):
        r=run_traj(press,contam,m,T,rng,compounding)
        allrecs+=r; accs.append(np.mean([x["ok"] for x in r]))
        strict.append(int([x["y"] for x in r]==[LET.index(c) for c in "CDEFGH"][:H]) if m>0 else int(all(x["ok"] for x in r)))
    te,ll,flat=teff(allrecs)
    return dict(press=press,contam=contam,m=m,T=T,N=N,compounding=compounding,
        acc=float(np.mean(accs)),acc_se=float(np.std(accs,ddof=1)/np.sqrt(N)),strict=float(np.mean(strict)),
        lock=float(np.mean([x["lock"] for x in allrecs])),rep=float(np.mean([x["rep"] for x in allrecs])),
        entropy=float(np.mean([x["H"] for x in allrecs])),Teff=te,Teff_minus_T=te-T,loglik=ll,Teff_flat=flat)

jobs=[]
if os.environ.get('EXTRA'):
    TS2=[0.15,0.4,0.8,1.2,1.6,2.0,2.5,3.0,4.0,5.0]
    for m in (2,3,4,6):
        for T in TS2: jobs.append((0,0,m,T,100,True))
    for m in (3,):
        for pc in ((1,0),(0,1),(1,1)):
            for T in (0.4,1.2,3.0): jobs.append((pc[0],pc[1],m,T,50,True))
else:
  pass
if not os.environ.get('EXTRA'):
  pass
TS=[0.15,0.4,0.8,1.2,2.0,3.0]
if not os.environ.get('EXTRA'):
  for m in (0,2,3,4,6):                      # block A: clean prompt, planted-attractor strength
    for T in TS: jobs.append((0,0,m,T,60 if T<=1.2 else 40,True))
if not os.environ.get('EXTRA'):
  for press,contam in ((1,0),(0,1),(1,1)):
    for m in (0,3):
        for T in (0.15,0.8,2.0): jobs.append((press,contam,m,T,30,True))
  for T in TS: jobs.append((0,0,0,T,60 if T<=1.2 else 40,False))
res=json.load(open(OUT)) if os.path.exists(OUT) else []
done={(r["press"],r["contam"],r["m"],r["T"],r["compounding"]) for r in res}
t0=time.time()
for j in jobs:
    if (j[0],j[1],j[2],j[3],j[5]) in done: continue
    r=cell(*j); res.append(r); json.dump(res,open(OUT,"w"),indent=1)
    print(f"{time.time()-t0:7.0f}s p{j[0]} c{j[1]} m{j[2]} T{j[3]} comp{int(j[5])} acc={r['acc']:.2f} lock={r['lock']:.2f} Teff={r['Teff']:.2f} cache={NC()}",flush=True)
print("DONE",flush=True)
