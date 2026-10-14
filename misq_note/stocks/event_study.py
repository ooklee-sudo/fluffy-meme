import re,json,numpy as np,pandas as pd
def blocks(path):
    L=open(path,errors="ignore").read().splitlines(); out=[];cur=None
    for i,l in enumerate(L):
        if re.match(r"^\s*\d{8}\s*,",l):
            if cur is None: cur=[]
            cur.append(l)
        elif cur is not None and l.strip()=="" : out.append(cur);cur=None
        elif cur is not None: out.append(cur);cur=None
    if cur: out.append(cur)
    return L,out
L,B=blocks("raw/48_Industry_Portfolios_Daily.csv")
# header of the first data block = nearest preceding line with commas and names
idx=[i for i,l in enumerate(L) if re.match(r"^\s*\d{8}\s*,",l)][0]
hdr=[h.strip() for h in L[idx-1].split(",")]
rows=[[x.strip() for x in l.split(",")] for l in B[0]]
I=pd.DataFrame([r[1:] for r in rows],columns=hdr[1:len(rows[0])],index=pd.to_datetime([r[0] for r in rows],format="%Y%m%d")).astype(float).replace([-99.99,-999],np.nan)
Lf,Bf=blocks("raw/F-F_Research_Data_Factors_daily.csv")
rowsf=[[x.strip() for x in l.split(",")] for l in Bf[0]]
F=pd.DataFrame([r[1:] for r in rowsf],columns=["Mkt-RF","SMB","HML","RF"],index=pd.to_datetime([r[0] for r in rowsf],format="%Y%m%d")).astype(float)
print(I.shape,I.index.min(),I.index.max(),list(I.columns)[:6])
D=I.join(F,how="inner")
ev=D.index.get_loc(pd.Timestamp("2026-03-02")); est=D.iloc[ev-260:ev-30]; print("event day",D.index[ev].date(),"estimation",est.index[0].date(),est.index[-1].date(),len(est))
def ars(model="mkt"):
    X=est[["Mkt-RF"]] if model=="mkt" else est[["Mkt-RF","SMB","HML"]]
    out={};res={}
    A=np.column_stack([np.ones(len(est)),X.values])
    for c in I.columns:
        y=(est[c]-est["RF"]).values; ok=~np.isnan(y)
        b,*_=np.linalg.lstsq(A[ok],y[ok],rcond=None)
        full=np.column_stack([np.ones(len(D)),D[X.columns].values])
        ar=(D[c]-D["RF"]).values-full@b; out[c]=pd.Series(ar,index=D.index)
    return pd.DataFrame(out)
res={}
for model in["mkt","ff3"]:
    AR=ars(model); pre=AR.iloc[ev-260:ev-30]
    out={}
    for lab,k in[("0",0),("0-1",1),("0-4",4),("0-19",19),("0-end",len(D)-1-ev)]:
        car=AR.iloc[ev:ev+k+1].sum()
        n=k+1
        roll=pre.rolling(n).sum().dropna() if n<=len(pre) else None
        p=(roll.abs().ge(car.abs(),axis=1)).mean() if roll is not None and n<100 else pd.Series(np.nan,index=car.index)
        out[lab]=dict(car=car.round(2).to_dict(),p=p.round(3).to_dict(),sd5=(pre.rolling(5).sum().std()).round(2).to_dict())
    res[model]=out
mk=D["Mkt-RF"]; res["market"]={"CAR0":float(mk.iloc[ev]),"CAR0-4":float(mk.iloc[ev:ev+5].sum()),"CAR0-19":float(mk.iloc[ev:ev+20].sum()),"CAR0-end":float(mk.iloc[ev:].sum()),"daily_0_to_4":mk.iloc[ev:ev+5].round(2).tolist()}
json.dump(res,open("results_events.json","w"),indent=1)
m=res["mkt"]
print("market excess return day0 %.2f, 0-4 %.2f, 0-19 %.2f, 0-end %.2f"%(res["market"]["CAR0"],res["market"]["CAR0-4"],res["market"]["CAR0-19"],res["market"]["CAR0-end"]),res["market"]["daily_0_to_4"])
print("PRIMARY (market model) CAR[0,4] and empirical p:")
for c in["Oil","Trans","Meals"]: print(" ",c,m["0-4"]["car"][c],m["0-4"]["p"][c],"| ff3:",res["ff3"]["0-4"]["car"][c])
s=pd.Series(m["0-4"]["car"]).sort_values()
print("lowest 8:",s.head(8).round(1).to_dict()); print("highest 8:",s.tail(8).round(1).to_dict())
for h in["0","0-19","0-end"]:
    print(h,{c:m[h]["car"][c] for c in["Oil","Trans","Meals","Rtail","Autos","Fun","Food","Smoke","Beer","Banks","Util","Guns","Gold"] if c in m[h]["car"]})
