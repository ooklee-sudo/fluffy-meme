import json,numpy as np,pandas as pd,statsmodels.api as sm
P=pd.read_csv("raw/prices.csv",index_col=0,parse_dates=True); P=P.groupby(level=0).last()
R=pd.DataFrame({c:np.log(P[c].dropna()).diff()*100 for c in P.columns})
oil=pd.read_csv("raw/DCOILWTICO.csv",parse_dates=["observation_date"]).set_index("observation_date").iloc[:,0].replace(".",np.nan).astype(float).dropna(); oil=oil[oil>0]; dw=(np.log(oil).diff()*100).dropna()
gs=R["^GSPC"].dropna()
def prev(ser,idx): v=ser.index.values; k=np.searchsorted(v,idx.values,side="left")-1; return pd.Series(np.where(k>=0,ser.values[np.clip(k,0,None)],np.nan),index=idx)
KR=["003490.KS","089590.KS","272450.KS","091810.KS","^KS11"]; US=["UAL","DAL","AAL","JETS","XOM"]; JP=["9202.T"]
est=("2025-03-03","2026-01-30"); AR={}
for c in US:
    s=R[c].dropna(); x=gs.reindex(s.index); e=s.loc[est[0]:est[1]]; xe=gs.reindex(e.index); b,a=np.polyfit(xe,e,1); AR[c]=s-(a+b*x)
for c in KR+JP:
    s=R[c].dropna(); x=prev(gs,s.index); e=s.loc[est[0]:est[1]]; xe=x.loc[e.index]; b,a=np.polyfit(xe,e,1); AR[c]=s-(a+b*x)
res={}
def cars(c):
    s=AR[c].dropna(); i0=s.index.searchsorted(pd.Timestamp("2026-03-01")); pre=s.loc[est[0]:est[1]]; out={}
    for lab,n in[("0-4",5),("0-19",20)]:
        car=s.iloc[i0:i0+n].sum(); roll=pre.rolling(n).sum().dropna(); out[lab]=dict(car=float(car),emp_p=float((roll.abs()>=abs(car)).mean()))
    out["first_day"]=str(s.index[i0].date()); return out
res["part1"]={c:cars(c) for c in AR}
base={}
for c in P.columns:
    s=P[c].dropna(); b=s.loc[:"2026-02-27"].iloc[-1]; t=s.loc["2026-03-02":]
    base[c]=dict(cum=float((s.iloc[-1]/b-1)*100),max_dd=float((t.min()/b-1)*100),trough=str(t.idxmin().date()),peak=float((t.max()/b-1)*100),peak_date=str(t.idxmax().date()))
res["part2"]=base
def oilreg(c):
    s=R[c].dropna(); d=pd.DataFrame({"y":s,"oil":prev(dw,s.index),"sp":prev(gs,s.index)}).dropna().loc["2025-01-02":"2026-10-06"]; d["war"]=(d.index>="2026-03-02").astype(float); d["ow"]=d.oil*d.war; d["sw"]=d.sp*d.war
    out={}
    for nm,dd in[("pre",d[d.war==0]),("war",d[d.war==1])]:
        m=sm.OLS(dd.y,sm.add_constant(dd[["oil","sp"]])).fit(cov_type="HAC",cov_kwds={"maxlags":5}); mo=sm.OLS(dd.y,sm.add_constant(dd[["oil"]])).fit(cov_type="HAC",cov_kwds={"maxlags":5})
        out[nm]=dict(b_oil_ctrl=float(m.params["oil"]),p_ctrl=float(m.pvalues["oil"]),b_oil_only=float(mo.params["oil"]),p_only=float(mo.pvalues["oil"]),b_sp=float(m.params["sp"]),n=int(m.nobs))
    m=sm.OLS(d.y,sm.add_constant(d[["oil","sp","war","ow","sw"]])).fit(cov_type="HAC",cov_kwds={"maxlags":5}); out["diff_p"]=float(m.pvalues["ow"]); return out
res["part3"]={c:oilreg(c) for c in["003490.KS","089590.KS","272450.KS","UAL","DAL","JETS","9202.T"]}
EV=[("2026-03-06","N"),("2026-03-23","P"),("2026-04-06","N"),("2026-04-07","N"),("2026-04-13","N"),("2026-06-10","N"),("2026-06-11","P"),("2026-06-17","P"),("2026-06-22","N"),("2026-07-08","N"),("2026-10-05","N"),("2026-10-08","P")]
rng=np.random.default_rng(21); p4={}
def etest(series,mode,lab):
    s=series.dropna(); idx=s.index; rows=[]
    for d,t in EV:
        ts=pd.Timestamp(d)
        if mode=="us": i=idx.get_loc(ts); v=s.iloc[i:i+2].sum()
        else: j=idx.searchsorted(ts,side="right"); v=s.iloc[j] if j<len(s) else np.nan
        rows.append((d,t,float(v)))
    T=pd.DataFrame(rows,columns=["d","t","v"]).dropna(); post=s.loc["2026-03-02":]; pool=post.rolling(2).sum().dropna() if mode=="us" else post
    ex=set(pd.Timestamp(d) for d,_ in EV); pool=pool[[i for i in pool.index if i not in ex]]
    obs=T.v.abs().mean(); sim=np.array([pool.abs().sample(len(T),random_state=int(rng.integers(1e9))).mean() for _ in range(4000)]); N=T[T.t=="N"].v; Pp=T[T.t=="P"].v
    sN=np.array([pool.sample(len(N),random_state=int(rng.integers(1e9))).mean() for _ in range(3000)]); sP=np.array([pool.sample(len(Pp),random_state=int(rng.integers(1e9))).mean() for _ in range(3000)])
    p4[lab]=dict(mean_abs=float(obs),mean_abs_random=float(pool.abs().mean()),p_mag=float(np.mean(sim>=obs)),threat=float(N.mean()),p_threat_neg=float(np.mean(sN<=N.mean())),calloff=float(Pp.mean()),p_calloff_pos=float(np.mean(sP>=Pp.mean())),rows=T.round(2).to_dict("records"))
etest(AR["003490.KS"],"kr","Korean Air (next KR day)"); etest(AR["UAL"],"us","United (days 0-1)"); etest(AR["DAL"],"us","Delta (days 0-1)")
res["part4"]=p4; json.dump(res,open("results_airlines.json","w"),indent=1,default=float)
for c,v in res["part1"].items(): print("P1",c,v["first_day"],"CAR0-4 %.1f (p=%.2f) | CAR0-19 %.1f (p=%.2f)"%(v["0-4"]["car"],v["0-4"]["emp_p"],v["0-19"]["car"],v["0-19"]["emp_p"]))
for c,v in base.items(): print("P2",c,"cum %.1f | maxDD %.1f (%s) | peak %.1f (%s)"%(v["cum"],v["max_dd"],v["trough"],v["peak"],v["peak_date"]))
for c,v in res["part3"].items(): print("P3",c,"pre oil(ctrl) %+.3f p=%.2f | war oil(ctrl) %+.3f p=%.2f | war oil-only %+.3f p=%.2f | diff p=%.2f"%(v["pre"]["b_oil_ctrl"],v["pre"]["p_ctrl"],v["war"]["b_oil_ctrl"],v["war"]["p_ctrl"],v["war"]["b_oil_only"],v["war"]["p_only"],v["diff_p"]))
for k,v in p4.items(): print("P4",k,{a:round(b,3) for a,b in v.items() if a!="rows"})
print(pd.DataFrame(p4["Korean Air (next KR day)"]["rows"]).to_string(index=False))
