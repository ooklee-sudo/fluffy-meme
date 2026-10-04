"""Sector-level test of acquisition -> employment (proxy for the firm-level link), Europe and US.
Europe: country x NACE-section cells. Acquisition = share of enterprises (10+) using picture/video/audio-generating AI in 2025 (Eurostat isoc_eb_ain2, E_AI_TPVSG).
Outcome = ln(mean employment 2023-25) - ln(mean employment 2019-21) from LFS (lfsa_eisn2, all occupations). Placebo = same for 2019-21 vs 2016-18.
Model: outcome = country FE + b * z(acquisition) [+ c * z(text-generation acquisition)]; SE clustered by sector; permutation of acquisition across sectors within country.
US: BTOS sector means of AI use (question 7) and of the reported employee-change index."""
import json, numpy as np, pandas as pd
def jload(f):
    d=json.load(open(f)); ids=d["id"]; size=d["size"]; idx={k:d["dimension"][k]["category"]["index"] for k in ids}; inv={k:{i:c for c,i in idx[k].items()} for k in ids}
    rows=[]
    for pos,v in d["value"].items():
        p=int(pos); key={}
        for k,s in reversed(list(zip(ids,size))): key[k]=inv[k][p%s]; p//=s
        key["v"]=v; rows.append(key)
    return pd.DataFrame(rows)
a=jload("data/eurostat/isoc_eb_ain2.json"); a=a[(a.time=="2025")&(a.unit=="PC_ENT")&(a.size_emp=="GE10")&a.indic_is.isin(["E_AI_TPVSG","E_AI_TNLG","E_AI_TANY"])]
a=a.pivot_table(index=["geo","nace_r2"],columns="indic_is",values="v").reset_index()
SECT=["C","F","G","H","I","J","L","M","N"]; a=a[a.nace_r2.isin(SECT)&~a.geo.isin(["EU27_2020","EA"])].dropna(subset=["E_AI_TPVSG"])
e=jload("data/eurostat/lfsa_eisn2.json"); e=e[(e.isco08=="TOTAL")&e.nace_r2.isin(SECT)&(e.sex=="T")&(e.age=="Y_GE15")]
w=e.pivot_table(index=["geo","nace_r2"],columns="time",values="v")
def lm(y): return np.log(w[[str(t) for t in y]].mean(axis=1))
w["d_post"]=lm([2023,2024,2025])-lm([2019,2020,2021]); w["d_pre"]=lm([2019,2020,2021])-lm([2016,2017,2018]); w=w[["d_post","d_pre"]].reset_index()
df=a.merge(w,on=["geo","nace_r2"]).dropna(subset=["d_post","d_pre","E_AI_TNLG","E_AI_TANY","E_AI_TPVSG"]); print("cells:",len(df),"countries:",df.geo.nunique(),"sectors:",sorted(df.nace_r2.unique()))
for c in ("E_AI_TPVSG","E_AI_TNLG","E_AI_TANY"): df["z_"+c]=(df[c]-df[c].mean())/df[c].std()
print("acquisition (picture/video/audio) mean %.1f sd %.1f; corr with text generation %.2f, with any AI %.2f"%(df.E_AI_TPVSG.mean(),df.E_AI_TPVSG.std(),df.E_AI_TPVSG.corr(df.E_AI_TNLG),df.E_AI_TPVSG.corr(df.E_AI_TANY)))
def fit(d,y,xs):
    X=np.column_stack([d[xs].values,pd.get_dummies(d.geo,drop_first=False).astype(float).values]); yy=d[y].values
    b=np.linalg.lstsq(X,yy,rcond=None)[0]; e_=yy-X@b; A=np.linalg.pinv(X.T@X); cl=d.nace_r2.values; meat=np.zeros((X.shape[1],)*2)
    for g in pd.unique(cl):
        m=cl==g; s=X[m].T@e_[m]; meat+=np.outer(s,s)
    n,k=X.shape; G=len(pd.unique(cl)); c=G/(G-1)*(n-1)/(n-k); se=np.sqrt(np.diag(c*A@meat@A)); return b[:len(xs)],se[:len(xs)]
res={}
for y in ("d_post","d_pre"):
    for nm,xs in (("picture/video/audio only",["z_E_AI_TPVSG"]),("+ text-generation control",["z_E_AI_TPVSG","z_E_AI_TNLG"]),("+ any-AI control",["z_E_AI_TPVSG","z_E_AI_TANY"])):
        b,se=fit(df,y,xs); res[(y,nm)]=(b[0],se[0]); print(f"{y:7s} {nm:28s} b={b[0]:+.3f} (se {se[0]:.3f})")
df['d_dd']=df.d_post-df.d_pre
b,se=fit(df,'d_dd',['z_E_AI_TPVSG']); print(f'd_post - d_pre  picture/video/audio only  b={b[0]:+.3f} (se {se[0]:.3f})')
b,se=fit(df,'d_dd',['z_E_AI_TPVSG','z_E_AI_TNLG']); print(f'd_post - d_pre  + text-generation control  b={b[0]:+.3f} (se {se[0]:.3f})')
rng=np.random.default_rng(11)
for y in ("d_post","d_pre"):
    obs=fit(df,y,["z_E_AI_TPVSG"])[0][0]; cnt=0; R=2000
    for _ in range(R):
        d2=df.copy(); d2["z_E_AI_TPVSG"]=d2.groupby("geo").z_E_AI_TPVSG.transform(lambda v: rng.permutation(v.values)); cnt+=abs(fit(d2,y,["z_E_AI_TPVSG"])[0][0])>=abs(obs)
    print(f"permutation p (acquisition permuted across sectors within country), {y}: {(cnt+1)/(R+1):.3f}")
# predicted coefficient under complete assimilation: sector employment share of the occupation s ~ exposure; use most exposed occupation share ~ 1 in sector -> upper bound on sector-level effect = beta * sd(acq in share units) * (occupation share of sector employment)
sd=df.E_AI_TPVSG.std()/100; print("sd of acquisition (share): %.3f -> complete assimilation with beta=-0.5 and visual-production share s of sector employment implies b = -0.5*%.3f*s = %.4f*s per SD"%(sd,sd,-0.5*sd))
# US BTOS
x=pd.read_excel("data/btos/Sector.xlsx",sheet_name="Response Estimates")
cols=[c for c in x.columns if str(c).isdigit()]
q7=x[(x["Question ID"]==7)&(x["Answer"]=="Yes")].set_index("Sector")[cols]
q7=q7.apply(lambda s: pd.to_numeric(s.astype(str).str.rstrip("%"),errors="coerce"))
ix=pd.read_excel("data/btos/Sector.xlsx",sheet_name="Index Estimates"); emp=ix[ix["Option Text"]=="Employees"].set_index("Sector").iloc[:,1:]
emp=emp.apply(pd.to_numeric,errors="coerce")
ai=q7[cols[:6]].mean(axis=1); en=emp.iloc[:,:6].mean(axis=1)
j=pd.concat([ai.rename("ai"),en.rename("emp")],axis=1).dropna(); j=j[j.index.astype(str).str.len()==2]
print("\nUS BTOS: sectors",len(j),"| corr(AI use share, employee index) = %.2f"%j.ai.corr(j.emp),"| Spearman %.2f"%j.ai.rank().corr(j.emp.rank()))
