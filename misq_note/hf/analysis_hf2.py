import re,json,numpy as np,pandas as pd
exec(open("analysis_hf.py").read().split("ev=d[d.N|d.P]")[0])
cod={x["id"]:x for x in json.load(open("posts_coded.json"))}
allp=d[d.N|d.P].copy(); allp["cls"]=allp.id.astype(str).map(lambda i:cod[i]["cls"]); allp["conf"]=allp.id.astype(str).map(lambda i:cod[i]["conf"])
allp["ep"]=(allp.t-pd.Timestamp("1970-01-01",tz="UTC")).dt.total_seconds().astype(int)
sig=allp[allp.cls.isin(["ESC","DEESC","MIXED"])].sort_values("t")
keep=[];last=-10**12
for ep in sig.ep: keep.append(ep-last>=3*3600); last=ep
ev=sig[keep]; print("coded signal posts:",len(sig),"after cluster filter:",len(ev),ev.cls.value_counts().to_dict())
ES=sig.ep.values
def load(n):
    b=pd.read_csv(f"raw/{n}_1h.csv").sort_values("t").reset_index(drop=True); b["r2"]=100*np.log(b.close.shift(-1)/b.open); b["cont"]=(b.t.shift(-1)-b.t)==3600; b.loc[~b.cont,"r2"]=np.nan; return b
def reaction(b,ep):
    k=np.searchsorted(b.t.values,ep,side="right")-1
    if k<0 or ep>=b.t.values[k]+3600: return np.nan
    return b.r2.iloc[k]
res={}; rng=np.random.default_rng(17)
for n in["CL","BZ","SPX","NDX","SOX","NVDA","UAL","XOM","KRW"]:
    b=load(n); post=b[(b.t>=pd.Timestamp("2026-03-02",tz="UTC").timestamp())&b.r2.notna()]
    dist=np.abs(post.t.values[:,None]-ES[None,:]).min(axis=1); null=post[dist>2*3600].r2.values; out={"null_n":int(len(null)),"null_sd":float(null.std())}
    for cls in["ESC","DEESC","MIXED"]:
        r=np.array([reaction(b,ep) for ep in ev[ev.cls==cls].ep.values]); r=r[~np.isnan(r)]
        if len(r)<3: out[cls]=dict(n=int(len(r))); continue
        m=r.mean(); sim=np.array([rng.choice(null,len(r),replace=False).mean() for _ in range(5000)]); simabs=np.array([np.abs(rng.choice(null,len(r),replace=False)).mean() for _ in range(5000)])
        out[cls]=dict(n=int(len(r)),mean=float(m),median=float(np.median(r)),share_pos=float((r>0).mean()),p_two=float(np.mean(np.abs(sim-null.mean())>=abs(m-null.mean()))),mean_abs=float(np.abs(r).mean()),p_mag=float(np.mean(simabs>=np.abs(r).mean())),null_mean=float(null.mean()))
    res[n]=out
json.dump(res,open("results_hf2.json","w"),indent=1)
for n,o in res.items():
    s=f"{n:5s} sd0={o['null_sd']:.2f} |"
    for cls in["ESC","DEESC","MIXED"]:
        v=o[cls]; s+=(f" {cls}: n={v['n']} mean={v['mean']:+.2f} share+={v['share_pos']:.2f} p={v['p_two']:.3f} |abs|={v['mean_abs']:.2f} (p={v['p_mag']:.2f}) |" if "mean" in v else f" {cls}: n={v['n']} |")
    print(s)
b=load("CL"); ev=ev.assign(oil=[reaction(b,e) for e in ev.ep]); ev[["t","cls","conf","oil"]].to_csv("post_reactions_oil_coded.csv",index=False)
print(ev.sort_values("oil")[["t","cls","oil"]].head(6).to_string(index=False)); print(ev.sort_values("oil")[["t","cls","oil"]].tail(6).to_string(index=False))
