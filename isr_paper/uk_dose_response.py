"""Dose-response event study: UK new online adverts by SOC-2020 unit group on occupational exposure to visual content creation.
Pre-specified (before outcomes): primary exposure E = mean over an occupation's O*NET task statements of (score/2), score from prompt_creation.txt (0,1,2),
mapped O*NET-SOC -> ISCO-08 -> UK SOC-2020 (uk_exposure.py). Control: language exposure L (Eloundou et al. 2023, dv_rating_beta) mapped the same way.
Outcome: ln(adverts in Jul(t-1)..Jun(t)) - ln(adverts in Jul2021..Jun2022); base year t=2022.
Model per year t: y_it = a_t + b_t * z(E_i) + c_t * z(L_i) + sub-major-group FE + e;  SE clustered by SOC minor group (3-digit).
Inference check: randomization of E across occupations within SOC sub-major groups (2,000 draws)."""
import json, re, sys, collections, numpy as np, pandas as pd
import uk_exposure as UX
import classify_onet as C
import os, rule_creation as RC
EXPO=os.environ.get("EXPO","llm")
if EXPO=="rule":      # rule-based score on ALL 18,796 tasks (no LLM; validated against LLM labels in rule_creation.py)
    tasks=pd.DataFrame(C.load()); tasks["s"]=tasks.text.map(RC.score); print("exposure source: RULE-BASED, tasks scored:",len(tasks))
else:
    cls=[json.loads(l) for l in open("data/all_broad_llm.jsonl" if EXPO=="broad" else "data/all_creation_llm.jsonl")]; print("exposure source:",EXPO.upper(),"LLM, classified tasks:",len(cls),"of 18796")
    tasks=pd.DataFrame(cls)
tasks["soc"]=tasks.soc.astype(str)
occ=tasks.groupby("soc").s.agg(lambda x:(x/2).mean()); occ_any=tasks.groupby("soc").s.agg(lambda x:(x>0).mean())
E,covE=UX.uk_exposure(occ.to_dict()); E2,_=UX.uk_exposure(occ_any.to_dict())
import csv
lang={r["O*NET-SOC Code"]:float(r["dv_rating_beta"]) for r in csv.DictReader(open("data/ext/occ_level.csv"))}
L,_=UX.uk_exposure(lang)
E,covE=UX.uk_exposure(occ.to_dict()); covO=UX.uk_exposure.onet_cov   # coverage of O*NET occupations classified so far (partial run: SOC 11-29 only)
MINCOV=float(sys.argv[1]) if len(sys.argv)>1 else 0.0
# adverts
r=pd.read_csv("data/ons/uk_soc4_new_adverts_monthly.csv",dtype={"soc4":str}).set_index("soc4")
mc=[c for c in r.columns if re.match(r"[A-Z][a-z]{2}-\d\d$",c)]
X=r[mc].apply(pd.to_numeric,errors="coerce"); X.columns=pd.to_datetime(["01-"+c for c in mc],format="%d-%b-%y")
X=X.T.interpolate(method="linear",limit=2,limit_area="inside").T
def year(t): return X.loc[:,pd.Timestamp(f"{t-1}-07-01"):pd.Timestamp(f"{t}-06-01")].sum(axis=1,min_count=12)
years=list(range(2018,2027)); A={t:year(t) for t in years}
df=pd.DataFrame({"E":E,"E2":E2,"L":L,"cov":covO}).join(pd.DataFrame(A)).dropna()
print("UK occupations by O*NET classification coverage: >=0.9:",int((df["cov"]>=0.9).sum()),"| >=0.5:",int((df["cov"]>=0.5).sum()),"| all:",len(df))
df=df[df["cov"]>=MINCOV]
df=df[df[2022]>=1000].copy(); df["minor"]=df.index.str[:3]; df["sub"]=df.index.str[:2]; df["major"]=df.index.str[:1]
print("occupations in estimation sample:",len(df)); 
for c in ("E","L"): df["z"+c]=(df[c]-df[c].mean())/df[c].std()
print("corr(E,L) across occupations: %.3f"%df.E.corr(df.L)); print("top-10 exposure (E):",[(i,round(df.E[i],3)) for i in df.E.sort_values(ascending=False).index[:10]])
def ols_cluster(y,X,cl):
    b=np.linalg.lstsq(X,y,rcond=None)[0]; e=y-X@b; XtXi=np.linalg.pinv(X.T@X); G=pd.unique(cl); meat=np.zeros((X.shape[1],)*2)
    for g in G:
        m=cl==g; s=X[m].T@e[m]; meat+=np.outer(s,s)
    n,k=X.shape; c=len(G)/(len(G)-1)*(n-1)/(n-k); V=c*XtXi@meat@XtXi; return b,np.sqrt(np.diag(V))
def design(d,fe,controlL=True):
    cols=[np.ones(len(d)),d.zE.values]
    if controlL: cols.append(d.zL.values)
    X=np.column_stack(cols)
    if fe: X=np.column_stack([X,pd.get_dummies(d[fe],drop_first=True).astype(float).values])
    return X
rows=[]
for spec,fe,cl in (("no FE, controls L",None,True),("major-group FE, controls L","major",True),("sub-major FE, controls L","sub",True),("sub-major FE, no L control","sub",False)):
    for t in years:
        if t==2022: continue
        d=df.copy(); y=(np.log(d[t])-np.log(d[2022])).values; X=design(d,fe,cl); b,se=ols_cluster(y,X,d.minor.values)
        rows.append((spec,t,b[1],se[1])) 
res=pd.DataFrame(rows,columns=["spec","t","b_E","se"]); res["lo"]=res.b_E-1.96*res.se; res["hi"]=res.b_E+1.96*res.se
res.to_csv(f"data/ons/uk_dose_response_{EXPO}.csv",index=False)
print("\nCoefficient on z(E): change in ln adverts (year t vs Jul21-Jun22) per 1 SD of creation exposure")
piv=res.pivot(index="spec",columns="t",values="b_E"); pse=res.pivot(index="spec",columns="t",values="se")
for sp in piv.index: print(sp.ljust(30)," ".join(f"{t}:{piv.loc[sp,t]:+.3f}({pse.loc[sp,t]:.3f})" for t in piv.columns))
# randomization inference for the main spec at t=2025,2026 (sub-major FE, controls L)
rng=np.random.default_rng(3); out={}
for t in (2024,2025,2026):
    d=df.copy(); y=(np.log(d[t])-np.log(d[2022])).values; obs=ols_cluster(y,design(d,"sub"),d.minor.values)[0][1]; cnt=0; R=2000
    for _ in range(R):
        dd=d.copy(); dd["zE"]=dd.groupby("sub").zE.transform(lambda v: rng.permutation(v.values)); cnt+=abs(ols_cluster(y,design(dd,"sub"),dd.minor.values)[0][1])>=abs(obs)
    out[t]=(obs,(cnt+1)/(R+1))
print("\nrandomization p (E permuted within sub-major groups), sub-major FE + L control:",{t:(round(o,3),round(p,3)) for t,(o,p) in out.items()})
# robustness at 2025: alternative exposure E2 (share of tasks with any creation), drop web design, volume-weighted
d=df.copy(); y=(np.log(d[2025])-np.log(d[2022])).values
d["zE"]=(d.E2-d.E2.mean())/d.E2.std(); print("alt exposure (share of tasks scoring >=1), 2025:",round(ols_cluster(y,design(d,"sub"),d.minor.values)[0][1],3),"se",round(ols_cluster(y,design(d,"sub"),d.minor.values)[1][1],3))
d=df.drop(index=[i for i in ["2141"] if i in df.index]); y=(np.log(d[2025])-np.log(d[2022])).values; b,se=ols_cluster(y,design(d,"sub"),d.minor.values); print("drop web design (2141), 2025:",round(b[1],3),"se",round(se[1],3))
d=df.copy(); y=(np.log(d[2025])-np.log(d[2022])).values; w=np.sqrt(d[2022].values); Xw=design(d,"sub")*w[:,None]; b,se=ols_cluster(y*w,Xw,d.minor.values); print("volume-weighted, 2025:",round(b[1],3),"se",round(se[1],3))
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(7,3.8)); s=res[res.spec=="sub-major FE, controls L"]; ax.errorbar(s.t,s.b_E,yerr=1.96*s.se,fmt="o-",color="#1f77b4",capsize=3); ax.axhline(0,color="black",lw=.6); ax.axvline(2022,color="gray",ls=":")
ax.set_xlabel("year ending June"); ax.set_ylabel("coefficient on creation exposure (per SD)\nrelative to Jul2021–Jun2022"); ax.set_title("UK adverts: dose-response event study (exploratory)",fontsize=10); plt.tight_layout(); plt.savefig(f"data/ons/uk_dose_response_{EXPO}.png",dpi=130)
