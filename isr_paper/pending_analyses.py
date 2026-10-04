"""Three analyses reported in the revised manuscript (Sections 7.5-7.6):
(1) UK event study with occupation-specific linear pre-trends (slope through the base year, estimated on 2018-2021),
(2) errors-in-variables check: LLM exposure instrumented by the rule-based score (2SLS, independent-error assumption),
(3) European dose-response interacted with country-level acquisition of picture/video/audio generation (Eurostat 2025), and the position k of the most exposed ISCO occupation.
Usage: LLM_MODEL not needed (reads stored task scores). Run from this directory."""
import os, re, sys, numpy as np, pandas as pd
os.environ["EXPO"]="llm"
src=open("uk_dose_response.py").read(); src=src[:src.index("rows=[]")]
g={}; exec(compile(src,"uk_dose_response_head","exec"),g)
df,ols_cluster,design=g["df"],g["ols_cluster"],g["design"]
# rule-based exposure on the same occupations
os.environ["EXPO"]="rule"
src2=open("uk_dose_response.py").read(); src2=src2[:src2.index("rows=[]")]
g2={}; exec(compile(src2,"uk_dose_response_rule_head","exec"),g2); dfr=g2["df"]
df["Er"]=dfr["E"].reindex(df.index); df=df.dropna(subset=["Er"]); df["zR"]=(df.Er-df.Er.mean())/df.Er.std()
print("\n== (1) occupation-specific linear pre-trends (UK), sub-major FE + L control; N=",len(df))
pre=[2018,2019,2020,2021]; Y={t:np.log(df[t])-np.log(df[2022]) for t in range(2018,2027) if t!=2022}
tt=np.array([t-2022 for t in pre],float)
slope=sum(Y[t]*(t-2022) for t in pre)/ (tt**2).sum()   # through-origin slope per occupation
rows=[]
for label,sl in (("raw",0*slope),("detrended (2018-2021 slope)",slope)):
    out=[]
    for t in (2021,2023,2024,2025,2026):
        y=(Y[t]-sl*(t-2022)).values; b,se=ols_cluster(y,design(df,"sub"),df.minor.values); out.append((t,b[1],se[1])); rows.append((label,t,b[1],se[1]))
    print(label.ljust(30)," ".join(f"{t}:{b:+.3f}({s:.3f})" for t,b,s in out))
# randomization p for detrended 2026
rng=np.random.default_rng(5); 
for t in (2025,2026):
    y=(Y[t]-slope*(t-2022)).values; obs=ols_cluster(y,design(df,"sub"),df.minor.values)[0][1]; cnt=0; R=2000
    for _ in range(R):
        dd=df.copy(); dd["zE"]=dd.groupby("sub").zE.transform(lambda v: rng.permutation(v.values)); cnt+=abs(ols_cluster(y,design(dd,"sub"),dd.minor.values)[0][1])>=abs(obs)
    print(f"detrended {t}: b={obs:+.3f}, randomization p={(cnt+1)/(R+1):.3f}")
pd.DataFrame(rows,columns=["spec","t","b","se"]).to_csv("data/ons/uk_pretrend_detrended.csv",index=False)
print("\n== (2) 2SLS: z(E_llm) instrumented by z(E_rule), controls z(L), sub-major FE")
def tsls(y,d,fe="sub"):
    Z=np.column_stack([np.ones(len(d)),d.zR.values,d.zL.values,pd.get_dummies(d[fe],drop_first=True).astype(float).values])
    X=design(d,fe,True)
    Xh=X.copy(); Xh[:,1]=Z@np.linalg.lstsq(Z,X[:,1],rcond=None)[0]
    b=np.linalg.lstsq(Xh,y,rcond=None)[0]; e=y-X@b; A=np.linalg.pinv(Xh.T@Xh); cl=d.minor.values; meat=np.zeros((X.shape[1],)*2)
    for gg in pd.unique(cl):
        m=cl==gg; s=Xh[m].T@e[m]; meat+=np.outer(s,s)
    n,k=X.shape; c=len(pd.unique(cl))/(len(pd.unique(cl))-1)*(n-1)/(n-k); V=c*A@meat@A; return b[1],np.sqrt(V[1,1])
fs=np.corrcoef(df.zE,df.zR)[0,1]; print("corr(z_llm, z_rule) =%.2f"%fs)
for t in (2021,2023,2024,2025,2026):
    y=(np.log(df[t])-np.log(df[2022])).values; b,se=tsls(y,df); b0,se0=ols_cluster(y,design(df,"sub"),df.minor.values); print(f"{t}: OLS {b0[1]:+.3f}({se0[1]:.3f})  2SLS {b:+.3f}({se:.3f})")
print("\n== (3) Europe: exposure x country acquisition")
os.environ["EXPO"]="llm"
src3=open("eurostat_oja_dose_response.py").read(); src3=src3[:src3.index('print("\\nCoefficient on z(E)')]
g3={}; exec(compile(src3,"oja_head","exec"),g3); pan=g3["pan"].copy(); oc=g3["oc"]
acq=pd.read_csv("data/eurostat/country_barriers_adoption_2025.csv").set_index("geo").tpvsg/100
print("countries with acquisition data:",len(acq),"| in panel:",pan.geo.nunique())
pan=pan[pan.geo.isin(acq.index)].copy(); pan["a"]=pan.geo.map(acq); a=pan.drop_duplicates("geo").set_index("geo").a; pan["za"]=(pan.a-a.mean())/a.std()
pan["zEa"]=pan.zE*pan.za
print("acquisition mean %.3f sd %.3f min %.3f max %.3f"%(a.mean(),a.std(),a.min(),a.max()))
print("k (most exposed ISCO3 in standardized exposure):",round(oc.zE.max(),2),oc.zE.idxmax(), "| top 5:",[(i,round(oc.zE[i],2)) for i in oc.zE.sort_values(ascending=False).index[:5]])
for t in (2023,2024):
    d=pan[pan.t==t]
    X=np.column_stack([d.zE.values,d.zEa.values,d.zL.values,d.zL.values*d.za.values,pd.get_dummies(d.geo,drop_first=False).astype(float).values]); y=d.y.values
    b=np.linalg.lstsq(X,y,rcond=None)[0]; e=y-X@b; A=np.linalg.pinv(X.T@X); meat=np.zeros((X.shape[1],)*2)
    for cl in [d.isco3.values]:
        for gg in pd.unique(cl):
            m=cl==gg; s=X[m].T@e[m]; meat+=np.outer(s,s)
    n,k=X.shape; ng=d.isco3.nunique(); c=ng/(ng-1)*(n-1)/(n-k); V=c*A@meat@A; se=np.sqrt(np.diag(V))
    print(f"{t}: b(E)={b[0]:+.3f}({se[0]:.3f})  b(E x acquisition)={b[1]:+.3f}({se[1]:.3f})  N={n}")
