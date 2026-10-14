import re,json,glob,numpy as np,pandas as pd
from collections import Counter
rng=np.random.default_rng(31)
arch=pd.read_csv("raw/truth_archive.csv"); arch["t"]=pd.to_datetime(arch.created_at,utc=True); arch["id"]=arch.id.astype(str); T=arch.set_index("id").t
def load(c):
    L=[]
    for i in range(1,5):
        tp={x["id"]:x["topic"] for x in json.load(open(f"posts_type_part{i}.json"))}
        for r in json.load(open(f"posts_type_coder{c}_part{i}.json")): r=dict(r); r["topic"]=tp[r["id"]]; L.append(r)
    D=pd.DataFrame(L); D["key"]=D.id+"|"+D.topic; return D.set_index("key")
a=load(1); b=load(2); P=pd.DataFrame({"id":a.id,"topic":a.topic}); P["c1"]=a.cls; P["c2"]=b.cls.reindex(P.index); P["t1"]=a.typ; P["t2"]=b.typ.reindex(P.index); P["t"]=pd.to_datetime(T.reindex(P.id).values,utc=True); P=P.dropna(subset=["t","c1","c2"])
P["ep"]=(P.t-pd.Timestamp("1970-01-01",tz="UTC")).dt.total_seconds().astype(int)
def kappa(x,y):
    cats=sorted(set(x)|set(y)); n=len(x); po=np.mean([i==j for i,j in zip(x,y)]); pe=sum((Counter(x)[c]/n)*(Counter(y)[c]/n) for c in cats); return float((po-pe)/(1-pe)),float(po)
res={"n":len(P),"by_topic":P.topic.value_counts().to_dict()}
res["kappa_cls"]={tp:kappa(P[P.topic==tp].c1.tolist(),P[P.topic==tp].c2.tolist()) for tp in["O","T"]}; res["kappa_cls_all"]=kappa(P.c1.tolist(),P.c2.tolist())
S=P[P.c1.isin(["ESC","DEESC"])&P.c2.isin(["ESC","DEESC"])]; res["kappa_typ_on_signal_both"]=kappa(S.t1.tolist(),S.t2.tolist())
P["cls"]=np.where(P.c1==P.c2,P.c1,"DISAGREE"); P["typ"]=np.where(P.t1==P.t2,P.t1,"DISAGREE")
liberation=pd.Timestamp("2025-04-03",tz="UTC"); war0=pd.Timestamp("2026-03-01",tz="UTC")
P["regime"]=np.where(P.topic=="O",np.where(P.t>=war0,"high","low"),np.where(P.t>=liberation,"high","low"))   # high K: war / post-Liberation Day
P["asset"]=np.where(P.topic=="O","CL","ES")
def barload(n):
    d=pd.read_csv(f"raw2y/{n}_1h.csv").sort_values("t").reset_index(drop=True); d["r2"]=100*np.log(d.close.shift(-1)/d.open); d["cont"]=(d.t.shift(-1)-d.t)==3600; d.loc[~d.cont,"r2"]=np.nan
    d["pre2"]=100*np.log(d.close.shift(1)/d.open.shift(2)); d["cp"]=(d.t-d.t.shift(2))==7200; d.loc[~d.cp,"pre2"]=np.nan; return d
BARS={n:barload(n) for n in["CL","ES"]}
def val(n,ep,col="r2"):
    b=BARS[n]; k=np.searchsorted(b.t.values,ep,side="right")-1
    if k<2 or ep>=b.t.values[k]+3600: return np.nan
    return b[col].iloc[k]
sig=P[P.cls.isin(["ESC","DEESC"])].sort_values("t").copy()   # agreed signal posts
allsig=P[P.c1.isin(["ESC","DEESC","MIXED"])|P.c2.isin(["ESC","DEESC","MIXED"])]
# cluster filter within topic: drop posts within 3h of a previous signal post of the same topic
keep=[]; last={}
for _,r in sig.iterrows():
    keep.append(r.ep-last.get(r.topic,-10**12)>=3*3600); last[r.topic]=r.ep
sig=sig[keep].copy()
sig["r"]=[val(a_,e) for a_,e in zip(sig.asset,sig.ep)]; sig["pre"]=[val(a_,e,"pre2") for a_,e in zip(sig.asset,sig.ep)]
# directional effect: positive = in the expected direction (oil: ESC up, DEESC down; ES: ESC down, DEESC up)
sgn=np.where(sig.topic=="O",np.where(sig.cls=="ESC",1,-1),np.where(sig.cls=="ESC",-1,1)); sig["e"]=sig.r*sgn; sig["epre"]=sig.pre*sgn
# learning variables
allt=P[P.c1.isin(["ESC","DEESC","MIXED"])|P.c2.isin(["ESC","DEESC","MIXED"])]
nprev=[];gap=[]
for _,r in sig.iterrows():
    prev=allt[(allt.topic==r.topic)&(allt.ep<r.ep)]; w=prev[prev.ep>=r.ep-86400]; nprev.append(len(w)); gap.append(min((r.ep-prev.ep.max())/3600,168) if len(prev) else 168)
sig["nprev24"]=nprev; sig["gap"]=gap
def perm_diff(x,y,n=5000):
    x=np.array(x,float);y=np.array(y,float); x=x[~np.isnan(x)]; y=y[~np.isnan(y)]
    if len(x)<3 or len(y)<3: return None
    d=x.mean()-y.mean(); z=np.concatenate([x,y]); sim=[]
    for _ in range(n): rng.shuffle(z); sim.append(z[:len(x)].mean()-z[len(x):].mean())
    return dict(n1=len(x),n2=len(y),mean1=float(x.mean()),mean2=float(y.mean()),diff=float(d),p=float(np.mean(np.abs(sim)>=abs(d))))
out={}
# cell means
for tp in["O","T"]:
    for cls in["ESC","DEESC"]:
        for rg in["low","high"]:
            s=sig[(sig.topic==tp)&(sig.cls==cls)&(sig.regime==rg)]; r=s.r.dropna()
            out[f"cell {tp} {cls} {rg}"]=dict(n=int(len(r)),mean_reaction=float(r.mean()) if len(r) else None,mean_directional=float(s.e.dropna().mean()) if len(r) else None,mean_pre=float(s.epre.dropna().mean()) if len(r) else None)
# T1/T2: state dependence
for tp in["O","T"]:
    out[f"{tp}: DEESC high vs low (directional)"]=perm_diff(sig[(sig.topic==tp)&(sig.cls=="DEESC")&(sig.regime=="high")].e,sig[(sig.topic==tp)&(sig.cls=="DEESC")&(sig.regime=="low")].e)
    out[f"{tp}: ESC low vs high (directional)"]=perm_diff(sig[(sig.topic==tp)&(sig.cls=="ESC")&(sig.regime=="low")].e,sig[(sig.topic==tp)&(sig.cls=="ESC")&(sig.regime=="high")].e)
# T4 type
for tp in["O","T","all"]:
    s=sig if tp=="all" else sig[sig.topic==tp]
    out[f"type {tp}: ACTION vs RHETORIC (directional)"]=perm_diff(s[s.typ=="ACTION"].e,s[s.typ=="RHETORIC"].e)
# T3 learning
import statsmodels.api as sm
d=sig.dropna(subset=["e"]).copy(); d["lgap"]=np.log1p(d.gap); d["topic_dir"]=d.topic+d.cls
X=pd.get_dummies(d.topic_dir,dtype=float,drop_first=True); X["nprev24"]=d.nprev24; X["lgap"]=d.lgap
m=sm.OLS(d.e.values,sm.add_constant(X).astype(float).values).fit(cov_type="HC1"); names=["const"]+list(X.columns)
out["learning (pooled OLS, directional effect)"]={nm:dict(coef=float(m.params[i]),p=float(m.pvalues[i])) for i,nm in enumerate(names) if nm in("nprev24","lgap")}; out["learning n"]=int(len(d))
# placebo: pre-post-window directional move (should be ~0) and OTHER posts
out["pre-window directional (placebo)"]={k:float(sig[sig.topic==k].epre.dropna().mean()) for k in["O","T"]}
oth=P[(P.cls=="OTHER")&(P.c1=="OTHER")&(P.c2=="OTHER")].copy(); oth["asset"]=np.where(oth.topic=="O","CL","ES"); oth["r"]=[val(a_,e) for a_,e in zip(oth.asset,oth.ep)]
out["OTHER posts mean |r| vs signal |r|"]={tp:dict(other=float(oth[oth.topic==tp].r.abs().mean()),signal=float(sig[sig.topic==tp].r.abs().mean())) for tp in["O","T"]}
res["tests"]=out; res["n_signal_after_filter"]={tp:int((sig.topic==tp).sum()) for tp in["O","T"]}
json.dump(res,open("results_paper.json","w"),indent=1,default=float); sig.to_csv("paper_signal_posts.csv",index=False)
print(json.dumps({k:res[k] for k in["n","by_topic","kappa_cls","kappa_cls_all","kappa_typ_on_signal_both","n_signal_after_filter"]},indent=1))
for k,v in out.items(): print(k,"->",json.dumps(v,default=float)[:260])
