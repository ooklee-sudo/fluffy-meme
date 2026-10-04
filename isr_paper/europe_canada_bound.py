"""Inputs for the detectability bound without UK data, and the European acquisition interaction.
(1) k = position (in SD) of the most exposed occupation in the European (ISCO3) and Canadian (NOC unit group) exposure distributions.
(2) European dose-response interacted with country-level acquisition of picture/video/audio generation (Eurostat 2025): complete assimilation predicts a steeper gradient where acquisition is higher.
(3) Minimum detectable effects (2.8 x SE) for Europe (2023, 2024) and Canada (NOC 2-digit FE)."""
import os, numpy as np, pandas as pd
os.environ["EXPO"]="llm"
src=open("eurostat_oja_dose_response.py").read(); src=src[:src.index('print("\\nCoefficient on z(E)')]
g={}; exec(compile(src,"oja_head","exec"),g); pan=g["pan"].copy(); oc=g["oc"]
print("\nEurope: k =",round(oc.zE.max(),2),oc.zE.idxmax(),"| top 5:",[(i,round(oc.zE[i],2)) for i in oc.zE.sort_values(ascending=False).index[:5]])
acq=pd.read_csv("data/eurostat/country_barriers_adoption_2025.csv").set_index("geo").tpvsg/100
pan=pan[pan.geo.isin(acq.index)].copy(); print("countries in panel with acquisition data:",pan.geo.nunique(),sorted(pan.geo.unique()))
pan["a"]=pan.geo.map(acq); a=pan.drop_duplicates("geo").set_index("geo").a; pan["za"]=(pan.a-a.mean())/a.std(); pan["zEa"]=pan.zE*pan.za
print("acquisition: mean %.3f sd %.3f min %.3f max %.3f"%(a.mean(),a.std(),a.min(),a.max()))
for t in (2021,2023,2024):
    d=pan[pan.t==t]
    X=np.column_stack([d.zE.values,d.zEa.values,d.zL.values,d.zL.values*d.za.values,pd.get_dummies(d.geo,drop_first=False).astype(float).values]); y=d.y.values
    b=np.linalg.lstsq(X,y,rcond=None)[0]; e=y-X@b; A=np.linalg.pinv(X.T@X); meat=np.zeros((X.shape[1],)*2); cl=d.isco3.values
    for gg in pd.unique(cl):
        m=cl==gg; s=X[m].T@e[m]; meat+=np.outer(s,s)
    n,k=X.shape; ng=d.isco3.nunique(); c=ng/(ng-1)*(n-1)/(n-k); se=np.sqrt(np.diag(c*A@meat@A@np.eye(len(b))))
    print(f"{t}: b(E)={b[0]:+.3f}({se[0]:.3f})  b(E x acq)={b[1]:+.3f}({se[1]:.3f})  N={n}")
# randomization of the interaction: permute country acquisition across countries
rng=np.random.default_rng(7)
for t in (2023,2024):
    d=pan[pan.t==t]; countries=a.index.values
    def inter(d,za):
        X=np.column_stack([d.zE.values,d.zE.values*za,d.zL.values,d.zL.values*za,pd.get_dummies(d.geo,drop_first=False).astype(float).values]); return np.linalg.lstsq(X,d.y.values,rcond=None)[0][1]
    za=d.za.values; obs=inter(d,za); cnt=0; R=2000; zmap=pan.drop_duplicates("geo").set_index("geo").za
    for _ in range(R):
        perm=dict(zip(countries,rng.permutation(zmap.reindex(countries).values))); cnt+=abs(inter(d,d.geo.map(perm).values))>=abs(obs)
    print(f"  {t}: interaction {obs:+.3f}, permutation p (countries) = {(cnt+1)/(R+1):.3f}")
# Canada k
import json, re
d=pd.read_csv("data/statcan/canada_jv.csv",encoding="utf-8-sig",usecols=["REF_DATE","National Occupational Classification","VALUE"])
sc=pd.DataFrame([json.loads(l) for l in open("data/noc_creation_llm.jsonl")]); E=(sc.s/2).groupby(sc.noc).mean()
base=pd.read_csv("data/statcan/canada_dose_response.csv"); n=base[(base.spec=="NOC 2-digit FE")]
print("\nCanada SD of exposure %.3f; max z (all NOC with exposure) %.2f at %s"%(E.std(),(E.max()-E.mean())/E.std(),E.idxmax()))
print("Canada 2-digit FE:",n[["t","b","se"]].round(3).values.tolist())
e=pd.read_csv("data/eurostat/oja_dose_response.csv"); print("Europe MDE (2.8 x SE_isco3, LLM control):",{int(r.t):round(2.8*r.se_isco3,3) for r in e[e.spec=="with LLM control"].itertuples()})

# (4) Europe: deviation of post-2022 coefficients from the linear pre-2022 trend in the exposure gradient (stacked, country-year FE, L control interacted with year dummies)
print("\nEurope detrended (stacked 2019-2021, 2023-2024; linear trend in exposure gradient estimated on 2019-2021 through the base year):")
pn=g["pan"].copy(); pn=pn[pn.t.isin([2019,2020,2021,2023,2024])].copy(); pn["tt"]=pn.t-2022
pn["cy"]=pn.geo+"_"+pn.t.astype(str)
cols=[pn.zE.values*pn.tt.values, pn.zE.values*(pn.t==2023), pn.zE.values*(pn.t==2024)]
for t in (2019,2020,2021,2023,2024): cols.append(pn.zL.values*(pn.t==t))
X=np.column_stack(cols+[pd.get_dummies(pn.cy,drop_first=False).astype(float).values]); y=pn.y.values
b=np.linalg.lstsq(X,y,rcond=None)[0]; e=y-X@b; A=np.linalg.pinv(X.T@X); meat=np.zeros((X.shape[1],)*2); cl=pn.isco3.values
for gg in pd.unique(cl):
    m=cl==gg; s=X[m].T@e[m]; meat+=np.outer(s,s)
n,k=X.shape; ng=pn.isco3.nunique(); c=ng/(ng-1)*(n-1)/(n-k); se=np.sqrt(np.diag(c*A@meat@A))
# post coefficient relative to the base year line: b_t_dev = delta_t ; implied trend contribution g*(t-2022)
print(f"pre-trend slope per year (exposure gradient, 2019-2021): {b[0]:+.4f} ({se[0]:.4f})")
print(f"deviation from the extrapolated linear pre-trend (trend term applies to all years; post dummies measure deviations): 2023 {b[1]:+.4f} ({se[1]:.4f}); 2024 {b[2]:+.4f} ({se[2]:.4f})")
print("occupations:",pn.isco3.nunique(),"countries:",pn.geo.nunique(),"cells (2023):",int((pn.t==2023).sum()))
