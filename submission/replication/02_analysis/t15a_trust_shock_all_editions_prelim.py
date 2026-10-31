"""Table 15, preliminary version (superseded by t15_trust_shock.py): same triple difference with all 27 editions,
OLS standard errors and placebo ranks. Kept because it writes the analysis panels (panel_<platform>.csv)
and the daily English-minus-others gap for all platforms (daily_gap.csv) that are distributed in data/trust/.
Input: data/trust/hours.csv. Outputs: output/trust/panel_{desktop,mobile,all}.csv, output/trust/daily_gap.csv"""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"; HAND = ROOT / "data" / "hand_coded"; OUT = ROOT / "output"
DER.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
# -------------------------------------------------------------------------------------------------
TRUST=ROOT/"data"/"trust"; OUTT=OUT/"trust"; OUTT.mkdir(parents=True, exist_ok=True)
import pandas as pd, numpy as np, statsmodels.formula.api as smf, sys
w=pd.read_csv(TRUST/"hours.csv"); w["date"]=pd.to_datetime(w.stamp.str[:8],format="%Y%m%d")
periods=[("pre","2024-04-15","2024-05-13"),("aio","2024-05-14","2024-05-22"),("errors","2024-05-23","2024-05-31"),("june","2024-06-01","2024-06-30"),("july","2024-07-01","2024-07-31")]
def per(d):
    for n,a,b in periods:
        if pd.Timestamp(a)<=d<=pd.Timestamp(b): return n
    return None
out={}
for plat in ["desktop","mobile","all"]:
    x=w if plat=="all" else w[w.platform==plat]
    g=x.groupby(["lang","date"]).views.sum().reset_index(); g["y"]=np.log(g.views)
    a=g[g.date.dt.year==2024].copy(); b=g[g.date.dt.year==2023].copy(); b["date"]=b.date+pd.Timedelta(days=364)
    m=a.merge(b,on=["lang","date"],suffixes=("","_ly")); m["d"]=m.y-m.y_ly; m["p"]=m.date.map(per); m=m.dropna(subset=["p"])
    def est(treat):
        mm=m.copy(); mm["T"]=(mm.lang==treat).astype(int)
        for n,_,_ in periods[1:]: mm[f"T_{n}"]=mm["T"]*(mm.p==n)
        r=smf.ols("d ~ "+" + ".join(f"T_{n}" for n,_,_ in periods[1:])+" + C(lang) + C(date)",mm).fit()
        return {n:r.params[f"T_{n}"] for n,_,_ in periods[1:]}
    en=est("en"); plac=pd.DataFrame({l:est(l) for l in m.lang.unique() if l!="en"}).T
    print(f"== {plat}: N langs={m.lang.nunique()}, days={m.date.nunique()}")
    for n in en:
        p=(np.abs(plac[n])>=abs(en[n])).mean()
        print(f"  {n:7s} English effect vs pre = {en[n]*100:+6.2f}%   placebo SD {plac[n].std()*100:5.2f}   randomization p = {p:.2f}  rank {int((plac[n]<en[n]).sum())+1}/{len(plac)+1}")
    # daily series of English minus others (YoY), for plotting
    dd=m.groupby(["date"]).apply(lambda z: z[z.lang=="en"].d.mean()-z[z.lang!="en"].d.mean(),include_groups=False)
    out[plat]=dd
    m.to_csv(OUTT/f"panel_{plat}.csv",index=False)
pd.DataFrame(out).to_csv(OUTT/"daily_gap.csv")
