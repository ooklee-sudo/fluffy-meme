import json,numpy as np,pandas as pd,statsmodels.api as sm
P=pd.read_csv("raw/prices.csv",index_col=0,parse_dates=True); P=P.groupby(level=0).last()
R=pd.DataFrame({c:np.log(P[c].dropna()).diff()*100 for c in P.columns})
US=["^SOX","NVDA","AVGO","AMD","MU","INTC","TSM","QCOM"]; AS={"2330.TW":"TW","^TWII":"TW","005930.KS":"KR","000660.KS":"KR","^KS11":"KR","^N225":"JP","8035.T":"JP"}
gs=R["^GSPC"].dropna(); gsd=gs.index.values
def prev_us(idx): 
    k=np.searchsorted(gsd,idx.values,side="left")-1; return pd.Series(np.where(k>=0,gs.values[np.clip(k,0,None)],np.nan),index=idx)
est=("2025-03-03","2026-01-30"); AR={}; BETA={}
for c in US:
    s=R[c].dropna(); x=gs.reindex(s.index); ok=x.notna(); e=s.loc[est[0]:est[1]]; xe=gs.reindex(e.index)
    b,a=np.polyfit(xe.dropna(),e[xe.notna()],1); AR[c]=s-(a+b*x); BETA[c]=float(b)
for c in AS:
    s=R[c].dropna(); x=prev_us(s.index); e=s.loc[est[0]:est[1]]; xe=x.loc[e.index]
    b,a=np.polyfit(xe,e,1); AR[c]=s-(a+b*x); BETA[c]=float(b)
res={"beta_pre":BETA}
# Part 1
def cars(c):
    s=AR[c]; idx=s.index; i0=idx.searchsorted(pd.Timestamp("2026-03-01"))   # first local trading date after the weekend (>=Mar 1)
    pre=s.loc[est[0]:est[1]]; out={}
    for lab,n in[("0-4",5),("0-19",20)]:
        car=s.iloc[i0:i0+n].sum(); roll=pre.rolling(n).sum().dropna(); out[lab]=dict(car=float(car),emp_p=float((roll.abs()>=abs(car)).mean()),first_day=str(idx[i0].date()))
    return out
res["part1"]={c:cars(c) for c in list(AR)}
# Part 2
lv=P.copy(); base={}
for c in lv.columns:
    s=lv[c].dropna(); b=s.loc[:"2026-02-27"].iloc[-1]; t=s.loc["2026-03-02":]; base[c]=dict(cum_to_end=float((s.iloc[-1]/b-1)*100),max_dd=float((t.min()/b-1)*100),trough_date=str(t.idxmin().date()),peak_gain=float((t.max()/b-1)*100),peak_date=str(t.idxmax().date()))
res["part2"]=base
# Part 3
def trans(c):
    s=R[c].dropna(); x=R["^SOX"].dropna(); xv=x.index.values
    k=np.searchsorted(xv,s.index.values,side="left")-1; X=pd.Series(np.where(k>=0,x.values[np.clip(k,0,None)],np.nan),index=s.index)
    d=pd.DataFrame({"y":s,"x":X}).dropna(); d=d.loc["2025-01-01":]; d["war"]=(d.index>="2026-03-02").astype(float); d["xw"]=d.x*d.war
    out={}
    for nm,dd in[("pre",d[d.war==0]),("war",d[d.war==1])]:
        m=sm.OLS(dd.y,sm.add_constant(dd.x)).fit(cov_type="HAC",cov_kwds={"maxlags":5}); out[nm]=dict(b=float(m.params["x"]),se=float(m.bse["x"]),r2=float(m.rsquared),n=int(m.nobs))
    m=sm.OLS(d.y,sm.add_constant(d[["x","war","xw"]])).fit(cov_type="HAC",cov_kwds={"maxlags":5}); out["diff_p"]=float(m.pvalues["xw"]); return out
res["part3"]={c:trans(c) for c in["005930.KS","000660.KS","2330.TW","^KS11","^TWII"]}
# Part 4
EV=[("2026-03-06","N"),("2026-03-23","P"),("2026-04-06","N"),("2026-04-07","N"),("2026-04-13","N"),("2026-06-10","N"),("2026-06-11","P"),("2026-06-17","P"),("2026-06-22","N"),("2026-07-08","N"),("2026-10-05","N"),("2026-10-08","P")]
rng=np.random.default_rng(11); p4={}
def event_test(series,mode,lab):
    s=series.dropna(); idx=s.index; rows=[]
    for d,t in EV:
        ts=pd.Timestamp(d)
        if mode=="us": i=idx.get_loc(ts); v=s.iloc[i:i+2].sum()
        else: j=idx.searchsorted(ts,side="right"); v=s.iloc[j] if j<len(s) else np.nan
        rows.append((d,t,float(v)))
    T=pd.DataFrame(rows,columns=["d","t","v"]).dropna()
    post=s.loc["2026-03-02":]; pool=post.rolling(2).sum().dropna() if mode=="us" else post
    ex=set(pd.Timestamp(d) for d,_ in EV); pool=pool[[i for i in pool.index if i not in ex]]
    obs=T.v.abs().mean(); sim=np.array([pool.abs().sample(len(T),random_state=int(rng.integers(1e9))).mean() for _ in range(5000)])
    N=T[T.t=="N"].v; Pp=T[T.t=="P"].v
    simN=np.array([pool.sample(len(N),random_state=int(rng.integers(1e9))).mean() for _ in range(3000)]); simP=np.array([pool.sample(len(Pp),random_state=int(rng.integers(1e9))).mean() for _ in range(3000)])
    p4[lab]=dict(mean_abs_events=float(obs),mean_abs_random=float(pool.abs().mean()),p_mag=float(np.mean(sim>=obs)),threat_mean=float(N.mean()),p_threat_neg=float(np.mean(simN<=N.mean())),calloff_mean=float(Pp.mean()),p_calloff_pos=float(np.mean(simP>=Pp.mean())),table=T.round(2).to_dict("records"))
event_test(AR["^SOX"],"us","SOX (US, days 0-1)"); event_test(AR["NVDA"],"us","NVDA (US, days 0-1)")
event_test(AR["005930.KS"],"kr","Samsung (next KR day)"); event_test(AR["000660.KS"],"kr","SK hynix (next KR day)"); event_test(AR["2330.TW"],"kr","TSMC Taiwan (next TW day)")
# share of top 20 |SOX AR| days near events
sx=AR["^SOX"].loc["2026-03-02":].dropna(); top=sx.abs().sort_values(ascending=False).head(20).index
near=sum(any(abs((d-pd.Timestamp(e)).days)<=1 for e,_ in EV) for d in top); res["top20_SOX_near_events"]=dict(n=int(near),share_days_near_events=float(len({pd.Timestamp(e)+pd.Timedelta(days=k) for e,_ in EV for k in(-1,0,1)})/len(sx)))
res["part4"]=p4
json.dump(res,open("results_semis.json","w"),indent=1,default=float)
print("betas",{k:round(v,2) for k,v in BETA.items()})
for c,v in res["part1"].items(): print("P1",c,v["0-4"]["first_day"],"CAR0-4 %.1f p=%.2f | CAR0-19 %.1f p=%.2f"%(v["0-4"]["car"],v["0-4"]["emp_p"],v["0-19"]["car"],v["0-19"]["emp_p"]))
for c,v in base.items(): print("P2",c,"cum %.1f maxDD %.1f (%s) peak %.1f (%s)"%(v["cum_to_end"],v["max_dd"],v["trough_date"],v["peak_gain"],v["peak_date"]))
for c,v in res["part3"].items(): print("P3",c,v)
for k,v in p4.items(): print("P4",k,{a:round(b,3) for a,b in v.items() if a!="table"})
print(res["top20_SOX_near_events"])
