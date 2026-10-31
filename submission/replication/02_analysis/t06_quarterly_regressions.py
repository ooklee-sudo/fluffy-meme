"""Table 6: Search revenue growth and the advertising cycle, 2019Q4-2026Q3 (N = 28), Newey-West (4 lags).
Column (1) level shift: 'g_s ~ g_m + att + covid + post'; (2) post-ChatGPT trend: '... + k';
(3) sensitivity break: 'g_s ~ g_m + g_m:post + att + covid + post' (printed after '---- elasticity break').
Also prints the gap regression, post-only regression, period means, and the placebo-break loop for the trend k
(the latter reported in Table 7). Input: data/derived/quarterly.csv"""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"; HAND = ROOT / "data" / "hand_coded"; OUT = ROOT / "output"
DER.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
# -------------------------------------------------------------------------------------------------
import pandas as pd, numpy as np, statsmodels.formula.api as smf
df=pd.read_csv(DER/"quarterly.csv",index_col=0); df.index=pd.PeriodIndex(df.index,freq="Q")
df["post"]=(df.index>=pd.Period("2023Q1")).astype(int)
df["att"]=((df.index>=pd.Period("2021Q3"))&(df.index<=pd.Period("2022Q4"))).astype(int)
df["covid"]=((df.index>=pd.Period("2020Q2"))&(df.index<=pd.Period("2021Q2"))).astype(int)
df["k"]=np.where(df.post==1,(df.index-pd.Period("2022Q4")).map(lambda x:x.n),0)
df["gap"]=df.g_s-df.g_m
for f in ["g_s ~ g_m + att + covid + post","g_s ~ g_m + att + covid + post + k","gap ~ att + covid + post + k"]:
    m=smf.ols(f,df).fit(cov_type="HAC",cov_kwds={"maxlags":4})
    print(f, "N=",int(m.nobs),"R2=%.2f"%m.rsquared); print(m.summary2().tables[1][["Coef.","Std.Err.","P>|z|"]].round(3))
post=df[df.post==1]
m=smf.ols("g_s ~ g_m + k",post).fit(cov_type="HAC",cov_kwds={"maxlags":4})
print("POST only", int(m.nobs), "R2=%.2f"%m.rsquared); print(m.summary2().tables[1][["Coef.","Std.Err.","P>|z|"]].round(3))
print(df[["g_s","g_m","gap"]].groupby(df.post).mean().round(2))
print(post.gap.round(1).to_string())
print("---- elasticity break")
m=smf.ols("g_s ~ g_m + g_m:post + att + covid + post",df).fit(cov_type="HAC",cov_kwds={"maxlags":4})
print(m.summary2().tables[1][["Coef.","Std.Err.","P>|z|"]].round(3))
print("---- placebo break dates for k (trend) coefficient")
for b in ["2021Q1","2022Q1","2023Q1","2023Q3","2024Q1"]:
    d=df.copy(); bp=pd.Period(b)
    d["post"]=(d.index>=bp).astype(int); d["k"]=np.where(d.post==1,(d.index-(bp-1)).map(lambda x:x.n),0)
    m=smf.ols("g_s ~ g_m + att + covid + post + k",d).fit(cov_type="HAC",cov_kwds={"maxlags":4})
    print(b, round(m.params["k"],3), round(m.pvalues["k"],3), "R2",round(m.rsquared,3))
