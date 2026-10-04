"""UK ONS/Textkernel NEW online job adverts by SOC 2020 4-digit unit group, monthly Jan 2017-Aug 2026 (Total UK).
Groups fixed a priori from occupation labels only (before looking at outcomes):
 PROD   (image/video production): 2142 graphic & multimedia designers, 3411 artists, 3417 photographers/AV operators, 2141 web design professionals
 DIRECT (creative direction/producing): 3416 arts officers, producers & directors, 2494 advertising accounts managers & creative directors, 1255 managers in the creative industries
 TEXT   (text production): 3412 authors, writers & translators, 2492 journalists & reporters, 2491 editors
Outcome: ln of 12-month-trailing sum of new adverts (removes seasonality), relative to base year Jul 2021-Jun 2022 (pre image-gen).
Statistic: group mean minus control-pool mean of [ln S(t) - ln S(base)] at horizons; randomization over random sets of equal size from the control pool.
Event times (to be verified): text-to-image public release Jul-Aug 2022; ChatGPT Nov 2022; DALL-E 3 / GPT-4V Oct 2023; Sora announced Feb 2024, released Dec 2024."""
import re, random, numpy as np, pandas as pd
r=pd.read_csv("data/ons/uk_soc4_new_adverts_monthly.csv",dtype={"soc4":str})
mc=[c for c in r.columns if re.match(r"[A-Z][a-z]{2}-\d\d$",c)]
for c in mc: r[c]=pd.to_numeric(r[c],errors="coerce")
r=r.set_index("soc4"); X=r[mc]; X.columns=pd.to_datetime(["01-"+c for c in mc],format="%d-%b-%y")
X=X.T.interpolate(method='linear',limit=2,limit_area='inside').T   # impute suppressed/missing months (Mar-26 missing for all occupations; Jun/Jul-25, Jun-26 for many)
S=X.T.rolling(12,min_periods=12).sum().T   # trailing 12m sum
PROD=["2142","3411","3417","2141"]; DIRECT=["3416","2494","1255"]; TEXT=["3412","2492","2491"]; G={"PROD":PROD,"DIRECT":DIRECT,"TEXT":TEXT}
base=pd.Timestamp("2022-06-01")   # S = Jul 2021..Jun 2022
vol=X.loc[:,pd.Timestamp("2021-07-01"):pd.Timestamp("2022-06-01")].sum(axis=1)
ok=(vol>=1000)&S.loc[:,pd.Timestamp('2019-06-01'):pd.Timestamp('2026-05-01')].notna().all(axis=1)&(S.loc[:,pd.Timestamp('2019-06-01'):pd.Timestamp('2026-05-01')]>0).all(axis=1)
excl=set(PROD)|set(DIRECT)|set(TEXT); pool=[t for t in r.index if ok[t] and t not in excl]
white=[t for t in pool if t[0] in "1235"]   # SOC major groups 1-3 = managers, professionals, associate professionals
ok=ok&S[pd.Timestamp('2026-06-01')].notna()
print("groups present:",{g:[t for t in l if t in r.index and ok[t]] for g,l in G.items()}); print("pool sizes: all",len(pool),"| SOC major groups 1-3 (managerial/professional/associate prof.)",len(white))
rng=random.Random(5)
def dlog(t): return np.log(S.loc[t])-np.log(S.loc[t,base])
hz={"Jul22-Jun23":"2023-06-01","Jul23-Jun24":"2024-06-01","Jul24-Jun25":"2025-06-01","Jul25-Jun26 (Mar-26 imputed)":"2026-06-01"}
def stat(g,pl,date,R=10000):
    d=pd.Series({t:dlog(t)[pd.Timestamp(date)] for t in set(pl)|set(G[g]) if t in r.index and ok[t]})
    gt=[t for t in G[g] if t in d.index]; obs=d[gt].mean()-d[pl].mean(); k=len(gt); dd=d[pl].values; cnt=0
    for _ in range(R):
        s=rng.sample(range(len(pl)),k); cnt+=abs(dd[s].mean()-dd.mean())>=abs(obs)
    return obs,(cnt+1)/(R+1)
print("\nln change in trailing-12m new adverts since Jul21-Jun22 base: group minus controls (randomization p)")
print("group".ljust(8),"pool".ljust(8),*[h.rjust(30) for h in hz])
res=[]
for g in G:
    for nm,pl in (("all",pool),("SOC1-3",white)):
        row=[stat(g,pl,dt) for dt in hz.values()]; res.append((g,nm,*[x for o in row for x in o]))
        print(g.ljust(8),nm.ljust(8),*[f"{o:+.3f} ({p:.3f})".rjust(30) for o,p in row])
pd.DataFrame(res,columns=["group","pool"]+[f"{h}_{k}" for h in hz for k in ("est","p")]).to_csv("data/ons/uk_soc4_results.csv",index=False)
# pre-trend: same statistic one year earlier (base Jun 2021 -> Jun 2022 falls in the base year, so use Jun 2019 base -> Jun 2021)
b0=pd.Timestamp("2019-06-01"); d=pd.Series({t:np.log(S.loc[t,pd.Timestamp("2021-06-01")])-np.log(S.loc[t,b0]) for t in r.index if ok[t] and np.isfinite(S.loc[t,b0])})
print("\npre-period placebo (ln change Jun2019->Jun2021, includes COVID): "+", ".join(f"{g} {d[[t for t in G[g] if t in d.index]].mean()-d[[t for t in pool if t in d.index]].mean():+.3f}" for g in G))
# 12-month-ago comparison path for plot
rows=[]
for dt in S.columns[S.columns>=pd.Timestamp("2019-01-01")]:
    d=np.log(S.loc[:,dt])-np.log(S[base]); rows.append((dt,*[d[[t for t in G[g] if ok.get(t,False)]].mean()-d[pool].mean() for g in G]))
path=pd.DataFrame(rows,columns=["date"]+list(G)); path.to_csv("data/ons/uk_soc4_path.csv",index=False)
print(path[path.date.isin(pd.to_datetime(["2020-06-01","2021-06-01","2022-06-01","2022-12-01","2023-06-01","2023-12-01","2024-06-01","2024-12-01","2025-06-01","2025-12-01","2026-06-01"]))].to_string(index=False,float_format=lambda v:f'{v:+.3f}'))
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig,ax=plt.subplots(figsize=(8,4)); 
for g,c in zip(G,("#d62728","#1f77b4","#2ca02c")): ax.plot(path.date,path[g],label=g,color=c)
for d,l in (("2022-07-01","text-to-image"),("2022-11-30","ChatGPT"),("2023-10-01","DALL-E 3"),("2024-12-01","video gen")): ax.axvline(pd.Timestamp(d),color="gray",ls=":",lw=1)
ax.axhline(0,color="black",lw=.6); ax.set_ylabel("ln gap in trailing-12m new adverts\n(group minus controls, base Jul21-Jun22)"); ax.legend(frameon=False); ax.set_title("UK new online job adverts by SOC group (exploratory)",fontsize=10); plt.tight_layout(); plt.savefig("data/ons/uk_soc4_gap.png",dpi=130)
