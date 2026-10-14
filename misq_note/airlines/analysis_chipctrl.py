import json,numpy as np,pandas as pd,statsmodels.api as sm
P=pd.read_csv("raw/prices.csv",index_col=0,parse_dates=True); P=P.groupby(level=0).last()
S=pd.read_csv("raw/semis_prices.csv",index_col=0,parse_dates=True); S=S.groupby(level=0).last()
for c in["^SOX","005930.KS","000660.KS"]: P[c]=S[c]
R=pd.DataFrame({c:np.log(P[c].dropna()).diff()*100 for c in P.columns})
oil=pd.read_csv("raw/DCOILWTICO.csv",parse_dates=["observation_date"]).set_index("observation_date").iloc[:,0].replace(".",np.nan).astype(float).dropna(); oil=oil[oil>0]; dw=(np.log(oil).diff()*100).dropna()
def prev(ser,idx): ser=ser.dropna(); v=ser.index.values; k=np.searchsorted(v,idx.values,side="left")-1; return pd.Series(np.where(k>=0,ser.values[np.clip(k,0,None)],np.nan),index=idx)
res={}
for c in["003490.KS","089590.KS","272450.KS","9202.T"]:
    s=R[c].dropna(); d=pd.DataFrame({"y":s,"oil":prev(dw,s.index),"sp":prev(R["^GSPC"],s.index),"sox":prev(R["^SOX"],s.index),"chip":((R["005930.KS"]+R["000660.KS"])/2).reindex(s.index)}).dropna().loc["2025-01-02":"2026-10-06"]
    d["war"]=(d.index>="2026-03-02").astype(float)
    specs={"S0":["oil"],"S1":["oil","sp"],"S2":["oil","sp","sox"],"S3":["oil","sp","sox","chip"]}
    out={}
    for sn,cols in specs.items():
        o={}
        for nm,dd in[("pre",d[d.war==0]),("war",d[d.war==1])]:
            m=sm.OLS(dd.y,sm.add_constant(dd[cols])).fit(cov_type="HAC",cov_kwds={"maxlags":5}); o[nm]=dict(b=float(m.params["oil"]),se=float(m.bse["oil"]),p=float(m.pvalues["oil"]),r2=float(m.rsquared),n=int(m.nobs),b_chip=float(m.params["chip"]) if "chip" in cols else None)
        X=d[cols].copy(); X["war"]=d.war; X["ow"]=d.oil*d.war
        m=sm.OLS(d.y,sm.add_constant(X)).fit(cov_type="HAC",cov_kwds={"maxlags":5}); o["diff_p"]=float(m.pvalues["ow"]); o["diff"]=float(m.params["ow"]); out[sn]=o
    res[c]=out
# first stage: chip factor on oil, war period
d=pd.DataFrame({"chip":((R["005930.KS"]+R["000660.KS"])/2),"oil":prev(dw,R["005930.KS"].dropna().index).reindex(R.index)}).dropna()
res["chip_on_oil"]={}
for nm,(a,b) in{"pre":("2025-01-02","2026-02-27"),"war":("2026-03-02","2026-10-06")}.items():
    dd=d.loc[a:b]; m=sm.OLS(dd.chip,sm.add_constant(dd.oil)).fit(cov_type="HAC",cov_kwds={"maxlags":5}); res["chip_on_oil"][nm]=dict(b=float(m.params["oil"]),p=float(m.pvalues["oil"]),r2=float(m.rsquared),n=int(m.nobs))
json.dump(res,open("results_chipctrl.json","w"),indent=1)
for c in["003490.KS","089590.KS","272450.KS","9202.T"]:
    print(c)
    for sn in["S0","S1","S2","S3"]:
        o=res[c][sn]; print("  %s pre b=%+.3f (p=%.2f, R2=%.2f) | war b=%+.3f (p=%.2f, R2=%.2f, chip b=%s) | diff=%+.3f p=%.2f"%(sn,o["pre"]["b"],o["pre"]["p"],o["pre"]["r2"],o["war"]["b"],o["war"]["p"],o["war"]["r2"],("%.2f"%o["war"]["b_chip"] if o["war"]["b_chip"] is not None else "-"),o["diff"],o["diff_p"]))
print(res["chip_on_oil"])
