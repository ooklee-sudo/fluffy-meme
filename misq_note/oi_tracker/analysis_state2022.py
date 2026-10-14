import sys; sys.path.insert(0,".")
import re,json,html,numpy as np,pandas as pd,statsmodels.api as sm
RF="../oil_income/raw_fred/"
NAMES={"Alabama":"AL","Alaska":"AK","Arizona":"AZ","Arkansas":"AR","California":"CA","Colorado":"CO","Connecticut":"CT","Delaware":"DE","District of Columbia":"DC","Florida":"FL","Georgia":"GA","Hawaii":"HI","Idaho":"ID","Illinois":"IL","Indiana":"IN","Iowa":"IA","Kansas":"KS","Kentucky":"KY","Louisiana":"LA","Maine":"ME","Maryland":"MD","Massachusetts":"MA","Michigan":"MI","Minnesota":"MN","Mississippi":"MS","Missouri":"MO","Montana":"MT","Nebraska":"NE","Nevada":"NV","New Hampshire":"NH","New Jersey":"NJ","New Mexico":"NM","New York":"NY","North Carolina":"NC","North Dakota":"ND","Ohio":"OH","Oklahoma":"OK","Oregon":"OR","Pennsylvania":"PA","Rhode Island":"RI","South Carolina":"SC","South Dakota":"SD","Tennessee":"TN","Texas":"TX","Utah":"UT","Vermont":"VT","Virginia":"VA","Washington":"WA","West Virginia":"WV","Wisconsin":"WI","Wyoming":"WY"}
SL=pd.read_csv("../oil_income/SERIES_LIST.csv",dtype=str); F2A=dict(zip(SL.fips,SL.state))
# exposure
t=open("raw/fhwa_vm2_2019.html",errors="ignore").read(); vm={}
for r in re.findall(r"<tr.*?</tr>",t,flags=re.S):
    c=[html.unescape(re.sub(r"<[^>]+>","",x)).strip() for x in re.findall(r"<t[dh].*?</t[dh]>",r,flags=re.S)]
    c=[x for x in c if x]
    if c and c[0] in NAMES:
        nums=[float(x.replace(",","")) for x in c[1:] if re.fullmatch(r"[\d,]+",x)]
        vm[NAMES[c[0]]]=nums[-1]
print("VMT states",len(vm))
def fred19(sid):
    d=pd.read_csv(RF+sid+".csv"); d.columns=["date","v"]; d["date"]=pd.to_datetime(d.date); return float(d[d.date.dt.year==2019].v.iloc[0])
E1={};E2={}
for ab,fips in zip(SL.state,SL.fips):
    pop=fred19(f"{ab}POP"); E1[ab]=vm[ab]*1e6/(pop*1e3)
    E2[ab]=fred19(f"PPAA{ab}{fips}000A156NCEN")
E=pd.DataFrame({"E1":pd.Series(E1),"E2":pd.Series(E2)}); E=(E-E.mean())/E.std(ddof=0)
print(E.describe().round(2).loc[["count","min","max"]])
# spending
d=pd.read_csv("raw/Affinity_-_State_-_Daily.csv",na_values=".",low_memory=False)
d["date"]=pd.to_datetime(d[["year","month","day"]]); d["st"]=d.statefips.astype(int).astype(str).str.zfill(2).map(F2A)
cats=["spend_acf","spend_aap","spend_aer","spend_sgh","spend_grf","spend_hcs","spend_all","spend_all_q1","spend_all_q4"]
dd=d[d.freq=="d"].copy(); dd["wk"]=dd.date.dt.to_period("W-SUN").dt.end_time.dt.normalize()
g=dd.groupby(["st","wk"]); cnt=g.size(); Wd=g[cats].mean()[cnt==7].reset_index().rename(columns={"wk":"date"})
Ww=d[d.freq=="w"][["st","date"]+cats]
W=pd.concat([Wd,Ww]).drop_duplicates(["st","date"]); W=W[(W.date>="2021-07-11")&(W.date<="2024-06-16")&W.st.notna()]
gas=pd.read_csv("../oi_tracker/raw/GASREGW.csv",parse_dates=["observation_date"]).set_index("observation_date").GASREGW
gas.index=gas.index.to_period("W-SUN").end_time.normalize(); gas=np.log(gas.groupby(level=0).mean()).rename("G")
W=W.merge(gas,left_on="date",right_index=True,how="left")
W["acf_missing"]=W.spend_acf.isna()
cov=W.groupby("st").spend_acf.apply(lambda s:s.notna().mean()); drop=list(cov[cov<0.9].index); print("dropped (coverage<90%):",drop)
W=W[~W.st.isin(drop)]
W["DISC"]=W[["spend_acf","spend_aap","spend_aer","spend_sgh"]].mean(axis=1,skipna=False); W["ESS"]=W[["spend_grf","spend_hcs"]].mean(axis=1,skipna=False)
W=W.merge(E,left_on="st",right_index=True)
print("panel",W.shape,"states",W.st.nunique(),"weeks",W.date.nunique())
def fit(y,ex="E1",data=None,G="G"):
    X=W if data is None else data
    X=X.dropna(subset=[y,G]).copy(); X["I"]=X[ex]*X[G]
    D=pd.get_dummies(X.st,drop_first=True,dtype=float); T=pd.get_dummies(X.date.astype(str),drop_first=True,dtype=float)
    M=pd.concat([X[["I"]],D,T],axis=1); M=sm.add_constant(M)
    m=sm.OLS(X[y].values,M.values.astype(float)).fit(cov_type="cluster",cov_kwds={"groups":pd.factorize(X.st)[0]})
    return float(m.params[1]),float(m.bse[1]),float(m.pvalues[1]),X
def perm(y,ex="E1",n=5000,data=None,G="G",seed=1):
    b,se,p,X=fit(y,ex,data,G); rng=np.random.default_rng(seed)
    Xd=X.copy(); Xd["I"]=Xd[ex]*Xd[G]
    # fast: partial out FE once, then permute exposure across states
    st=pd.factorize(Xd.st)[0]; wk=pd.factorize(Xd.date)[0]
    def demean(v):
        v=v.copy()
        for _ in range(30):
            v=v-pd.Series(v).groupby(st).transform("mean").values; v=v-pd.Series(v).groupby(wk).transform("mean").values
        return v
    yv=demean(Xd[y].values.astype(float)); gv=Xd[G].values; ab=sorted(Xd.st.unique()); ev=Xd.groupby("st")[ex].first().reindex(ab).values
    idx=pd.Series(st); out=[]
    for _ in range(n):
        pe=rng.permutation(ev); iv=demean((pe[st]*gv).astype(float)); out.append(float((iv@yv)/(iv@iv)))
    out=np.array(out); return b,se,p,float(np.mean(np.abs(out)>=abs(b))),float(np.mean(out<=b))
if '--checks' not in sys.argv:
    res={}
    for y in["spend_acf","DISC","spend_aap","spend_aer","spend_sgh","ESS","spend_grf","spend_hcs","spend_all"]:
        b,se,p,pp,pl=perm(y,n=1000); res["E1 "+y]=dict(beta=b,se=se,p_cluster=p,p_perm_2s=pp,p_perm_low=pl)
    for y in["spend_acf","DISC","ESS"]:
        b,se,p,pp,pl=perm(y,ex="E2",n=1000); res["E2 "+y]=dict(beta=b,se=se,p_cluster=p,p_perm_2s=pp,p_perm_low=pl)
    for y in["spend_all_q1","spend_all_q4"]:
        b,se,p,_=fit(y); res["E1 "+y]=dict(beta=b,se=se,p_cluster=p)
    json.dump(res,open("results_state2022.json","w"),indent=1)
    for k,v in res.items(): print("%-18s beta=%+.4f se=%.4f p_cl=%.3f"%(k,v["beta"],v["se"],v["p_cluster"]),("perm2s=%.3f permLow=%.3f"%(v["p_perm_2s"],v["p_perm_low"]) if "p_perm_2s" in v else ""))

else:
    pass
if '--checks' in sys.argv:
    res={}
    big=W.groupby("st").spend_acf.size().index  # placeholder
    pop={ab:fred19(f"{ab}POP") for ab in SL.state}; top5=sorted(pop,key=pop.get)[-5:]
    W["dG8"]=W.groupby("st").G.diff(8)
    variants={"drop DC/AK/HI":W[~W.st.isin(["DC","AK","HI"])],"drop top5 pop":W[~W.st.isin(top5)],"to 2023-06":W[W.date<="2023-06-30"]}
    for y in["spend_acf","DISC","ESS"]:
        for k,dat in variants.items():
            b,se,p,_=fit(y,data=dat); res[f"{k} | {y}"]=dict(beta=b,se=se,p_cluster=p)
        b,se,p,_=fit(y,G="dG8"); res[f"dG8 | {y}"]=dict(beta=b,se=se,p_cluster=p)
    # event study on acf and ess: 8-week bins relative to 2022-01-02..2022-02-27
    for y in["spend_acf","ESS"]:
        X=W.dropna(subset=[y]).copy(); dts=sorted(X.date.unique()); ref0=pd.Timestamp("2022-01-09"); 
        X["bin"]=((X.date-ref0).dt.days//56).astype(int)   # 0 = reference bin (Jan 9..Mar 5 2022 => weeks ending)
        bins=sorted(b for b in X.bin.unique() if b!=0)
        for b in bins: X[f"b{b}"]=(X.bin==b)*X.E1
        D=pd.get_dummies(X.st,drop_first=True,dtype=float); T=pd.get_dummies(X.date.astype(str),drop_first=True,dtype=float)
        M=sm.add_constant(pd.concat([X[[f"b{b}" for b in bins]],D,T],axis=1)); m=sm.OLS(X[y].values,M.values.astype(float)).fit(cov_type="cluster",cov_kwds={"groups":pd.factorize(X.st)[0]})
        res["ES "+y]={f"bin{b}":(round(float(m.params[1+i]),4),round(float(m.bse[1+i]),4)) for i,b in enumerate(bins)}
        pre=[i for i,b in enumerate(bins) if b<0]
        if pre:
            R=np.zeros((len(pre),len(m.params))); 
            for r,i in enumerate(pre): R[r,1+i]=1
            w=m.wald_test(R,scalar=True); res["ES "+y]["pre_wald_p"]=float(w.pvalue)
    json.dump(res,open("results_state2022_checks.json","w"),indent=1)
    for k,v in res.items(): print(k,v)
