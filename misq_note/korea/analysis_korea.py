import json,numpy as np,pandas as pd,statsmodels.api as sm
P=pd.read_csv("raw/prices.csv",index_col=0,parse_dates=True); P=P.groupby(level=0).last(); R=pd.DataFrame({c:np.log(P[c].dropna()).diff()*100 for c in P.columns})  # per-series returns (bug fix: union-index diff dropped returns after one-market holidays)
KR=["^KS11","^KQ11","005930.KS","000660.KS"]
kr=R[KR+["KRW=X"]].dropna(subset=["^KS11"]); us=R[["^GSPC","^IXIC"]].dropna()
# previous US session return aligned to each Korean date t: latest US date strictly before t
usd=us.index.values; prev=pd.Series([us["^GSPC"].iloc[np.searchsorted(usd,t.to_datetime64(),side="left")-1] if np.searchsorted(usd,t.to_datetime64(),side="left")>0 else np.nan for t in kr.index],index=kr.index)
kr["us_prev"]=prev; kr=kr.dropna(subset=["us_prev"])
pre=kr.loc["2025-01-02":"2026-02-27"]; war=kr.loc["2026-03-02":]
res={}
for c in KR:
    out={}
    for nm,d in[("pre",pre),("war",war)]:
        dd=d.dropna(subset=[c]); m=sm.OLS(dd[c],sm.add_constant(dd["us_prev"])).fit(cov_type="HAC",cov_kwds={"maxlags":5}); out[nm]=dict(b=float(m.params["us_prev"]),se=float(m.bse["us_prev"]),r2=float(m.rsquared),n=int(m.nobs),mean_abs=float(dd[c].abs().mean()))
    # Chow-type: interaction
    a=kr.dropna(subset=[c]).copy(); a["war"]=(a.index>="2026-03-02").astype(float); a["x"]=a.us_prev; a["xw"]=a.x*a.war
    m=sm.OLS(a[c],sm.add_constant(a[["x","war","xw"]])).fit(cov_type="HAC",cov_kwds={"maxlags":5}); out["b_diff_war"]=dict(coef=float(m.params["xw"]),p=float(m.pvalues["xw"]))
    res["A "+c]=out
# Part B
b,a0=np.polyfit(pre.us_prev,pre["^KS11"],1)
kr["AR"]=kr["^KS11"]-(a0+b*kr.us_prev)
EV=[("2026-03-06","N"),("2026-03-23","P"),("2026-04-06","N"),("2026-04-07","N"),("2026-04-13","N"),("2026-06-10","N"),("2026-06-11","P"),("2026-06-17","P"),("2026-06-22","N"),("2026-07-08","N"),("2026-10-05","N"),("2026-10-08","P")]
ki=kr.index; rows=[]
for d,t in EV:
    nxt=ki[ki>pd.Timestamp(d)][0] if (ki>pd.Timestamp(d)).any() else None
    same=pd.Timestamp(d) if pd.Timestamp(d) in ki else None
    rows.append(dict(us_date=d,type=t,kr_next=str(nxt.date()) if nxt is not None else None,raw_next=float(kr.loc[nxt,"^KS11"]) if nxt is not None else np.nan,ar_next=float(kr.loc[nxt,"AR"]) if nxt is not None else np.nan,raw_same=float(kr.loc[same,"^KS11"]) if same is not None else np.nan,ar_same=float(kr.loc[same,"AR"]) if same is not None else np.nan,us_ret=float(R.loc[d,"^GSPC"]),sec_next=float(kr.loc[nxt,"005930.KS"]) if nxt is not None else np.nan,hynix_next=float(kr.loc[nxt,"000660.KS"]) if nxt is not None else np.nan))
T=pd.DataFrame(rows); res["B_table"]=T.round(2).to_dict("records")
warv=kr.loc["2026-03-02":]; ev_next=set(pd.to_datetime(T.kr_next.dropna())); ev_same=set(pd.Timestamp(d) for d,_ in EV)
non=warv.drop([x for x in (ev_next|ev_same) if x in warv.index])
rng=np.random.default_rng(7)
for lab,col in[("next","ar_next"),("same","ar_same")]:
    obs=T[col].abs().mean(); n=T[col].notna().sum(); sim=np.array([non.AR.abs().sample(n,random_state=int(rng.integers(1e9))).mean() for _ in range(5000)])
    N=T[T.type=="N"][col].dropna(); Pp=T[T.type=="P"][col].dropna()
    simN=np.array([non.AR.sample(len(N),random_state=int(rng.integers(1e9))).mean() for _ in range(5000)]); simP=np.array([non.AR.sample(len(Pp),random_state=int(rng.integers(1e9))).mean() for _ in range(5000)])
    res["B_"+lab]=dict(mean_abs_AR_events=float(obs),mean_abs_AR_random=float(non.AR.abs().mean()),p_magnitude=float(np.mean(sim>=obs)),meanAR_threats=float(N.mean()),p_threat_neg=float(np.mean(simN<=N.mean())),meanAR_calloffs=float(Pp.mean()),p_calloff_pos=float(np.mean(simP>=Pp.mean())),n=int(n))
# Part C
pre_ks=R.loc["2025-01-02":"2026-02-27"]; war_ks=R.loc["2026-03-02":]
res["C"]={c:dict(pre_mean_abs=float(pre_ks[c].abs().mean()),war_mean_abs=float(war_ks[c].abs().mean())) for c in KR+["KRW=X"]}
lv=P[["^KS11","005930.KS","000660.KS","KRW=X"]]; 
res["C"]["cum_since_Feb27_pct"]={c:float((lv[c].dropna().iloc[-1]/lv[c].dropna().loc[:"2026-02-27"].iloc[-1]-1)*100) for c in lv.columns}
res["C"]["min_drawdown_after_Mar2_KOSPI_pct"]=float(((lv["^KS11"].loc["2026-03-02":]/lv["^KS11"].loc["2026-02-27"]-1).min())*100)
json.dump(res,open("results_korea.json","w"),indent=1,default=float)
for k in res:
    if k.startswith("A "): print(k,json.dumps(res[k],default=float))
print(T.round(2).to_string(index=False)); print(json.dumps({k:res[k] for k in["B_next","B_same","C"]},indent=1,default=float))
