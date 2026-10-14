"""EXPLORATORY July-only variant of the discretionary analysis (see JULY_RESULTS.md); original: Pre-registered discretionary vs essential retail analysis (ANALYSIS_PLAN_DISCRETIONARY.md). Usage: python analysis_discretionary.py mrtssales92-present.xlsx"""
import sys,re,json,warnings,numpy as np,pandas as pd
warnings.filterwarnings("ignore")
X=pd.ExcelFile(sys.argv[1]); MON={m:i+1 for i,m in enumerate(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])}
WANT={"442":"c442","443":"c443","448":"c448","451":"c451","453":"c453","4451":"c4451","446":"c446","441":"c441","444":"c444","4522":"c4522","4523":"c4523","447":"c447","454":"c454","722":"c722","7225":"c7225","722513, 722514, 722515":"cLim"}
rows=[]
for sh in X.sheet_names:
    if not re.fullmatch(r"\d{4}",sh): continue
    s=X.parse(sh,header=None); hdr=None
    for i in range(min(12,len(s))):
        vals=[str(v) for v in s.iloc[i,:].tolist()]
        if sum(bool(re.match(r"[A-Z][a-z]{2}\.? \d{4}",v)) for v in vals)>=2: hdr=i; break
    if hdr is None: continue
    cols={}
    for j,v in enumerate(s.iloc[hdr,:].tolist()):
        m=re.match(r"([A-Z][a-z]{2})\.? (\d{4})",str(v))
        if m and m.group(1) in MON: cols[j]=pd.Period(f"{m.group(2)}-{MON[m.group(1)]:02d}","M")
    seen=set()
    for i in range(hdr+1,len(s)):
        lab=str(s.iloc[i,1]).upper()
        if "ADJUSTED" in lab and "NOT" not in lab: break
        code=str(s.iloc[i,0]).strip()
        if code in WANT and code not in seen:
            seen.add(code)
            for j,per in cols.items():
                v=pd.to_numeric(s.iloc[i,j],errors="coerce")
                if pd.notna(v): rows.append((WANT[code],per,float(v)))
D=pd.DataFrame(rows,columns=["s","p","v"]).drop_duplicates(["s","p"]).pivot(index="p",columns="s",values="v").sort_index()
print("months",len(D),D.index.min(),D.index.max()); print("missing:",D.isna().sum()[D.isna().sum()>0].to_dict())
DISC=["c442","c443","c448","c451","c453"]; ESS=["c4451","c446"]
D["DISC"]=D[DISC].sum(axis=1,min_count=len(DISC)); D["ESS"]=D[ESS].sum(axis=1,min_count=len(ESS)); D["R"]=np.log(D.DISC)-np.log(D.ESS); D["cFull"]=D.c7225-D.cLim; D["LSR"]=np.log(D.cLim)-np.log(D.cFull)
def ln(c): return D[c] if c in("R","LSR") else np.log(D[c])
def dev(c,Y,train=36,npost=5,trend=True):
    end=pd.Period(f"{Y}-02","M"); st=end-(train-1); post=[pd.Period(f"{Y}-07","M")] if npost==1 else [pd.Period(f"{Y}-{m:02d}","M") for m in range(3,3+npost)]
    y=ln(c); tr=y.loc[st:end].dropna()
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
    pl={y:dev(c,y,**k) for y in YEARS}; pl={y:v for y,v in pl.items() if v is not None}; allv=list(pl.values())+[d]
    return dict(D2026=d,placebo={y:round(v,4) for y,v in pl.items()},n=len(allv),perm_p=float(np.mean([abs(v)>=abs(d)-1e-12 for v in allv])),onesided_low_p=float(np.mean([v<=d+1e-12 for v in allv])))
K=dict(npost=1)
for c in["R","DISC","ESS"]+DISC+ESS+["c441","c444","c4522","c4523","c447","c454","c722","c7225","cLim","cFull","LSR"]: res["July "+c]=run(c,**K)
res["July R no trend"]=run("R",npost=1,trend=False); res["July R train24"]=run("R",npost=1,train=24)
json.dump(res,open("results_july.json","w"),indent=1,default=float)
for k,v in res.items():
    if v: print("%-18s D2026=%+.4f perm p=%.2f low-tail p=%.2f n=%d | placebo %+.3f..%+.3f"%(k,v["D2026"],v["perm_p"],v["onesided_low_p"],v["n"],min(v["placebo"].values()),max(v["placebo"].values())))
