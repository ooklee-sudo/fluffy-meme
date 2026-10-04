"""Replication in Canada: Statistics Canada Job Vacancy and Wage Survey, vacancies by NOC-2021 unit group (table 14-10-0444), quarterly 2015Q1-2026Q2, Canada total.
Exposure: NOC 'Main duties' statements scored with the same LLM rubric (classify_noc.py); occupation exposure = mean(score/2) over duties.
Outcome: ln(vacancies in the four quarters ending Jun of year t) - ln(vacancies in the 4 quarters ending Jun 2022); i.e. year t = Jul(t-1)..Jun(t) windows (JVWS reference months 2015-01 = Jan-Mar).
Model per year: y = a + b z(E) + FE(NOC 2-digit group) + e, SE clustered by NOC 3-digit group. (No language-exposure control: Eloundou scores are SOC-based and not mapped to NOC; flagged as limitation.)"""
import json, re, numpy as np, pandas as pd
d=pd.read_csv("data/statcan/canada_jv.csv",encoding="utf-8-sig",usecols=["REF_DATE","National Occupational Classification","VALUE"])
d["code"]=d["National Occupational Classification"].str.extract(r"\[(\d+)\]$")[0]; d=d[d.code.str.len()==5].copy()
d["q"]=pd.PeriodIndex(d.REF_DATE.str[:4]+"Q"+((d.REF_DATE.str[5:7].astype(int)-1)//3+1).astype(str),freq="Q")
wide=d.pivot_table(index="code",columns="q",values="VALUE",aggfunc="first")
wide=wide.reindex(columns=pd.period_range("2015Q1","2026Q2",freq="Q"))   # 2020Q2 was not collected (COVID) -> missing
def yr(y):   # four quarters: Q3(y-1)..Q2(y) -> reference months Jul(y-1)..Jun(y)
    qs=[pd.Period(f"{y-1}Q3"),pd.Period(f"{y-1}Q4"),pd.Period(f"{y}Q1"),pd.Period(f"{y}Q2")]
    return wide[qs].sum(axis=1,min_count=4)
years=[2017,2018,2019,2021,2023,2024,2025,2026]; A={t:yr(t) for t in years+[2022]}   # 2020 window excluded: 2020Q2 not collected
try:
    sc=pd.DataFrame([json.loads(l) for l in open("data/noc_creation_llm.jsonl")])
except FileNotFoundError: raise SystemExit("classification not finished")
E=(sc.s/2).groupby(sc.noc).mean(); print("NOC unit groups with exposure:",len(E),"| share of duties scoring >=1: %.3f"%(sc.s>0).mean())
df=pd.DataFrame({"E":E}).join(pd.DataFrame(A)).dropna(subset=["E",2022]); df=df[df[2022]>=1000].copy(); df["g3"]=df.index.str[:3]; df["g2"]=df.index.str[:2]; df["g1"]=df.index.str[:1]
df["zE"]=(df.E-df.E.mean())/df.E.std(); print("estimation sample:",len(df),"unit groups; SD of exposure %.3f; top:"%df.E.std(),[(i,round(df.E[i],3)) for i in df.E.sort_values(ascending=False).index[:8]])
def ols(y,X,cl):
    b=np.linalg.lstsq(X,y,rcond=None)[0]; e=y-X@b; XtXi=np.linalg.pinv(X.T@X); G=pd.unique(cl); meat=np.zeros((X.shape[1],)*2)
    for g in G:
        m=cl==g; s=X[m].T@e[m]; meat+=np.outer(s,s)
    n,k=X.shape; c=len(G)/(len(G)-1)*(n-1)/(n-k); V=c*XtXi@meat@XtXi; return b,np.sqrt(np.diag(V))
def design(x,fe): 
    X=np.column_stack([np.ones(len(x)),x.zE.values]); 
    return np.column_stack([X,pd.get_dummies(x[fe],drop_first=True).astype(float).values]) if fe else X
res=[]
print("\nCoefficient on z(E): change in log vacancies (year ending June t vs base Jul2021-Jun2022) per SD of creation exposure; SE clustered by NOC3")
for spec,fe in (("no FE",None),("NOC major-group FE","g1"),("NOC 2-digit FE","g2")):
    out=[]
    for t in years:
        x=df[(df[t]>0)&(df[2022]>0)]; y=(np.log(x[t])-np.log(x[2022])).values; b,se=ols(y,design(x,fe),x.g3.values); out.append(f"{t}:{b[1]:+.3f}({se[1]:.3f})"); res.append((spec,t,b[1],se[1],len(x)))
    print(spec.ljust(20)," ".join(out))
pd.DataFrame(res,columns=["spec","t","b","se","n"]).to_csv("data/statcan/canada_dose_response.csv",index=False)
rng=np.random.default_rng(6); print("\nRandomization p (E permuted within NOC 2-digit groups, 2-digit FE):")
for t in (2023,2024,2025,2026):
    x=df[(df[t]>0)&(df[2022]>0)].copy(); y=(np.log(x[t])-np.log(x[2022])).values; obs=ols(y,design(x,"g2"),x.g3.values)[0][1]; cnt=0; R=1000
    for _ in range(R):
        x2=x.copy(); x2["zE"]=x2.groupby("g2").zE.transform(lambda v: rng.permutation(v.values)); cnt+=abs(ols(y,design(x2,"g2"),x2.g3.values)[0][1])>=abs(obs)
    print(f"  {t}: b={obs:+.3f}, p={(cnt+1)/(R+1):.3f}")
for code,nm in (("52120","Graphic designers and illustrators"),("21233","Web designers"),("51111","Authors and writers"),("51120","Producers, directors, choreographers"),("52110","Film and video camera operators"),("52112","Photographers (if present)")):
    if code in A[2022].index and pd.notna(A[2022][code]):
        print(f"  NOC {code} {nm}: vacancies (4Q windows) "+", ".join(f"{t}:{A[t][code]:.0f}" for t in (2019,2021,2022,2023,2024,2025,2026) if pd.notna(A[t][code])))
