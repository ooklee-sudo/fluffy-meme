import re,json,numpy as np,pandas as pd,statsmodels.api as sm
from scipy import stats
rng=np.random.default_rng(53)
arch=pd.read_csv("raw/truth_archive.csv"); arch["t"]=pd.to_datetime(arch.created_at,utc=True); arch["id"]=arch.id.astype(str); T=arch.set_index("id").t
def ep(t): return int((t-pd.Timestamp("1970-01-01",tz="UTC")).total_seconds())
# ---------- load coded posts: hold-out (F, C) and in-sample (O, T) with agreed labels
def hold(c):
    L=[]
    for tp in["F","C"]:
        for r in json.load(open(f"posts_holdout_coder{c}_{tp}.json")): r=dict(r); r["topic"]=tp; L.append(r)
    return pd.DataFrame(L).set_index(["id","topic"])
def insample(c):
    L=[]
    for i in range(1,5):
        tp={x["id"]:x["topic"] for x in json.load(open(f"posts_type_part{i}.json"))}
        for r in json.load(open(f"posts_type_coder{c}_part{i}.json")): r=dict(r); r["topic"]=tp[r["id"]]; L.append(r)
    return pd.DataFrame(L).set_index(["id","topic"])
a=pd.concat([hold(1),insample(1)]); b=pd.concat([hold(2),insample(2)]).reindex(a.index)
P=pd.DataFrame({"c1":a.cls,"c2":b.cls,"t1":a.typ,"t2":b.typ}).reset_index(); P["t"]=pd.to_datetime(T.reindex(P.id).values,utc=True); P=P.dropna(subset=["t","c1","c2"])
P["ep"]=P.t.map(ep); P["cls"]=np.where(P.c1==P.c2,P.c1,"DISAGREE"); P["typ"]=np.where(P.t1==P.t2,P.t1,"DISAGREE")
from collections import Counter
def kappa(x,y):
    cats=sorted(set(x)|set(y)); n=len(x); po=np.mean([i==j for i,j in zip(x,y)]); pe=sum((Counter(x)[c]/n)*(Counter(y)[c]/n) for c in cats); return float((po-pe)/(1-pe)),float(po)
res={"kappa":{tp:kappa(P[P.topic==tp].c1.tolist(),P[P.topic==tp].c2.tolist()) for tp in["F","C","O","T"]}}
# ---------- bars
def barload(n):
    d=pd.read_csv(f"raw2y/{n}_1h.csv").sort_values("t").reset_index(drop=True); d["r2"]=100*np.log(d.close.shift(-1)/d.open); d["cont"]=(d.t.shift(-1)-d.t)==3600; d.loc[~d.cont,"r2"]=np.nan
    d["pre2"]=100*np.log(d.close.shift(1)/d.open.shift(2)); d["cp"]=(d.t-d.t.shift(2))==7200; d.loc[~d.cp,"pre2"]=np.nan
    d["sd"]=d.r2.rolling(300,min_periods=100).std().shift(1); return d
ASSET={"O":"CL","T":"ES","F":"ZN","C":"CNH"}; SIGN={"O":{"ESC":1,"DEESC":-1},"T":{"ESC":-1,"DEESC":1},"F":{"ESC":-1,"DEESC":1},"C":{"ESC":1,"DEESC":-1}}
B={n:barload(n) for n in set(ASSET.values())|{"DXY","ES"}}
def val(n,e,col="r2"):
    bb=B[n]; k=np.searchsorted(bb.t.values,e,side="right")-1
    if k<2 or e>=bb.t.values[k]+3600: return np.nan
    return bb[col].iloc[k]
sig=P[P.cls.isin(["ESC","DEESC"])].sort_values("t").copy(); allsig=P[P.c1.isin(["ESC","DEESC","MIXED"])|P.c2.isin(["ESC","DEESC","MIXED"])]
keep=[];last={}
for _,r in sig.iterrows(): keep.append(r.ep-last.get(r.topic,-10**12)>=3*3600); last[r.topic]=r.ep
sig=sig[keep].copy()
sig["asset"]=sig.topic.map(ASSET); sig["r"]=[val(x,e) for x,e in zip(sig.asset,sig.ep)]; sig["sd"]=[val(x,e,"sd") for x,e in zip(sig.asset,sig.ep)]; sig["pre"]=[val(x,e,"pre2") for x,e in zip(sig.asset,sig.ep)]
sig["sgn"]=[SIGN[tp][c] for tp,c in zip(sig.topic,sig.cls)]; sig["e"]=sig.r*sig.sgn; sig["estd"]=sig.e/sig.sd; sig["epre"]=sig.pre*sig.sgn
n7=[];n24=[]
for _,r in sig.iterrows():
    prev=allsig[(allsig.topic==r.topic)&(allsig.ep<r.ep)]; n7.append(int((prev.ep>=r.ep-7*86400).sum())); n24.append(int((prev.ep>=r.ep-86400).sum()))
sig["n7"]=n7; sig["n24"]=n24; sig["A"]=np.log1p(sig.n7)
res["n_signal"]={tp:int((sig.topic==tp).sum()) for tp in["F","C","O","T"]}; res["cells"]={f"{tp} {c}":dict(n=int(((sig.topic==tp)&(sig.cls==c)).sum()),mean_e=float(sig[(sig.topic==tp)&(sig.cls==c)].e.mean()),mean_estd=float(sig[(sig.topic==tp)&(sig.cls==c)].estd.mean())) for tp in["F","C","O","T"] for c in["ESC","DEESC"] if ((sig.topic==tp)&(sig.cls==c)).any()}
def reg(d,label,extra=[]):
    d=d.dropna(subset=["estd","A","n24"]); X=pd.get_dummies(d.topic,dtype=float,drop_first=True)
    X["A"]=d.A; X["n24"]=d.n24; X["DEESC"]=(d.cls=="DEESC").astype(float)
    for z in extra: X[z]=d[z]
    m=sm.OLS(d.estd.values,sm.add_constant(X).astype(float).values).fit(cov_type="HC1"); nm=["const"]+list(X.columns); out={"n":int(len(d))}
    for i,k in enumerate(nm):
        if k in("A","n24","DEESC")+tuple(extra): out[k]=dict(coef=float(m.params[i]),se=float(m.bse[i]),p_two=float(m.pvalues[i]),p_one_pos=float(stats.norm.sf(m.params[i]/m.bse[i])))
    res[label]=out
reg(sig[sig.topic.isin(["F","C"])],"S1S2 confirmatory (hold-out F,C)")
reg(sig[sig.topic.isin(["O","T"])],"S1S2 exploratory (in-sample O,T)")
reg(sig,"S1S2 all four topics")
d=sig.copy(); d["ACTION"]=(d.typ=="ACTION").astype(float); d=d[d.typ.isin(["ACTION","RHETORIC"])]
reg(d[d.topic.isin(["F","C"])],"S3 hold-out (ACTION dummy)",["ACTION"]); reg(d,"S3 all topics (ACTION dummy)",["ACTION"])
# S4 placebo: OTHER posts' standardized absolute reaction vs n7
oth=P[(P.cls=="OTHER")&(P.c1=="OTHER")&(P.c2=="OTHER")].copy(); oth["asset"]=oth.topic.map(ASSET); oth["r"]=[val(x,e) for x,e in zip(oth.asset,oth.ep)]; oth["sd"]=[val(x,e,"sd") for x,e in zip(oth.asset,oth.ep)]
oth["absz"]=(oth.r/oth.sd).abs(); oth["n7"]=[int(((allsig.topic==r.topic)&(allsig.ep<r.ep)&(allsig.ep>=r.ep-7*86400)).sum()) for _,r in oth.iterrows()]; oth["A"]=np.log1p(oth.n7)
oo=oth.dropna(subset=["absz"]); X=pd.get_dummies(oo.topic,dtype=float,drop_first=True); X["A"]=oo.A; m=sm.OLS(oo.absz.values,sm.add_constant(X).astype(float).values).fit(cov_type="HC1")
res["S4 placebo OTHER: |z| on A"]=dict(n=int(len(oo)),coef=float(m.params[-1]),p=float(m.pvalues[-1]))
res["pre-window directional (placebo)"]={tp:float(sig[sig.topic==tp].epre.mean()) for tp in["F","C","O","T"]}
json.dump(res,open("results_holdout.json","w"),indent=1,default=float); sig.to_csv("holdout_signal_posts.csv",index=False)
print(json.dumps({k:res[k] for k in["kappa","n_signal","cells"]},indent=1,default=float))
for k in res:
    if k.startswith("S") or k.startswith("pre"): print(k,json.dumps(res[k],default=float)[:420])
