import json,numpy as np,pandas as pd,warnings
warnings.filterwarnings("ignore")
d=pd.read_csv("raw/monthly.csv",encoding="latin-1"); d=d[d.Statistical_Group.str.startswith("2-Removed Taxable")]
d["p"]=[pd.Period(f"{y}-{m:02d}","M") for y,m in zip(d.Year,d.CY_Month_Number)]
sel={"cigarettes":"1-Cigarettes","cigars_small_large_le":"2-Large Cigars <= $763.222 and Small Cigars","cigars_large_gt":"3-Large Cigars > $763.222","RYO":"7-Roll-Your-Own Tobacco","snuff":"8-Snuff","chewing":"5-Chewing Tobacco","pipe":"6-Pipe Tobacco"}
D={}
for k,v in sel.items():
    x=d[d.Statistical_Detail==v]; D[k]=x.groupby("p").Value.sum().astype(float)
D=pd.DataFrame(D).sort_index(); print(D.index.min(),D.index.max(),D.isna().sum().to_dict())
def dev(c,Y,train=36,npost=4,trend=True):
    end=pd.Period(f"{Y}-02","M"); st=end-(train-1); post=[pd.Period(f"{Y}-{m:02d}","M") for m in range(3,3+npost)]
    y=np.log(D[c].where(D[c]>0)); tr=y.loc[st:end].dropna()
    if len(tr)<train-2 or any(p not in y.index or pd.isna(y.loc[p]) for p in post): return None
    mo=np.array([p.month for p in tr.index]); t0=np.arange(len(tr))
    X=np.column_stack([(mo==m).astype(float) for m in range(1,13)]+([t0.astype(float)] if trend else []))
    b,*_=np.linalg.lstsq(X,tr.values,rcond=None); pr=[]
    for p in post:
        k=int((p-tr.index[0]).n); pr.append(np.array([(p.month==m)*1.0 for m in range(1,13)]+([float(k)] if trend else []))@b)
    return float(np.mean(y.loc[post].values-np.array(pr)))
YEARS=[2012,2013,2014,2015,2016,2017,2018,2019,2025]; res={}
def run(c,**k):
    d26=dev(c,2026,**k)
    if d26 is None: return None
    pl={y:dev(c,y,**k) for y in YEARS}; pl={y:v for y,v in pl.items() if v is not None}; a=list(pl.values())+[d26]
    return dict(D2026=d26,exp_pct=float(np.expm1(d26)*100),placebo={y:round(v,3) for y,v in pl.items()},n=len(a),perm_p=float(np.mean([abs(v)>=abs(d26)-1e-12 for v in a])),low_p=float(np.mean([v<=d26+1e-12 for v in a])),high_p=float(np.mean([v>=d26-1e-12 for v in a])))
for c in D.columns: res["main "+c]=run(c)
for lab,k in[("train24",dict(train=24)),("train48",dict(train=48)),("notrend",dict(trend=False)),("MarMay",dict(npost=3))]: res[lab+" cigarettes"]=run("cigarettes",**k)
res["monthly cigarettes 2026"]={m:round(float(np.log(D.cigarettes[pd.Period(f'2026-{m:02d}','M')])-np.log(D.cigarettes[pd.Period(f'2025-{m:02d}','M')])),4) for m in range(1,7)}
json.dump(res,open("results_tobacco.json","w"),indent=1,default=float)
for k,v in res.items():
    if isinstance(v,dict) and "D2026" in v: print("%-26s D=%+.3f (%+.1f%%) n=%d perm p=%.2f low p=%.2f high p=%.2f | placebo %+.3f..%+.3f"%(k,v["D2026"],v["exp_pct"],v["n"],v["perm_p"],v["low_p"],v["high_p"],min(v["placebo"].values()),max(v["placebo"].values())))
    elif v is None: print(k,"NA")
    else: print(k,v)
