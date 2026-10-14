import json,numpy as np,pandas as pd
P=pd.read_csv("raw/prices.csv",index_col=0,parse_dates=True); R=np.log(P).diff().dropna()*100
S=["AAPL","MSFT","GOOGL","AMZN","META","NVDA","TSLA","AVGO"]
est=R.loc["2025-03-03":"2026-01-30"]; ab={}
for s in S:
    b,a=np.polyfit(est["^GSPC"],est[s],1); ab[s]=R[s]-(a+b*R["^GSPC"])
AR=pd.DataFrame(ab); AR["PORT"]=AR[S].mean(axis=1); AR["NDX"]=R["^IXIC"]-np.polyval(np.polyfit(est["^GSPC"],est["^IXIC"],1),R["^GSPC"])
EV=[("2026-03-06","N"),("2026-03-23","P"),("2026-04-06","N"),("2026-04-07","N"),("2026-04-13","N"),("2026-04-27","N"),("2026-05-26","P"),("2026-06-10","N"),("2026-06-11","P"),("2026-06-17","P"),("2026-06-22","N"),("2026-07-08","N"),("2026-10-05","N"),("2026-10-08","P")]
idx=R.index; days=[]
def car(d): i=idx.get_loc(pd.Timestamp(d)); return AR.iloc[i:i+2].sum()
rows=[]
for d,t in EV:
    c=car(d); rows.append(dict(date=d,type=t,port_car=c["PORT"],ndx_car=c["NDX"],raw_port=R.loc[d,S].mean(),raw_gspc=R.loc[d,"^GSPC"],raw_ndx=R.loc[d,"^IXIC"],**{s:c[s] for s in S}))
T=pd.DataFrame(rows).round(2)
# random pairs
post=idx[(idx>="2026-03-02")]
excl=set()
for d,_ in EV:
    i=idx.get_loc(pd.Timestamp(d)); excl.update([i-1,i,i+1])
cand=[idx.get_loc(x) for x in post if idx.get_loc(x) not in excl and idx.get_loc(x)+1 not in excl and idx.get_loc(x)+1<len(idx)]
pool=np.array([AR.iloc[i:i+2].sum() for i in cand]) if False else None
cp=pd.DataFrame([AR.iloc[i:i+2].sum() for i in cand])
rng=np.random.default_rng(1); n=len(EV)
absS=np.abs(cp[S].values); obs_abs=np.abs(T[S].values).mean()
sim=np.array([absS[rng.choice(len(cp),n,replace=False)].mean() for _ in range(5000)])
p_abs=float(np.mean(sim>=obs_abs))
q90=float(np.quantile(np.abs(cp["PORT"]),0.90)); share=float((T.port_car.abs()>q90).mean())
res=dict(n_events=n,n_random_pairs=len(cp),mean_abs_car_events=float(obs_abs),mean_abs_car_random=float(absS.mean()),p_T1=p_abs,q90_abs_port=q90,share_events_above_q90=share)
for t,lab in[("N","threat/breakdown"),("P","calloff/deal")]:
    sub=T[T.type==t].port_car; k=len(sub); simm=np.array([cp["PORT"].values[rng.choice(len(cp),k,replace=False)].mean() for _ in range(5000)])
    obs=float(sub.mean()); res["T2_"+t]=dict(mean=obs,n=k,p_expected_dir=float(np.mean(simm<=obs)) if t=="N" else float(np.mean(simm>=obs)),p_two=float(np.mean(np.abs(simm)>=abs(obs))))
res["table"]=T.to_dict("records"); json.dump(res,open("results_events.json","w"),indent=1,default=float)
print(T[["date","type","port_car","ndx_car","raw_port","raw_gspc","raw_ndx"]].to_string(index=False))
print({k:v for k,v in res.items() if k!="table"})
