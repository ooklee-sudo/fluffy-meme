"""NTTO U.S.-citizen outbound travel by region around the 2026 Iran war (ANALYSIS_PLAN.md)."""
import sys,re,json,warnings,numpy as np,pandas as pd
warnings.filterwarnings("ignore")
X=pd.ExcelFile("raw/US-Outbound-to-World-Regions.xlsx"); MON=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
KEY={"europe":"Europe","caribbean":"Caribbean","asia":"Asia","south america":"SouthAm","central america":"CentralAm","oceania":"Oceania","middle east":"MiddleEast","africa":"Africa","total overseas":"Overseas","mexico (air)":"MexicoAir","canada (air)":"CanadaAir","mexico (total)":"MexicoTotal","canada (total)":"CanadaTotal"}
rows=[]
for sh in X.sheet_names:
    m=re.fullmatch(r"(\d{4})(rev)?",sh)
    if not m: continue
    y=int(m.group(1)); d=X.parse(sh,header=None)
    hdr=None
    for i in range(min(8,len(d))):
        if str(d.iloc[i,0]).strip()=="Regions": hdr=i; break
    if hdr is None: print("no header",sh); continue
    cols={j:MON.index(str(v).strip()) for j,v in enumerate(d.iloc[hdr,:].tolist()) if str(v).strip() in MON}
    seen=set()
    for i in range(hdr+1,min(hdr+25,len(d))):
        lab=re.sub(r"\s*\(.*?\)\s*",lambda mm:" ("+mm.group(0).strip(" ()")+")" if re.match(r"\s*\((Air|Total)\)",mm.group(0)) else " ",str(d.iloc[i,0])).strip().lower()
        lab=re.sub(r"\s+"," ",lab)
        lab=re.sub(r"^(mexico|canada) \((air|total)\).*",r"\1 (\2)",lab); lab=re.sub(r"^total overseas.*","total overseas",lab)
        if lab in KEY and KEY[lab] not in seen:
            seen.add(KEY[lab])
            for j,mi in cols.items():
                v=pd.to_numeric(d.iloc[i,j],errors="coerce")
                if pd.notna(v) and v>0: rows.append((KEY[lab],pd.Period(f"{y}-{mi+1:02d}","M"),float(v)))
D=pd.DataFrame(rows,columns=["s","p","v"]).drop_duplicates(["s","p"]).pivot(index="p",columns="s",values="v").sort_index()
D["OverseasExME"]=D.Overseas-D.MiddleEast
print(D.index.min(),D.index.max(),len(D)); print("last obs by series:",{c:str(D[c].dropna().index.max()) for c in D.columns})
def dev(c,Y,train=36,npost=4,trend=True,start=3):
    end=pd.Period(f"{Y}-{start-1:02d}","M") if start>1 else None
    end=pd.Period(f"{Y}-02","M") if start==3 else pd.Period(f"{Y-1}-12","M")
    st=end-(train-1); post=[pd.Period(f"{Y}-{m:02d}","M") for m in range(start,start+npost)]
    y=np.log(D[c]); tr=y.loc[st:end].dropna()
    if len(tr)<train-2 or any(p not in y.index or pd.isna(y.loc[p]) for p in post): return None
    mo=np.array([p.month for p in tr.index]); t0=np.arange(len(tr))
    Xm=np.column_stack([(mo==m).astype(float) for m in range(1,13)]+([t0.astype(float)] if trend else []))
    b,*_=np.linalg.lstsq(Xm,tr.values,rcond=None); pr=[]
    for p in post:
        k=int((p-tr.index[0]).n); pr.append(np.array([(p.month==m)*1.0 for m in range(1,13)]+([float(k)] if trend else []))@b)
    return float(np.mean(y.loc[post].values-np.array(pr)))
YEARS=[2012,2013,2014,2015,2016,2017,2018,2019,2025]; res={}
def run(c,**k):
    d=dev(c,2026,**k)
    if d is None: return None
    pl={y:dev(c,y,**k) for y in YEARS}; pl={y:v for y,v in pl.items() if v is not None}; a=list(pl.values())+[d]
    return dict(D2026=d,exp_pct=float(np.expm1(d)*100),placebo={y:round(v,3) for y,v in pl.items()},n=len(a),perm_p=float(np.mean([abs(v)>=abs(d)-1e-12 for v in a])),low_p=float(np.mean([v<=d+1e-12 for v in a])))
S=["MiddleEast","Overseas","OverseasExME","Europe","Asia","Caribbean","SouthAm","CentralAm","Oceania","Africa","MexicoAir","MexicoTotal","CanadaAir","CanadaTotal"]
for c in S: res["main "+c]=run(c)
for c in["MiddleEast","OverseasExME","Europe","Asia"]:
    res["train24 "+c]=run(c,train=24); res["train48 "+c]=run(c,train=48); res["notrend "+c]=run(c,trend=False); res["MarMay "+c]=run(c,npost=3)
for c in["MiddleEast","OverseasExME","Africa","CentralAm"]: res["JanFeb(pre) "+c]=run(c,npost=2,start=1)
json.dump(res,open("results_travel.json","w"),indent=1,default=float)
for k,v in res.items():
    if v: print("%-26s D=%+.3f (%+.1f%%) perm p=%.2f low p=%.2f n=%d | placebo %+.3f..%+.3f"%(k,v["D2026"],v["exp_pct"],v["perm_p"],v["low_p"],v["n"],min(v["placebo"].values()),max(v["placebo"].values())))
    else: print(k,"NA")
