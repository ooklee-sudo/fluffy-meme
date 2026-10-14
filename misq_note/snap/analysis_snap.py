import pandas as pd,numpy as np,re,json
d=pd.read_excel('raw/snap-4fymonthly-9.xlsx',header=None); MN=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
rows=[]
for i in range(len(d)):
    m=re.fullmatch(r"([A-Z][a-z]{2}) (\d{4})",str(d.iloc[i,0]).strip())
    if m: rows.append((pd.Period(f"{m.group(2)}-{MN.index(m.group(1))+1:02d}","M"),*[float(d.iloc[i,j]) for j in (1,2,3,4,5)]))
S=pd.DataFrame(rows,columns=["p","persons","hh","cost","bpp","bph"]).set_index("p").sort_index()
Y=S.pct_change(12)*100; res={}
pre=Y.loc["2025-11":"2026-02"].mean(); post=Y.loc["2026-03":"2026-06"].mean()
res["pre_mean_yoy"]={c:round(float(pre[c]),2) for c in["persons","cost","bpp"]}; res["post_mean_yoy"]={c:round(float(post[c]),2) for c in["persons","cost","bpp"]}
res["monthly_yoy"]={str(k):{c:round(float(v[c]),2) for c in["persons","cost","bpp"]} for k,v in Y.loc["2025-06":].iterrows()}
for c in["persons","cost","bpp"]:
    y=Y[c].dropna(); vals={}
    for i in range(len(y)-7):
        vals[str(y.index[i+4])]=float(y.iloc[i+4:i+8].mean()-y.iloc[i:i+4].mean())
    sh=vals["2026-03"]; a=np.array(list(vals.values()))
    res["break_"+c]=dict(shock_pp=sh,n=len(vals),rank_from_most_negative=int(1+(a<sh).sum()),recent={k:round(v,2) for k,v in vals.items() if k>="2025-06"})
json.dump(res,open("results_snap.json","w"),indent=1)
for c in["persons","cost","bpp"]:
    r=res["break_"+c]; print(c,"break at 2026-03: %.2f pp; rank %d of %d (1 = most negative)"%(r["shock_pp"],r["rank_from_most_negative"],r["n"]),r["recent"])
