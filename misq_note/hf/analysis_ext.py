import re,json,sys,numpy as np,pandas as pd
from collections import Counter
rng=np.random.default_rng(23)
arch=pd.read_csv("raw/truth_archive.csv"); arch["t"]=pd.to_datetime(arch.created_at,utc=True); arch["id"]=arch.id.astype(str); T=arch.set_index("id").t
war=json.load(open("posts_coded.json")); ext=json.load(open("posts_ext_coder1.json")); samp={x["id"]:x["sample"] for x in json.load(open("posts_ext_to_code.json"))}; c2={x["id"]:x["cls"] for x in json.load(open("posts_all_coder2.json"))}
rows=[]
for x in war: rows.append(dict(id=x["id"],sample="W",c1=x["cls"],c2=c2.get(x["id"])))
for x in ext: rows.append(dict(id=x["id"],sample=samp[x["id"]],c1=x["cls"],c2=c2.get(x["id"])))
P=pd.DataFrame(rows); P["t"]=P.id.map(T); P=P.dropna(subset=["t"]).sort_values("t"); P["ep"]=(P.t-pd.Timestamp("1970-01-01",tz="UTC")).dt.total_seconds().astype(int)
P["period"]=np.where(P.t>=pd.Timestamp("2026-03-01",tz="UTC"),"war","pre")
# kappa
def kappa(a,b):
    cats=sorted(set(a)|set(b)); n=len(a); po=np.mean([x==y for x,y in zip(a,b)]); pe=sum((Counter(a)[c]/n)*(Counter(b)[c]/n) for c in cats); return (po-pe)/(1-pe),po
res={"n_posts":len(P)}
k,po=kappa(P.c1.tolist(),P.c2.tolist()); res["kappa_all"]=dict(kappa=float(k),agree=float(po),n=len(P))
for s in["W","A","B"]:
    q=P[P["sample"]==s]; kk,pp=kappa(q.c1.tolist(),q.c2.tolist()); res["kappa_"+s]=dict(kappa=float(kk),agree=float(pp),n=len(q))
# 3-class collapsed (ESC / DEESC / other incl. MIXED, OTHER)
col=lambda s:s if s in("ESC","DEESC") else "OTH"
kk,pp=kappa([col(x) for x in P.c1],[col(x) for x in P.c2]); res["kappa_collapsed"]=dict(kappa=float(kk),agree=float(pp))
def load(n):
    b=pd.read_csv(f"raw2y/{n}_1h.csv").sort_values("t").reset_index(drop=True); b["r2"]=100*np.log(b.close.shift(-1)/b.open); b["cont"]=(b.t.shift(-1)-b.t)==3600; b.loc[~b.cont,"r2"]=np.nan; return b
BARS={n:load(n) for n in["CL","BZ","SPX","NDX","SOX","NVDA","KRW","UAL"]}
def reaction(b,ep):
    k=np.searchsorted(b.t.values,ep,side="right")-1
    if k<0 or ep>=b.t.values[k]+3600: return np.nan
    return b.r2.iloc[k]
def run(coder):
    Q=P[P[coder].isin(["ESC","DEESC","MIXED"])].copy()
    keep=[];last=-10**12
    for ep in Q.ep: keep.append(ep-last>=3*3600); last=ep
    Q=Q[keep]; out={"n_signal":int(len(Q)),"by_sample":{s:Q[Q["sample"]==s][coder].value_counts().to_dict() for s in["W","A","B"]}}
    allep=P[P[coder].isin(["ESC","DEESC","MIXED"])].ep.values
    for var in["CL","BZ","SPX","NDX","NVDA","KRW"]:
        b=BARS[var]; o={}
        for per,(a,z) in{"pre":("2024-10-15","2026-02-27"),"war":("2026-03-02","2026-10-13")}.items():
            ta=pd.Timestamp(a,tz="UTC").timestamp(); tz_=pd.Timestamp(z,tz="UTC").timestamp()+86400
            post=b[(b.t>=ta)&(b.t<tz_)&b.r2.notna()]; dist=np.abs(post.t.values[:,None]-allep[None,:]).min(axis=1); null=post[dist>2*3600].r2.values
            for cls in["DEESC","ESC"]:
                for smp in["A","B","W","all"]:
                    q=Q[(Q.period==per)&(Q[coder]==cls)&((Q["sample"]==smp)|(smp=="all"))]
                    r=np.array([reaction(b,ep) for ep in q.ep.values]); r=r[~np.isnan(r)]
                    if len(r)<3: continue
                    m=r.mean(); sim=np.array([rng.choice(null,len(r),replace=False).mean() for _ in range(3000)])
                    o[f"{per}|{smp}|{cls}"]=dict(n=int(len(r)),mean=float(m),share_neg=float((r<0).mean()),p=float(np.mean(np.abs(sim-null.mean())>=abs(m-null.mean()))),null_sd=float(null.std()))
        out[var]=o
    # pooled WTI regression with sample FE, permutation of ESC/DEESC labels within sample
    b=BARS["CL"]; Q["r"]=[reaction(b,ep) for ep in Q.ep]; R=Q[Q[coder].isin(["ESC","DEESC"])&Q.r.notna()].copy(); R["D"]=(R[coder]=="DEESC").astype(float); R["E"]=1-R.D
    X=pd.get_dummies(R["sample"],dtype=float); 
    def fit(Dv):
        M=np.column_stack([Dv,1-Dv,X.values]); beta,*_=np.linalg.lstsq(M,R.r.values,rcond=None); return beta[0],beta[1]
    bD,bE=fit(R.D.values); sims=[]
    for _ in range(3000):
        perm=R.D.values.copy()
        for s in R["sample"].unique():
            idx=np.where(R["sample"].values==s)[0]; perm[idx]=rng.permutation(perm[idx])
        a,b2=fit(perm); sims.append(a-b2)
    out["pooled_WTI"]=dict(n=int(len(R)),beta_DEESC=float(bD),beta_ESC=float(bE),diff=float(bD-bE),p_perm_diff=float(np.mean(np.abs(sims)>=abs(bD-bE))),p_perm_DEESC_low=float(np.mean(np.array(sims)<=(bD-bE))))
    return out
res["coder1"]=run("c1"); res["coder2"]=run("c2")
P["agree"]=P.c1==P.c2; both=P.copy(); both["c_both"]=np.where(P.agree,P.c1,"DISAGREE"); P=both; res["coder_agree"]=run("c_both")
json.dump(res,open("results_ext.json","w"),indent=1)
print("kappa",{k:v for k,v in res.items() if k.startswith("kappa")})
for cod in["coder1","coder2","coder_agree"]:
    r=res[cod]; print(cod,"n signal",r["n_signal"],r["by_sample"]); 
    for var in["CL","BZ","SPX"]:
        for key,v in r[var].items(): print("  ",var,key,"n=%d mean=%+.2f share<0=%.2f p=%.3f"%(v["n"],v["mean"],v["share_neg"],v["p"]))
    print("  pooled WTI",r["pooled_WTI"])
