import json,numpy as np,pandas as pd
rng=np.random.default_rng(41)
S=pd.read_csv("paper_signal_posts.csv"); S["t"]=pd.to_datetime(S.t,utc=True,format="ISO8601")
def bars(n,folder="raw2y",suf="1h"):
    d=pd.read_csv(f"{folder}/{n}_{suf}.csv").sort_values("t").reset_index(drop=True); step=3600 if suf=="1h" else 300
    d["r2"]=100*np.log(d.close.shift(-1)/d.open); d["cont"]=(d.t.shift(-1)-d.t)==step; d.loc[~d.cont,"r2"]=np.nan; return d
def val(b,ep):
    k=np.searchsorted(b.t.values,ep,side="right")-1
    if k<0 or ep>=b.t.values[k]+3600: return np.nan
    return b.r2.iloc[k]
def flip_p(x,n=5000):
    x=np.array(x,float); x=x[~np.isnan(x)]
    if len(x)<4: return None,len(x)
    m=x.mean(); sim=np.abs(np.array([(x*rng.choice([-1,1],len(x))).mean() for _ in range(n)])); return float(np.mean(sim>=abs(m))),len(x)
res={}
# (i) other assets; sign mapping: ESC -> risk-off (ZN up, gold up, USD up, USD/CNH up); DEESC opposite
for asset in["ZN","GC","DXY","CNH"]:
    b=bars(asset); S["r_"+asset]=[val(b,e) for e in S.ep]
    sg=np.where(S.cls=="ESC",1,-1); S["e_"+asset]=S["r_"+asset]*sg
    for tp in["O","T"]:
        for cls in["ESC","DEESC"]:
            for rg in["low","high"]:
                x=S[(S.topic==tp)&(S.cls==cls)&(S.regime==rg)]["e_"+asset]; p,n=flip_p(x)
                res[f"{asset} {tp} {cls} {rg}"]=dict(n=n,mean=float(x.dropna().mean()) if n else None,p=p)
# Holm within each (tp,cls,rg) across the four assets
fam={}
for k,v in res.items():
    if v["p"] is None: continue
    a,rest=k.split(" ",1); fam.setdefault(rest,[]).append((k,v["p"]))
for rest,L in fam.items():
    L=sorted(L,key=lambda z:z[1]); m=len(L); run=0
    for i,(k,p) in enumerate(L): run=max(run,min(1,(m-i)*p)); res[k]["p_holm"]=run
# (ii) 5-minute subsample
five={}
for topic,asset in[("O","CL"),("T","ES")]:
    b=bars(asset,"raw5m","5m"); sub=S[(S.topic==topic)&(S.t>=pd.Timestamp("2026-08-05",tz="UTC"))]
    rows=[]
    for _,r in sub.iterrows():
        k=np.searchsorted(b.t.values,r.ep,side="right")-1; j=np.searchsorted(b.t.values,r.ep+3600,side="right")-1
        if k<0 or j<=k or abs(b.t.values[j]+300-(r.ep+3600))>600 or r.ep-b.t.values[k]>=300: continue
        ret=100*np.log(b.close.iloc[j]/b.open.iloc[k]); sgn=(1 if r.cls=="ESC" else -1)*(1 if topic=="O" else -1)
        rows.append(dict(t=str(r.t),cls=r.cls,typ=r.typ,ret=ret,e=ret*sgn))
    df=pd.DataFrame(rows); p,n=flip_p(df.e) if len(df) else (None,0)
    five[topic]=dict(n=int(len(df)),mean_directional=float(df.e.mean()) if len(df) else None,p=p,by_cls={c:dict(n=int((df.cls==c).sum()),mean_ret=float(df[df.cls==c].ret.mean())) for c in["ESC","DEESC"] if (df.cls==c).any()} if len(df) else {})
    df.to_csv(f"fivemin_{topic}.csv",index=False)
res["fivemin"]=five
json.dump(res,open("results_robust.json","w"),indent=1,default=float)
for k,v in res.items():
    if k=="fivemin": print("5-min",json.dumps(v,default=float)); continue
    if v["n"]>=4: print("%-26s n=%3d mean=%+.3f p=%.3f holm=%s"%(k,v["n"],v["mean"],v["p"],("%.3f"%v["p_holm"]) if "p_holm" in v else "-"))
