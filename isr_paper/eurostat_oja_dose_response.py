"""Replication in 18 European countries: Eurostat experimental statistics, online job advertisements (OJA, thousand) by ISCO-08 3-digit occupation, annual 2019-2024 (jvs_a_isco3_r1).
Exposure: O*NET creation exposure (LLM-coded) and LLM exposure (Eloundou), mapped O*NET -> ISCO-08 (ESCO crosswalk prefix, 3 digits).
Model per year t: y_oct = ln OJA_oct - ln OJA_oc,2022 = a_ct + b_t z(E_o) + c_t z(L_o) + e ; country-year fixed effects; SE clustered by ISCO 3-digit occupation (and by ISCO 2-digit).
Randomization: permute E across occupations within ISCO 2-digit groups."""
import json, csv, collections, numpy as np, pandas as pd
import uk_exposure as UX, classify_onet as C
d=json.load(open("data/eurostat/jvs_a_isco3_r1.json")); ids=d["id"]; size=d["size"]
idx={k:d["dimension"][k]["category"]["index"] for k in ids}; inv={k:{i:c for c,i in idx[k].items()} for k in ids}
rows=[]
for pos,v in d["value"].items():
    p=int(pos); key={}
    for k,s in reversed(list(zip(ids,size))): key[k]=inv[k][p%s]; p//=s
    if key["indic_em"]=="OJA" and key["unit"]=="THS" and len(key["geo"])==2 and key["geo"]!="EA" and key["isco08"].startswith("OC") and len(key["isco08"])==5:
        rows.append((key["geo"],key["isco08"][2:],int(key["time"]),v))
oja=pd.DataFrame(rows,columns=["geo","isco3","t","v"]); oja=oja[oja.v>0]
# exposures at ISCO3
tasks=pd.DataFrame(C.load())[["id","soc"]].merge(pd.DataFrame([json.loads(l) for l in open("data/all_creation_sonnet55.jsonl")])[["id","s"]],on="id")
expo=(tasks.s/2).groupby(tasks.soc).mean().to_dict()
lang={r["O*NET-SOC Code"]:float(r["dv_rating_beta"]) for r in csv.DictReader(open("data/ext/occ_level.csv"))}
o2i=UX.onet_to_isco(); gE=collections.defaultdict(list); gL=collections.defaultdict(list)
for soc,i4s in o2i.items():
    for i4 in i4s:
        if soc in expo: gE[i4[:3]].append(expo[soc])
        if soc in lang: gL[i4[:3]].append(lang[soc])
ex=pd.DataFrame({"E":{k:np.mean(v) for k,v in gE.items()},"L":{k:np.mean(v) for k,v in gL.items()}})
base=oja[oja.t==2022].rename(columns={"v":"v22"})[["geo","isco3","v22"]]
pan=oja.merge(base,on=["geo","isco3"]).merge(ex,left_on="isco3",right_index=True)
pan=pan[pan.v22>=1.0]            # at least 1,000 adverts in 2022 (OJA in thousands)
pan["y"]=np.log(pan.v)-np.log(pan.v22); pan["g2"]=pan.isco3.str[:2]
for c in ("E","L"): pan["z"+c]=(pan[c]-pan[c].mean())/pan[c].std()
print("countries:",pan.geo.nunique(),"| occupations:",pan.isco3.nunique(),"| cells:",len(pan[pan.t==2023]),"(2023)")
oc=pan.drop_duplicates("isco3").set_index("isco3"); print("corr(E,L) across occupations: %.2f"%oc.E.corr(oc.L)); print("top exposure ISCO3:",[(i,round(oc.E[i],3)) for i in oc.E.sort_values(ascending=False).index[:8]])
def fit(d,controlL=True,w=None):
    X=[d.zE.values]; 
    if controlL: X.append(d.zL.values)
    X=np.column_stack(X+[pd.get_dummies(d.geo,drop_first=False).astype(float).values]); y=d.y.values
    if w is not None: sw=np.sqrt(w); X=X*sw[:,None]; y=y*sw
    b=np.linalg.lstsq(X,y,rcond=None)[0]; e=y-X@b; XtXi=np.linalg.pinv(X.T@X); out=[]
    for cl in (d.isco3.values,d.g2.values):
        G=pd.unique(cl); meat=np.zeros((X.shape[1],)*2)
        for g in G:
            m=cl==g; s=X[m].T@e[m]; meat+=np.outer(s,s)
        n,k=X.shape; c=len(G)/(len(G)-1)*(n-1)/(n-k); V=c*XtXi@meat@XtXi; out.append(np.sqrt(V[0,0]))
    return b[0],out[0],out[1]
print("\nCoefficient on z(E) (log change of OJA vs 2022 per SD of creation exposure); country-year FE; SE by ISCO3 [by ISCO2]")
res=[]
for spec,cL in (("with LLM control",True),("without LLM control",False)):
    print(spec)
    for t in (2019,2020,2021,2023,2024):
        dd=pan[pan.t==t]; b,s3,s2=fit(dd,cL); res.append((spec,t,b,s3,s2,len(dd))); print(f"  {t}: {b:+.3f} ({s3:.3f}) [{s2:.3f}]  N={len(dd)}")
pd.DataFrame(res,columns=["spec","t","b","se_isco3","se_isco2","n"]).to_csv("data/eurostat/oja_dose_response.csv",index=False)
rng=np.random.default_rng(4); print("\nRandomization p (E permuted within ISCO2 groups, LLM control):")
for t in (2023,2024):
    dd=pan[pan.t==t].copy(); obs=fit(dd)[0]; cnt=0; R=1000
    occs=oc[["g2","zE"]].copy()
    for _ in range(R):
        perm=occs.groupby("g2").zE.transform(lambda v: rng.permutation(v.values)); m=perm.to_dict(); d2=dd.copy(); d2["zE"]=d2.isco3.map(m); cnt+=abs(fit(d2)[0])>=abs(obs)
    print(f"  {t}: b={obs:+.3f}, p={(cnt+1)/(R+1):.3f}")
# weighted and country heterogeneity
dd=pan[pan.t==2024]; print("\n2024 volume-weighted (2022 OJA):",[round(x,3) for x in fit(dd,True,dd.v22.values)])
cc=[]
for g,dg in pan.groupby("geo"):
    for t in (2023,2024):
        x=dg[dg.t==t]
        if len(x)>=25:
            X=np.column_stack([np.ones(len(x)),x.zE.values,x.zL.values]); b=np.linalg.lstsq(X,x.y.values,rcond=None)[0]; cc.append((g,t,b[1],len(x)))
cc=pd.DataFrame(cc,columns=["geo","t","b","n"]); 
for t in (2023,2024): x=cc[cc.t==t]; print(f"country-level slopes {t}: n={len(x)}, negative in {int((x.b<0).sum())}, median {x.b.median():+.3f}, range {x.b.min():+.3f}..{x.b.max():+.3f}")
cc.to_csv("data/eurostat/oja_country_slopes.csv",index=False)
# creative occupations at ISCO3: path relative to 2022 (country-year FE-free mean log change by occupation)
for code,nm in (("216","Architects, planners, surveyors, designers"),("265","Creative and performing artists"),("343","Artistic, cultural, culinary associates"),("264","Authors, journalists, linguists"),("243","Sales, marketing, PR professionals")):
    x=pan[pan.isco3==code].groupby("t").y.mean(); print(f"  ISCO {code} {nm}: mean log change vs 2022:",{int(k):round(v,2) for k,v in x.items()}, "| all-occupation mean:",{int(k):round(v,2) for k,v in pan.groupby('t').y.mean().items()} if code=="216" else "")
