import json,numpy as np,pandas as pd,statsmodels.api as sm
P=pd.read_csv("../korea/raw/prices.csv",index_col=0,parse_dates=True); P=P.groupby(level=0).last()
Q=pd.read_csv("raw/prices.csv",index_col=0,parse_dates=True); Q=Q.groupby(level=0).last()
for c in["^N225","^TWII"]: P[c]=Q[c]
R=pd.DataFrame({c:np.log(P[c].dropna()).diff()*100 for c in P.columns})
oil=pd.read_csv("raw/DCOILWTICO.csv",parse_dates=["observation_date"]).set_index("observation_date").iloc[:,0].replace(".",np.nan).astype(float).dropna(); oil=oil[oil>0]; dw=(np.log(oil).diff()*100).dropna()
gs=R["^GSPC"].dropna()
def prev(ser,idx):
    v=ser.index.values; k=np.searchsorted(v,idx.values,side="left")-1; return pd.Series(np.where(k>=0,ser.values[np.clip(k,0,None)],np.nan),index=idx)
res={}
for c in["^KS11","^KQ11","005930.KS","000660.KS","^N225","^TWII","KRW=X"]:
    s=R[c].dropna(); d=pd.DataFrame({"y":s,"oil":prev(dw,s.index),"sp":prev(gs,s.index)}).dropna(subset=["oil","sp"])
    d=d.loc["2025-01-02":"2026-10-06"]; d["war"]=(d.index>="2026-03-02").astype(float); d["ow"]=d.oil*d.war; d["sw"]=d.sp*d.war
    out={}
    for nm,dd in[("pre",d[d.war==0]),("war",d[d.war==1])]:
        m=sm.OLS(dd.y,sm.add_constant(dd[["oil","sp"]])).fit(cov_type="HAC",cov_kwds={"maxlags":5}); out[nm]=dict(b_oil=float(m.params["oil"]),se=float(m.bse["oil"]),p=float(m.pvalues["oil"]),b_sp=float(m.params["sp"]),r2=float(m.rsquared),n=int(m.nobs),sd_oil=float(dd.oil.std()))
    m=sm.OLS(d.y,sm.add_constant(d[["oil","sp","war","ow","sw"]])).fit(cov_type="HAC",cov_kwds={"maxlags":5}); out["b_oil_change_war"]=dict(coef=float(m.params["ow"]),p=float(m.pvalues["ow"]))
    # oil only (no S&P control), war period
    dd=d[d.war==1]; m2=sm.OLS(dd.y,sm.add_constant(dd[["oil"]])).fit(cov_type="HAC",cov_kwds={"maxlags":5}); out["war_oil_only"]=dict(b=float(m2.params["oil"]),p=float(m2.pvalues["oil"]),r2=float(m2.rsquared))
    res[c]=out
# oil level
res["WTI"]={"27feb":float(oil.loc[:"2026-02-27"].iloc[-1]),"last":float(oil.iloc[-1]),"max_after_mar2":float(oil.loc["2026-03-02":].max()),"max_date":str(oil.loc["2026-03-02":].idxmax().date()),"daily_sd_pre":float(dw.loc["2025-01-02":"2026-02-27"].std()),"daily_sd_war":float(dw.loc["2026-03-02":].std())}
json.dump(res,open("results_oil.json","w"),indent=1)
for c,v in res.items():
    if c=="WTI": print(c,v); continue
    print(c,"pre b_oil=%+.3f (p=%.2f) | war b_oil=%+.3f (p=%.2f), R2=%.2f | change p=%.2f | war oil-only b=%+.3f (p=%.2f)"%(v["pre"]["b_oil"],v["pre"]["p"],v["war"]["b_oil"],v["war"]["p"],v["war"]["r2"],v["b_oil_change_war"]["p"],v["war_oil_only"]["b"],v["war_oil_only"]["p"]))
