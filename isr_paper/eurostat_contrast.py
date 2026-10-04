"""Triple-difference style contrast: ln(image recognition use) - ln(NL generation use) by sector x country x year,
regressed on sector visual exposure x year (country-sector and country-year FE). Nets out sector-level general AI propensity."""
import json, random, numpy as np, pandas as pd
import eurostat_panel as P   # re-runs panel script once on import (also refreshes outputs)
a=P.a; ex=P.ex
w=a[a.indic_is.isin(["E_AI_TIR","E_AI_TNLG"])].pivot_table(index=["geo","nace_r2","time","zvis","zlang"],columns="indic_is",values="v").reset_index().dropna()
w=w[(w.E_AI_TIR>0)&(w.E_AI_TNLG>0)].copy(); w["y"]=np.log(w.E_AI_TIR)-np.log(w.E_AI_TNLG)
w=w[w.geo.isin(w.groupby("geo").nace_r2.nunique()[lambda s:s>=8].index)]; w["t"]=w.time.astype(int)
def est(d,vcol="zvis"):
    X=np.column_stack([((d.t==t)*d[vcol]).values for t in (2023,2024,2025)])
    FE=pd.get_dummies((d.geo+d.nace_r2).rename("sc").to_frame().join((d.geo+d.time).rename("ct")),drop_first=False).astype(float).values
    return np.linalg.lstsq(np.column_stack([X,FE]),d.y.values,rcond=None)[0][:3]
b=est(w); print("\nCONTRAST ln(TIR)-ln(TNLG) on zvis x year (base 2021): 2023/2024/2025 =",np.round(b,3),"| N =",len(w),"countries",w.geo.nunique())
sec=list(ex.nace); zv=ex.set_index("nace").zvis; rnd=random.Random(7); cnt=np.zeros(3); R=500
for _ in range(R):
    pm=sec[:]; rnd.shuffle(pm); m={s:float(zv[p]) for s,p in zip(sec,pm)}
    d=w.copy(); d["zvis"]=d.nace_r2.map(m); cnt+=np.abs(est(d))>=np.abs(b)
print("permutation p (500 draws; 11 sectors):",np.round((cnt+1)/(R+1),3))
# leave-one-sector-out stability of the 2025 coefficient
loo={s:round(float(est(w[w.nace_r2!=s])[2]),3) for s in sec}; print("leave-one-sector-out 2025 coef:",loo)
# first-differenced across countries: share of countries with positive sign of slope (country-level OLS of y_2025-y_2021 on zvis)
sl=[]
for g,d in w[w.t.isin([2021,2025])].groupby("geo"):
    p=d.pivot_table(index=["nace_r2","zvis"],columns="t",values="y").dropna().reset_index()
    if len(p)>=6 and 2021 in p.columns and 2025 in p.columns: sl.append(np.polyfit(p.zvis,p[2025]-p[2021],1)[0])
print("country-level slopes of (y2025-y2021) on zvis: n =",len(sl),"positive share =",round(float(np.mean(np.array(sl)>0)),2),"median =",round(float(np.median(sl)),3))
