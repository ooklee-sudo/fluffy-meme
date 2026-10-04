"""H2 test: does the post-2022 decline in UK adverts concentrate in occupations whose visual-content-creation tasks have LOW quality requirements?
Exposure components at O*NET-occupation level (all tasks in denominator): E_low = mean(s/2 * 1[q=0]); E_hi = mean(s/2 * 1[q=2]); E_mid for completeness.
Mapped to UK SOC4 via ISCO-08 (uk_exposure.py). Model per year t: y = a + g1*(zL+zH) + g2*(zL-zH) + c*zLang + sub-major FE;  b_low=g1+g2, b_high=g1-g2, difference b_low-b_high = 2*g2. SE clustered by SOC minor group."""
import json, re, csv, numpy as np, pandas as pd
import uk_exposure as UX, classify_onet as C
tasks=pd.DataFrame(C.load())[["id","soc"]]
cre=pd.DataFrame([json.loads(l) for l in open("data/all_creation_llm.jsonl")])[["id","s"]]; q=pd.DataFrame([json.loads(l) for l in open("data/quality_llm.jsonl")])[["id","q"]]
t=tasks.merge(cre,on="id").merge(q,on="id",how="left"); t["q"]=t.q.fillna(-1)
comp={}
for name,cond in (("low",t.q==0),("mid",t.q==1),("hi",t.q==2)):
    comp[name]=(t.s/2*cond).groupby(t.soc).mean()
E={k:UX.uk_exposure(v.to_dict())[0] for k,v in comp.items()}
lang={r["O*NET-SOC Code"]:float(r["dv_rating_beta"]) for r in csv.DictReader(open("data/ext/occ_level.csv"))}; L=UX.uk_exposure(lang)[0]
r=pd.read_csv("data/ons/uk_soc4_new_adverts_monthly.csv",dtype={"soc4":str}).set_index("soc4"); mc=[c for c in r.columns if re.match(r"[A-Z][a-z]{2}-\d\d$",c)]
X=r[mc].apply(pd.to_numeric,errors="coerce"); X.columns=pd.to_datetime(["01-"+c for c in mc],format="%d-%b-%y"); X=X.T.interpolate(method="linear",limit=2,limit_area="inside").T
yr=lambda y:X.loc[:,pd.Timestamp(f"{y-1}-07-01"):pd.Timestamp(f"{y}-06-01")].sum(axis=1,min_count=12)
years=[2018,2019,2020,2021,2023,2024,2025,2026]; A={y:yr(y) for y in years+[2022]}
df=pd.DataFrame({"low":E["low"],"mid":E["mid"],"hi":E["hi"],"L":L}).join(pd.DataFrame(A)).dropna(); df=df[df[2022]>=1000].copy()
df["minor"]=df.index.str[:3]; df["sub"]=df.index.str[:2]
z=lambda s:(s-s.mean())/s.std()
for c in ("low","hi","L"): df["z"+c]=z(df[c])
print("occupations:",len(df),"| corr(E_low,E_hi) = %.3f, corr(E_low,L) = %.3f, corr(E_hi,L) = %.3f"%(df.low.corr(df.hi),df.low.corr(df.L),df.hi.corr(df.L)))
print("top E_low:",[(i,round(df.low[i],3)) for i in df.low.sort_values(ascending=False).index[:6]]); print("top E_hi :",[(i,round(df.hi[i],3)) for i in df.hi.sort_values(ascending=False).index[:6]])
def ols_cluster(y,Xm,cl):
    b=np.linalg.lstsq(Xm,y,rcond=None)[0]; e=y-Xm@b; XtXi=np.linalg.pinv(Xm.T@Xm); G=pd.unique(cl); meat=np.zeros((Xm.shape[1],)*2)
    for g in G:
        m=cl==g; s=Xm[m].T@e[m]; meat+=np.outer(s,s)
    n,k=Xm.shape; c=len(G)/(len(G)-1)*(n-1)/(n-k); V=c*XtXi@meat@XtXi; return b,np.sqrt(np.diag(V))
rows=[]
for y in years:
    d=df; yv=(np.log(d[y])-np.log(d[2022])).values
    Xm=np.column_stack([np.ones(len(d)),(d.zlow+d.zhi).values,(d.zlow-d.zhi).values,d.zL.values,pd.get_dummies(d["sub"],drop_first=True).astype(float).values])
    b,se=ols_cluster(yv,Xm,d.minor.values); bl,bh=b[1]+b[2],b[1]-b[2]; diff,sed=2*b[2],2*se[2]
    # separate se for b_low and b_high via two direct regressions
    Xl=np.column_stack([np.ones(len(d)),d.zlow.values,d.zhi.values,d.zL.values,pd.get_dummies(d["sub"],drop_first=True).astype(float).values]); b2,se2=ols_cluster(yv,Xl,d.minor.values)
    rows.append((y,b2[1],se2[1],b2[2],se2[2],diff,sed))
res=pd.DataFrame(rows,columns=["year","b_low","se_low","b_hi","se_hi","diff_low_minus_hi","se_diff"]); res.to_csv("data/ons/uk_threshold_heterogeneity.csv",index=False)
print("\nyear  b_low(se)          b_high(se)         low-high (se)")
for _,x in res.iterrows(): print(int(x.year),f"{x.b_low:+.3f}({x.se_low:.3f})   {x.b_hi:+.3f}({x.se_hi:.3f})   {x.diff_low_minus_hi:+.3f}({x.se_diff:.3f})")
