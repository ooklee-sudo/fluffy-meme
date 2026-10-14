import json,numpy as np,pandas as pd,statsmodels.api as sm
from scipy import stats
from collections import Counter
arch=pd.read_csv("raw/truth_archive.csv"); arch["t"]=pd.to_datetime(arch.created_at,utc=True); arch["id"]=arch.id.astype(str); T=arch.set_index("id").t
base=pd.DataFrame(json.load(open("posts_oot.json")))[["id","topic"]]
def ld(f): 
    d=pd.DataFrame(json.load(open(f)))
    if "topic" not in d: raise SystemExit("coder file lacks topic: "+f)
    return d.set_index(["id","topic"])
a=ld("posts_oot_coder1.json"); b=ld("posts_oot_coder2.json")
P=base.set_index(["id","topic"]); P["c1"]=a.cls; P["t1"]=a.typ; P["c2"]=b.cls; P["t2"]=b.typ; P=P.reset_index()
P["t"]=pd.to_datetime(T.reindex(P.id).values,utc=True); P=P.dropna(subset=["c1","c2","t"])
def kappa(x,y):
    cats=sorted(set(x)|set(y)); n=len(x); po=np.mean([i==j for i,j in zip(x,y)]); pe=sum((Counter(x)[c]/n)*(Counter(y)[c]/n) for c in cats); return float((po-pe)/(1-pe)),float(po)
res={"n_rows":len(P),"kappa":{tp:kappa(P[P.topic==tp].c1.tolist(),P[P.topic==tp].c2.tolist()) for tp in["O","T"]}}
P["cls"]=np.where(P.c1==P.c2,P.c1,"DISAGREE"); P["typ"]=np.where(P.t1==P.t2,P.t1,"DISAGREE"); P["ep"]=P.t.map(lambda x:int((x-pd.Timestamp("1970-01-01",tz="UTC")).total_seconds()))
# daily returns
oil=pd.read_csv("rawd/DCOILWTICO.csv",parse_dates=["observation_date"]).set_index("observation_date").iloc[:,0].replace(".",np.nan).astype(float).dropna(); oil=oil[oil>0]
spx=pd.read_csv("rawd/GSPC_daily.csv",index_col=0,parse_dates=True).iloc[:,0]
R={"O":100*np.log(oil).diff().dropna(),"T":100*np.log(spx).diff().dropna()}; SD={k:v.rolling(20).std().shift(1) for k,v in R.items()}
SIGN={"O":{"ESC":1,"DEESC":-1},"T":{"ESC":-1,"DEESC":1}}
def reaction_day(t,idx):
    et=t.tz_convert("America/New_York"); d=et.tz_localize(None).normalize()
    after=(et.hour>16) or (et.hour==16 and et.minute>0)
    cand=idx[idx>=d] if not after else idx[idx>d]
    return cand[0] if len(cand) else pd.NaT
rows=[]
for _,r in P.iterrows():
    idx=R[r.topic].index; d=reaction_day(r.t,idx)
    rows.append((d,R[r.topic].get(d,np.nan),SD[r.topic].get(d,np.nan)))
P["day"]=[x[0] for x in rows]; P["r"]=[x[1] for x in rows]; P["sd"]=[x[2] for x in rows]
P=P[(P.t>=pd.Timestamp("2022-02-14",tz="UTC"))&(P.t<pd.Timestamp("2024-10-14",tz="UTC"))]
nonoth=P[P.c1.isin(["ESC","DEESC","MIXED"])|P.c2.isin(["ESC","DEESC","MIXED"])]
def lag_feats(df):
    n24=[];gap=[]
    for _,r in df.iterrows():
        prev=nonoth[(nonoth.topic==r.topic)&(nonoth.ep<r.ep)]; n24.append(int((prev.ep>=r.ep-86400).sum())); gap.append(min((r.ep-prev.ep.max())/3600,168) if len(prev) else 168)
    return n24,gap
S=P[P.cls.isin(["ESC","DEESC"])].copy(); S["sgn"]=[SIGN[tp][c] for tp,c in zip(S.topic,S.cls)]; S["e"]=S.r*S.sgn; S["estd"]=S.e/S.sd
S["n24"],S["gap"]=lag_feats(S); S["lgap"]=np.log1p(S.gap); S["first"]=(S.gap>=24).astype(float); S["year"]=S.t.dt.year
res["n_signal"]={tp:int((S.topic==tp).sum()) for tp in["O","T"]}; res["cells"]={f"{tp} {c}":dict(n=int(((S.topic==tp)&(S.cls==c)).sum()),mean_estd=float(S[(S.topic==tp)&(S.cls==c)].estd.mean())) for tp in["O","T"] for c in["ESC","DEESC"] if ((S.topic==tp)&(S.cls==c)).any()}
def fit(d,cols,label):
    d=d.dropna(subset=["estd"]); X=pd.get_dummies(d.topic+d.cls,dtype=float,drop_first=True)
    for c in cols: X[c]=d[c].astype(float)
    Xm=sm.add_constant(X).astype(float); m=sm.OLS(d.estd.values,Xm.values).fit(cov_type="cluster",cov_kwds={"groups":pd.factorize(d.day.astype(str))[0]}); nm=list(Xm.columns); out={"n":int(len(d)),"n_days":int(d.day.nunique())}
    for c in cols:
        i=nm.index(c); out[c]=dict(coef=float(m.params[i]),se=float(m.bse[i]),p_two=float(m.pvalues[i]),p_one_neg=float(stats.norm.cdf(m.params[i]/m.bse[i])),mde80=float(2.8*m.bse[i]))
    res[label]=out
fit(S,["n24","lgap"],"H1 primary (n24, log gap)")
fit(S[S.topic=="O"],["n24","lgap"],"H1 oil only"); fit(S[S.topic=="T"],["n24","lgap"],"H1 tariffs only")
fit(S,["first"],"H2 first-in-cluster")
S["ACTION"]=(S.typ=="ACTION").astype(float); S["n24xA"]=S.n24*S.ACTION; fit(S[S.typ.isin(["ACTION","RHETORIC"])],["n24","ACTION","n24xA"],"H3 interaction")
for y in sorted(S.year.unique()): fit(S[S.year!=y],["n24","lgap"],f"H1 leave out {y}")
# H4 placebo
O=P[(P.cls=="OTHER")&(P.c1=="OTHER")&(P.c2=="OTHER")].copy(); O["n24"],O["gap"]=lag_feats(O); O["absz"]=(O.r/O.sd).abs(); oo=O.dropna(subset=["absz"])
X=pd.get_dummies(oo.topic,dtype=float,drop_first=True); X["n24"]=oo.n24.astype(float); m=sm.OLS(oo.absz.values,sm.add_constant(X).astype(float).values).fit(cov_type="cluster",cov_kwds={"groups":pd.factorize(oo.day.astype(str))[0]}); res["H4 placebo OTHER |z| on n24"]=dict(n=int(len(oo)),coef=float(m.params[-1]),p=float(m.pvalues[-1]))
json.dump(res,open("results_oot.json","w"),indent=1,default=float); S.to_csv("oot_signal_posts.csv",index=False)
print(json.dumps({k:res[k] for k in["n_rows","kappa","n_signal","cells"]},indent=1,default=float))
for k,v in res.items():
    if k.startswith("H"): print(k,json.dumps(v,default=float)[:380])
