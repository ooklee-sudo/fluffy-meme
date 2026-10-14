import json,numpy as np,pandas as pd
P=pd.read_csv("raw/prices.csv",index_col=0,parse_dates=True); P=P.groupby(level=0).last()
U=["^SOX","NVDA","AVGO","AMD","MU","INTC","TSM","QCOM","^GSPC"]
R=pd.DataFrame({c:np.log(P[c].dropna()).diff()*100 for c in U})
oil=pd.read_csv("raw/DCOILWTICO.csv",parse_dates=["observation_date"]).set_index("observation_date").iloc[:,0].replace(".",np.nan).astype(float).dropna(); oil=oil[oil>0]; dw=(np.log(oil).diff()*100)
res={}
# path
dates=["2026-02-27","2026-03-30","2026-04-07","2026-05-29","2026-06-10","2026-06-22","2026-06-23","2026-07-24","2026-07-27","2026-07-31","2026-08-31","2026-09-30","2026-10-13"]
L=lambda c,d: float(P[c].dropna().loc[:d].iloc[-1])
res["path"]={d:{c:round(L(c,d)/L(c,"2026-02-27")*100,1) for c in ["^SOX","NVDA","AVGO","AMD","MU","INTC","TSM","^GSPC"]} for d in dates}
# peaks and drawdowns
dd={}
for c in["^SOX","NVDA","AVGO","AMD","MU","INTC","TSM"]:
    s=P[c].dropna().loc["2026-03-02":]; pk=s.idxmax(); after=s.loc[pk:]; dd[c]=dict(peak_date=str(pk.date()),peak=float(s.max()),drop_from_peak_to_min=float((after.min()/s.max()-1)*100),min_date=str(after.idxmin().date()),last_vs_peak=float((s.iloc[-1]/s.max()-1)*100))
res["peaks"]=dd
# biggest days
post=R.loc["2026-03-02":]
for c in["^SOX","NVDA"]:
    big=post[c].abs().sort_values(ascending=False).head(10).index.sort_values()
    res["big_"+c]=[dict(date=str(d.date()),ret=round(float(post.loc[d,c]),1),sp=round(float(post.loc[d,"^GSPC"]),1),wti=round(float(dw.get(d,np.nan)),1) if d in dw.index else None,sox=round(float(post.loc[d,"^SOX"]),1),nvda=round(float(post.loc[d,"NVDA"]),1)) for d in big]
# cross-section on key days
keys=["2026-03-03","2026-03-04","2026-04-07","2026-06-11","2026-06-22","2026-06-23","2026-07-24","2026-07-27","2026-07-28","2026-07-29","2026-07-31"]
res["cross"]={d:{c:round(float(R.loc[d,c]),1) for c in U if d in R.index and not np.isnan(R.loc[d,c])} for d in keys if pd.Timestamp(d) in R.index}
# correlation of NVDA/SOX daily with S&P and WTI since war
res["corr"]={c:{"sp":float(post[c].corr(post["^GSPC"])),"wti_same_day":float(post[c].corr(dw.reindex(post.index)))} for c in["^SOX","NVDA"]}
json.dump(res,open("results_us_semis.json","w"),indent=1)
print(pd.DataFrame(res["path"]).T.to_string()); print(pd.DataFrame(res["peaks"]).T.round(1).to_string())
for k in["big_^SOX","big_NVDA"]: print(k); print(pd.DataFrame(res[k]).to_string(index=False))
print(pd.DataFrame(res["cross"]).T.to_string()); print(res["corr"])
