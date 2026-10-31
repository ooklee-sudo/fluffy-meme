"""Table 15: trust shock (AI Overviews errors, late May 2024). Triple difference on daily log pageviews:
English minus other editions, 2024 minus the same weekdays of 2023 (2023 dates shifted +364 days), by period
relative to April 15 - May 13, 2024. 'large editions' (the 11 largest, BIG) is the specification in the paper;
'all 27 editions' is a robustness check. Newey-West (7 lags) p-values for English; randomization (placebo)
p-value = share of other editions whose placebo estimate is at least as large in absolute value.
Input: data/trust/hours.csv. Outputs: output/trust/results.csv, output/trust/gap_desktop.csv (Figure 5).
The original outputs from the session are kept in data/trust/ for comparison. Runtime ~1-3 minutes."""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"; HAND = ROOT / "data" / "hand_coded"; OUT = ROOT / "output"
DER.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
# -------------------------------------------------------------------------------------------------
TRUST=ROOT/"data"/"trust"; OUTT=OUT/"trust"; OUTT.mkdir(parents=True, exist_ok=True)
import warnings; warnings.filterwarnings("ignore")
import pandas as pd, numpy as np, statsmodels.formula.api as smf
w=pd.read_csv(TRUST/"hours.csv"); w["date"]=pd.to_datetime(w.stamp.str[:8],format="%Y%m%d")
BIG=["en","de","fr","es","ja","ru","it","pt","pl","zh","nl"]
periods=[("pre","2024-04-15","2024-05-13"),("aio","2024-05-14","2024-05-22"),("errors","2024-05-23","2024-05-31"),("june","2024-06-01","2024-06-30"),("july","2024-07-01","2024-07-31")]
def per(d):
    for n,a,b in periods:
        if pd.Timestamp(a)<=d<=pd.Timestamp(b): return n
res={}
for plat in ["desktop","mobile","all"]:
    x=w if plat=="all" else w[w.platform==plat]
    g=x.groupby(["lang","date"]).views.sum().reset_index(); g["y"]=np.log(g.views)
    a=g[g.date.dt.year==2024]; b=g[g.date.dt.year==2023].copy(); b["date"]=b.date+pd.Timedelta(days=364)
    m=a.merge(b,on=["lang","date"],suffixes=("","_ly")); m["d"]=m.y-m.y_ly; m["p"]=m.date.map(per); m=m.dropna(subset=["p"])
    for pool,lab in [(BIG,"large editions"),(list(m.lang.unique()),"all 27 editions")]:
        mm=m[m.lang.isin(pool)]
        def est(t):
            z=mm.copy(); z["T"]=(z.lang==t).astype(int)
            for n,_,_ in periods[1:]: z[f"T_{n}"]=z["T"]*(z.p==n)
            r=smf.ols("d ~ "+" + ".join(f"T_{n}" for n,_,_ in periods[1:])+" + C(lang) + C(date)",z).fit(cov_type="HAC",cov_kwds={"maxlags":7}) if t=="en" else smf.ols("d ~ "+" + ".join(f"T_{n}" for n,_,_ in periods[1:])+" + C(lang) + C(date)",z).fit()
            return r
        r=est("en"); plac=pd.DataFrame({l:{n:est(l).params[f"T_{n}"] for n,_,_ in periods[1:]} for l in pool if l!="en"}).T
        print(f"== {plat}, {lab} (N={len(pool)}, days={mm.date.nunique()})")
        for n,_,_ in periods[1:]:
            e=r.params[f"T_{n}"]; p_ri=(np.abs(plac[n])>=abs(e)).mean()
            print(f"   {n:7s} {e*100:+6.2f}%  HAC p={r.pvalues[f'T_{n}']:.3f}  randomization p={p_ri:.2f}")
            res[(plat,lab,n)]=(e,r.pvalues[f"T_{n}"],p_ri)
    if plat=="desktop":
        mb=m[m.lang.isin(BIG)]
        gap=mb.groupby("date").apply(lambda z: z[z.lang=="en"].d.mean()-z[z.lang!="en"].d.mean())
        gap.to_csv(OUTT/"gap_desktop.csv")
pd.Series({str(k):v for k,v in res.items()}).to_csv(OUTT/"results.csv")
