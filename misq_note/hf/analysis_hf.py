import re,json,numpy as np,pandas as pd
d=pd.read_csv("raw/truth_archive.csv"); d["t"]=pd.to_datetime(d.created_at,utc=True); d=d[(d.t>="2026-03-01")&(d.t<"2026-10-14")].copy(); d["c"]=d.content.fillna("").str.lower()
d=d[~d.c.str.fullmatch(r"\s*rt:?\s*https?://\S+\s*")]
IR=re.compile(r"\biran"); TH=re.compile(r"attack|strik|bomb|destroy|obliterat|annihilat|wipe[sd]? out|blow(n)? up|kill|ultimatum|very hard"); PE=re.compile(r"\bdeal\b|ceasefire|cease-fire|agreement|peace|negotiat|\btalks\b|memorandum|reopen|\bopen\b")
d["N"]=d.c.apply(lambda s:bool(IR.search(s)) and bool(TH.search(s))); d["P"]=d.c.apply(lambda s:bool(IR.search(s)) and bool(PE.search(s))) & ~d.N
ev=d[d.N|d.P].sort_values("t").copy(); ev["typ"]=np.where(ev.N,"N","P"); ev["ep"]=ev.t.astype("int64")//10**9 if str(ev.t.dtype).endswith("ns, UTC]") else (ev.t.astype("int64")//10**9)
ev["ep"]=(ev.t-pd.Timestamp("1970-01-01",tz="UTC")).dt.total_seconds().astype(int)
# cluster filter: drop if another N/P post in prior 3h
keep=[];last=-10**12
for ep in ev.ep:
    keep.append(ep-last>=3*3600); last=ep
ev=ev[keep]; print("posts N:",int(d.N.sum()),"P:",int(d.P.sum()),"after cluster filter:",len(ev),ev.typ.value_counts().to_dict())
def load(n):
    b=pd.read_csv(f"raw/{n}_1h.csv").sort_values("t").reset_index(drop=True); b["r2"]=100*np.log(b.close.shift(-1)/b.open); b["cont"]=(b.t.shift(-1)-b.t)==3600; b.loc[~b.cont,"r2"]=np.nan; return b
ES=ev.ep.values
def reaction(b,ep):
    k=np.searchsorted(b.t.values,ep,side="right")-1
    if k<0 or ep>=b.t.values[k]+3600: return np.nan   # post not inside a bar
    return b.r2.iloc[k]
res={}; rng=np.random.default_rng(13)
for n in["CL","BZ","SPX","NDX","SOX","NVDA","UAL","XOM","KRW"]:
    b=load(n); bt=b.t.values
    # null bars: since 1 Mar, no N/P post within [-2h, +2h]
    post=b[(b.t>=pd.Timestamp("2026-03-02",tz="UTC").timestamp())&b.r2.notna()]
    dist=np.abs(post.t.values[:,None]-ES[None,:]).min(axis=1); null=post[dist>2*3600].r2.values
    out={"null_n":int(len(null)),"null_sd":float(null.std()),"null_mean_abs":float(np.abs(null).mean())}
    for typ in["N","P"]:
        r=np.array([reaction(b,ep) for ep in ev[ev.typ==typ].ep.values]); r=r[~np.isnan(r)]
        if len(r)==0: out[typ]=None; continue
        m=r.mean(); sim=np.array([rng.choice(null,len(r),replace=False).mean() for _ in range(5000)]); simabs=np.array([np.abs(rng.choice(null,len(r),replace=False)).mean() for _ in range(5000)])
        out[typ]=dict(n=int(len(r)),mean=float(m),median=float(np.median(r)),share_pos=float((r>0).mean()),p_two=float(np.mean(np.abs(sim-null.mean())>=abs(m-null.mean()))),mean_abs=float(np.abs(r).mean()),p_mag=float(np.mean(simabs>=np.abs(r).mean())),t_stat=float((m-null.mean())/(r.std(ddof=1)/np.sqrt(len(r)))) if len(r)>1 else None)
    res[n]=out
json.dump(res,open("results_hf.json","w"),indent=1)
for n,o in res.items():
    s=f"{n:5s} null sd={o['null_sd']:.2f}% n={o['null_n']} |"
    for typ in["N","P"]:
        v=o[typ]; s+=(f" {typ}: n={v['n']} mean={v['mean']:+.2f} share+={v['share_pos']:.2f} p={v['p_two']:.2f} |abs| {v['mean_abs']:.2f} (p={v['p_mag']:.2f}) |" if v else f" {typ}: none |")
    print(s)
ev[["t","typ"]].assign(oil=[reaction(load("CL"),e) for e in ev.ep]).round(2).to_csv("post_reactions_oil.csv",index=False)
