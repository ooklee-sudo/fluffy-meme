"""EXPLORATORY grocery variant (see GROCERY_RESULTS.md); derived from July-only variant of the discretionary analysis (see JULY_RESULTS.md); original: Pre-registered discretionary vs essential retail analysis (ANALYSIS_PLAN_DISCRETIONARY.md). Usage: python analysis_discretionary.py mrtssales92-present.xlsx"""
import sys,re,json,warnings,numpy as np,pandas as pd
warnings.filterwarnings("ignore")
X=pd.ExcelFile(sys.argv[1]); MON={m:i+1 for i,m in enumerate(["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])}
WANT={"445":"c445","4451":"c4451","44511":"c44511","4453":"c4453","4523":"c4523","452311":"c452311","446":"c446","722":"c722","7225":"c7225","454":"c454"}
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
D["GvR"]=np.log(D.c4451)-np.log(D.c7225)
def ln(c): return D[c] if c in("GvR",) else np.log(D[c])
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
res={}
for lab,k in[("main Mar-Jul",{}),("Jul only",dict(npost=1)),("train24",dict(train=24)),("train48",dict(train=48)),("no trend",dict(trend=False)),("Mar-Jun",dict(npost=4))]:
    res[lab]=run("c4453",**k)
def devm(c,Y,m,train=36):
    end=pd.Period(f"{Y}-02","M"); st=end-(train-1); p=pd.Period(f"{Y}-{m:02d}","M"); y=np.log(D[c]); tr=y.loc[st:end]
    mo=np.array([q.month for q in tr.index]); t0=np.arange(len(tr)); Xm=np.column_stack([(mo==k).astype(float) for k in range(1,13)]+[t0.astype(float)])
    b,*_=np.linalg.lstsq(Xm,tr.values,rcond=None); k=int((p-tr.index[0]).n); return float(y.loc[p]-(np.array([(p.month==q)*1.0 for q in range(1,13)]+[float(k)])@b))
res["monthly 2026"]={m:round(devm("c4453",2026,m),4) for m in range(3,8)}
res["monthly placebo range"]={m:[round(min(devm("c4453",y,m) for y in YEARS),4),round(max(devm("c4453",y,m) for y in YEARS),4)] for m in range(3,8)}
# relative to grocery (4451) and to total food-and-beverage excluding liquor
D["LvG"]=np.log(D.c4453)-np.log(D.c4451)
def ln2(c): return D[c]
import types
res["liquor vs grocery (Mar-Jul)"]=None
y=D["LvG"]; 
def devr(Y,npost=5):
    end=pd.Period(f"{Y}-02","M"); st=end-35; post=[pd.Period(f"{Y}-{m:02d}","M") for m in range(3,3+npost)]; tr=y.loc[st:end]
    mo=np.array([q.month for q in tr.index]); t0=np.arange(len(tr)); Xm=np.column_stack([(mo==k).astype(float) for k in range(1,13)]+[t0.astype(float)])
    b,*_=np.linalg.lstsq(Xm,tr.values,rcond=None); pr=[np.array([(p.month==q)*1.0 for q in range(1,13)]+[float(int((p-tr.index[0]).n))])@b for p in post]
    return float(np.mean(y.loc[post].values-np.array(pr)))
pl={Y:devr(Y) for Y in YEARS}; d26=devr(2026)
res["liquor vs grocery (Mar-Jul)"]=dict(D2026=d26,placebo=pl,perm_p=float(np.mean([abs(v)>=abs(d26)-1e-12 for v in list(pl.values())+[d26]])))
json.dump(res,open("results_liquor.json","w"),indent=1,default=float)
for k,v in res.items():
    if isinstance(v,dict) and "D2026" in v: print("%-28s D=%+.4f (%+.1f%%) perm p=%.2f | placebo %+.3f..%+.3f"%(k,v["D2026"],100*(np.exp(v["D2026"])-1),v["perm_p"],min(v["placebo"].values()),max(v["placebo"].values())),("low p=%.2f"%v["onesided_low_p"] if "onesided_low_p" in v else ""))
    else: print(k,v)
print({Y:round(v,3) for Y,v in pl.items()})
