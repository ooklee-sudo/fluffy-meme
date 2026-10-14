import re,json,numpy as np,pandas as pd,warnings
warnings.filterwarnings("ignore")
X=pd.ExcelFile('texas_sales_tax_naics_historical.xlsx'); MON=["September","October","November","December","January","February","March","April","May","June","July","August"]
rows=[]
for sh in X.sheet_names:
    m=re.fullmatch(r"FY (\d{4})",sh)
    if not m: continue
    fy=int(m.group(1)); s=X.parse(sh,header=None)
    hdr=[str(v).strip() for v in s.iloc[1,:].tolist()]
    for i in range(2,len(s)):
        lab=str(s.iloc[i,0]).strip()
        if lab in("Eating and Drinking Places","Retail Trade"):
            for j,h in enumerate(hdr[1:13],start=1):
                mi=MON.index(h); cal=(fy-1 if mi<4 else fy); mon=[9,10,11,12,1,2,3,4,5,6,7,8][mi]
                v=pd.to_numeric(s.iloc[i,j],errors='coerce')
                if pd.notna(v): rows.append((lab,pd.Period(f"{cal}-{mon:02d}","M")-1,float(v)))   # shift to sales month
D=pd.DataFrame(rows,columns=['s','p','v']).pivot(index='p',columns='s',values='v').sort_index()
D.columns=['E','R']; D['ER']=np.log(D.E)-np.log(D.R)
print(D.index.min(),D.index.max(),len(D),D.isna().sum().to_dict())
def ln(c): return D[c] if c=='ER' else np.log(D[c])
def dev(c,Y,train=36,npost=5,trend=True):
    end=pd.Period(f"{Y}-02","M"); st=end-(train-1); post=[pd.Period(f"{Y}-{m:02d}","M") for m in range(3,3+npost)]
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
    d=dev(c,2026,**k); pl={y:dev(c,y,**k) for y in YEARS}; pl={y:v for y,v in pl.items() if v is not None}
    allv=list(pl.values())+[d]; return dict(D2026=d,placebo={y:round(v,4) for y,v in pl.items()},n=len(allv),perm_p=float(np.mean([abs(v)>=abs(d)-1e-12 for v in allv])),rank_abs=int(1+sum(abs(v)>abs(d) for v in pl.values())))
for c in['E','R','ER']: res['main '+c]=run(c)
res['train24 E']=run('E',train=24); res['train48 E']=run('E',train=48); res['notrend E']=run('E',trend=False); res['MarJun E']=run('E',npost=4)
json.dump(res,open('results_texas.json','w'),indent=1)
for k,v in res.items(): print(k,'D2026=%.4f'%v['D2026'],'perm p=%.2f'%v['perm_p'],'rank',v['rank_abs'],'of',v['n'],'| placebo range %.3f..%.3f'%(min(v['placebo'].values()),max(v['placebo'].values())))
