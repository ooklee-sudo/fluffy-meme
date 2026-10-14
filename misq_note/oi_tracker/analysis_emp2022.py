import re,html,json,numpy as np,pandas as pd,statsmodels.api as sm
RF="../oil_income/raw_fred/"
SL=pd.read_csv("../oil_income/SERIES_LIST.csv",dtype=str)
NAMES={"Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA","Colorado":"CO","Connecticut":"CT","Delaware":"DE","District of Columbia":"DC","Florida":"FL","Georgia":"GA","Hawaii":"HI","Idaho":"ID","Illinois":"IL","Indiana":"IN","Iowa":"IA","Kansas":"KS","Kentucky":"KY","Louisiana":"LA","Maine":"ME","Maryland":"MD","Massachusetts":"MA","Michigan":"MI","Minnesota":"MN","Mississippi":"MS","Missouri":"MO","Montana":"MT","Nebraska":"NE","Nevada":"NV","New Hampshire":"NH","New Jersey":"NJ","New Mexico":"NM","New York":"NY","North Carolina":"NC","North Dakota":"ND","Ohio":"OH","Oklahoma":"OK","Oregon":"OR","Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC","South Dakota":"SD","Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT","Virginia":"VA","Washington":"WA","West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY"}
t=open("raw/fhwa_vm2_2019.html",errors="ignore").read(); vm={}
for r in re.findall(r"<tr.*?</tr>",t,flags=re.S):
    c=[x for x in (html.unescape(re.sub(r"<[^>]+>","",x)).strip() for x in re.findall(r"<t[dh].*?</t[dh]>",r,flags=re.S)) if x]
    if c and c[0] in NAMES: vm[NAMES[c[0]]]=[float(x.replace(",","")) for x in c[1:] if re.fullmatch(r"[\d,]+",x)][-1]
def rd(sid): d=pd.read_csv(RF+sid+".csv"); d.columns=["date","v"]; d["date"]=pd.to_datetime(d.date); return d.set_index("date").v
E1={};E2={};R={};NA={}
for ab,fips,rid in zip(SL.state,SL.fips,SL.restaurant_employment_FRED_id):
    import os
    if not os.path.exists(RF+rid+".csv"): continue
    pop=rd(f"{ab}POP"); pop19=float(pop[pop.index.year==2019].iloc[0]); E1[ab]=vm[ab]*1e6/(pop19*1e3)
    pv=rd(f"PPAA{ab}{fips}000A156NCEN"); E2[ab]=float(pv[pv.index.year==2019].iloc[0]); R[ab]=rd(rid); NA[ab]=rd(f"{ab}NA")
st=sorted(R); print("states",len(st))
E=pd.DataFrame({"E1":pd.Series(E1),"E2":pd.Series(E2)}).loc[st]; E=(E-E.mean())/E.std(ddof=0)
g=pd.read_csv("../oi_tracker/raw/GASREGW.csv",parse_dates=["observation_date"]).set_index("observation_date").GASREGW
G=np.log(g.resample("MS").mean())
rows=[]
for ab in st:
    d=pd.DataFrame({"lr":np.log(R[ab]),"ln":np.log(NA[ab])}).dropna(); d["st"]=ab; rows.append(d.reset_index())
P=pd.concat(rows).rename(columns={"index":"date","observation_date":"date"}); P["lrs"]=P.lr-P.ln
P=P.merge(E,left_on="st",right_index=True)
def prep(P,s,e,gshift=0,glag3=False,trend=True,drop=None):
    X=P[(P.date>=s)&(P.date<=e)].copy()
    if drop: X=X[~X.st.isin(drop)]
    gg=G.copy()
    if glag3: gg=gg.rolling(3).mean()
    if gshift: gg=gg.shift(gshift)
    X["G"]=X.date.map(gg); X=X.dropna(subset=["G"]); X["m"]=X.date.dt.month; X["t"]=(X.date.dt.year-2000)*12+X.date.dt.month; return X
def design(X,trend=True):
    cols=[pd.get_dummies(X.st+"_"+X.m.astype(str),dtype=float),pd.get_dummies(X.date.astype(str),dtype=float)]
    if trend:
        T=pd.get_dummies(X.st,dtype=float).mul(X.t-X.t.mean(),axis=0); cols.append(T)
    return pd.concat(cols,axis=1).values
def est(X,y,ex="E1",trend=True,nperm=0,seed=1):
    F=design(X,trend); Pm=np.linalg.pinv(F); resid=lambda v: v-F@(Pm@v)
    yr=resid(X[y].values.astype(float)); iv=(X[ex]*X.G).values; ir=resid(iv)
    b=float(ir@yr/(ir@ir)); u=yr-b*ir; ids=pd.factorize(X.st)[0]
    # cluster-robust se
    sc=np.array([ (ir[ids==k]*u[ids==k]).sum() for k in range(ids.max()+1)]); n=len(ids); K=ids.max()+1
    se=float(np.sqrt((sc**2).sum())/(ir@ir)*np.sqrt(K/(K-1)*(n-1)/(n-F.shape[1]-1))) if n>F.shape[1]+1 else float(np.sqrt((sc**2).sum())/(ir@ir))
    from scipy import stats
    p=float(2*(1-stats.t.cdf(abs(b/se),K-1)))
    out=dict(beta=b,se=se,p_cluster=p)
    if nperm:
        rng=np.random.default_rng(seed); ab=sorted(X.st.unique()); ev=X.groupby("st")[ex].first().reindex(ab).values; gv=X.G.values; sidx=pd.Categorical(X.st,categories=ab).codes
        bs=[]
        for _ in range(nperm):
            pe=rng.permutation(ev); v=resid(pe[sidx]*gv); bs.append(float(v@yr/(v@v)))
        bs=np.array(bs); out.update(p_perm_2s=float(np.mean(np.abs(bs)>=abs(b))),p_perm_low=float(np.mean(bs<=b)))
    return out
S,Ee="2021-09-01","2023-12-01"; res={}
X=prep(P,S,Ee); print("panel",X.shape,X.st.nunique(),X.date.nunique())
for y,lab in[("lr","restaurants"),("ln","nonfarm"),("lrs","rest share")]:
    res["E1 "+lab]=est(X,y,"E1",nperm=2000 if y=="lr" else 500)
for y,lab in[("lr","restaurants"),("ln","nonfarm"),("lrs","rest share")]:
    res["E2 "+lab]=est(X,y,"E2",nperm=500)
big=P[P.date=="2022-06-01"].set_index("st").lr.sort_values().index[-5:].tolist()
res["lag3 G"]=est(prep(P,S,Ee,glag3=True),"lr","E1")
res["no trend"]=est(X,"lr","E1",trend=False)
res["drop top5"]=est(prep(P,S,Ee,drop=big),"lr","E1")
res["2022-01..2023-12"]=est(prep(P,"2022-01-01",Ee),"lr","E1")
res["placebo G shifted 24m"]=est(prep(P,S,Ee,gshift=24),"lr","E1")
json.dump(res,open("results_emp2022.json","w"),indent=1)
for k,v in res.items(): print("%-22s beta=%+.5f se=%.5f p_cl=%.3f"%(k,v["beta"],v["se"],v["p_cluster"]),("perm2s=%.3f low=%.3f"%(v["p_perm_2s"],v["p_perm_low"]) if "p_perm_2s" in v else ""))
