"""Public occupation-by-industry employment check (EU27 LFS, lfsa_eisn2: ISCO-08 one-digit x NACE section) and ISCO two-digit employment (lfsa_egai2d).
Log change in mean employment 2023-25 vs 2019-21. Cross-tabulation is too coarse to isolate visual-production occupations; reported as a limit of public data."""
import json, numpy as np, pandas as pd
d=json.load(open("data/eurostat/lfsa_eisn2.json")); ids=d["id"]; size=d["size"]; idx={k:d["dimension"][k]["category"]["index"] for k in ids}; inv={k:{i:c for c,i in idx[k].items()} for k in ids}
rows=[]
for pos,v in d["value"].items():
    p=int(pos); key={}
    for k,s in reversed(list(zip(ids,size))): key[k]=inv[k][p%s]; p//=s
    if key["geo"]=="EU27_2020": rows.append((key["nace_r2"],key["isco08"],int(key["time"]),v))
df=pd.DataFrame(rows,columns=["n","o","t","v"]); A=[2019,2020,2021]; B=[2023,2024,2025]
def m(n,o,ys):
    s=df[(df.n==n)&(df.o==o)&df.t.isin(ys)].v; return s.mean() if len(s)==len(ys) else np.nan
for o in ("OC2","OC3","TOTAL"):
    r=pd.Series({n:np.log(m(n,o,B)/m(n,o,A)) for n in "ABCDEFGHIJKLMNOPQRS"}).dropna()
    print(o,"median over %d sections: %.3f"%(len(r),r.median()),{n:round(float(r[n]),3) for n in ("J","M","R") if n in r.index},"ranks (J,M,R):",[int((r>r[n]).sum())+1 for n in ("J","M","R")])
w=pd.read_csv("data/eurostat/eu27_isco2_employment.csv",index_col=0)
a=w[["2019","2020","2021"]].mean(axis=1); b=w[["2023","2024","2025"]].mean(axis=1); r=np.log(b/a); r=r[[i for i in r.index if len(i)==4 and i not in ("OC00","OC01","OC02","OC03")]].dropna()
print("ISCO 2-digit: n=%d median %.3f"%(len(r),r.median()),{c:round(float(r[c]),3) for c in ("OC21","OC26","OC34")})
