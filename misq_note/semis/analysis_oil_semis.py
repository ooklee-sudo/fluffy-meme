import json,numpy as np,pandas as pd,statsmodels.api as sm
P=pd.read_csv("../korea/raw/prices.csv",index_col=0,parse_dates=True); P=P.groupby(level=0).last()
Q=pd.read_csv("raw/prices.csv",index_col=0,parse_dates=True); Q=Q.groupby(level=0).last(); P["^SOX"]=Q["^SOX"]
oil=pd.read_csv("raw/DCOILWTICO.csv",parse_dates=["observation_date"]).set_index("observation_date").iloc[:,0].replace(".",np.nan).astype(float).dropna(); oil=oil[oil>0]
R=pd.DataFrame({c:np.log(P[c].dropna()).diff()*100 for c in P.columns}); dw=(np.log(oil).diff()*100).dropna()
def prev(ser,idx): v=ser.index.values; k=np.searchsorted(v,idx.values,side="left")-1; return pd.Series(np.where(k>=0,ser.values[np.clip(k,0,None)],np.nan),index=idx)
res={}
# path table: WTI vs Samsung/SK hynix/SOX at selected dates (index = 27 Feb 2026 close =100)
dates=["2026-02-27","2026-03-31","2026-04-07","2026-05-29","2026-06-10","2026-06-11","2026-06-22","2026-06-30","2026-07-31","2026-08-31","2026-09-30","2026-10-06"]
def lv(s,d): s=s.dropna(); return float(s.loc[:d].iloc[-1])
tab={}
for d in dates:
    tab[d]=dict(WTI=lv(oil,d),Samsung=lv(P["005930.KS"],d)/lv(P["005930.KS"],"2026-02-27")*100,SKhynix=lv(P["000660.KS"],d)/lv(P["000660.KS"],"2026-02-27")*100,KOSPI=lv(P["^KS11"],d)/lv(P["^KS11"],"2026-02-27")*100,SOX=lv(P["^SOX"],d)/lv(P["^SOX"],"2026-02-27")*100)
res["path"]={d:{k:round(v,1) for k,v in x.items()} for d,x in tab.items()}
# daily/weekly co-movement by window
def window(c,start,end,controls):
    s=R[c].dropna(); d=pd.DataFrame({"y":s,"oil":prev(dw,s.index),"sp":prev(R["^GSPC"].dropna(),s.index),"sox":prev(R["^SOX"].dropna(),s.index)}).dropna(subset=["oil"]); d=d.loc[start:end].dropna()
    out={}
    m=sm.OLS(d.y,sm.add_constant(d[["oil"]])).fit(cov_type="HAC",cov_kwds={"maxlags":5}); out["oil_only"]=dict(b=float(m.params["oil"]),p=float(m.pvalues["oil"]),r2=float(m.rsquared),n=int(m.nobs))
    X=d[["oil"]+controls]; m=sm.OLS(d.y,sm.add_constant(X)).fit(cov_type="HAC",cov_kwds={"maxlags":5}); out["with_controls"]=dict(b=float(m.params["oil"]),p=float(m.pvalues["oil"]),r2=float(m.rsquared))
    out["corr_daily"]=float(d.y.corr(d.oil)); return out
for lab,(a,b) in{"since_war (2 Mar-6 Oct)":("2026-03-02","2026-10-06"),"since_1_Jun":("2026-06-01","2026-10-06"),"since_22_Jun_peak":("2026-06-23","2026-10-06"),"March-May":("2026-03-02","2026-05-29")}.items():
    res[lab]={c:window(c,a,b,["sox"]) for c in["005930.KS","000660.KS","^KS11"]}
# weekly levels correlation (log changes) over since 1 Jun
W=pd.DataFrame({"hynix":np.log(P["000660.KS"].dropna()),"samsung":np.log(P["005930.KS"].dropna()),"oil":np.log(oil)}).dropna().loc["2026-06-01":"2026-10-06"].resample("W-FRI").last().diff().dropna()*100
res["weekly_since_1Jun"]={"n":int(len(W)),"corr_hynix_oil":float(W.hynix.corr(W.oil)),"corr_samsung_oil":float(W.samsung.corr(W.oil))}
# oil spikes: 10 largest daily WTI moves since 1 Jun and Korean chip reaction next day
bigs=dw.loc["2026-06-01":].abs().sort_values(ascending=False).head(8).index.sort_values()
rows=[]
for d in bigs:
    nxt=R.index[R.index>d]; 
    if len(nxt)==0: continue
    n=nxt[0]; rows.append(dict(date=str(d.date()),wti=round(float(dw.loc[d]),1),hynix_next=round(float(R.loc[n,"000660.KS"]),1),samsung_next=round(float(R.loc[n,"005930.KS"]),1),kospi_next=round(float(R.loc[n,"^KS11"]),1)))
res["big_oil_days_since_1Jun"]=rows
json.dump(res,open("results_oil_semis.json","w"),indent=1)
print(pd.DataFrame(res["path"]).T.to_string())
for k in["since_war (2 Mar-6 Oct)","since_1_Jun","since_22_Jun_peak","March-May"]:
    for c,v in res[k].items(): print(k,c,"oil-only b=%+.3f p=%.2f r2=%.3f | +SOX ctrl b=%+.3f p=%.2f | corr %.2f n=%d"%(v["oil_only"]["b"],v["oil_only"]["p"],v["oil_only"]["r2"],v["with_controls"]["b"],v["with_controls"]["p"],v["corr_daily"],v["oil_only"]["n"]))
print(res["weekly_since_1Jun"]); print(pd.DataFrame(rows).to_string(index=False))
