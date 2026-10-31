"""Table 7: placebo break dates. Columns 'g_M x Post, spec. (3)' and 'AIC, spec. (3)' are printed by the loop below;
column 'Trend k, spec. (2)' is printed by the placebo loop at the end of t06_quarterly_regressions.py
(break dates 2021Q1, 2022Q1, 2023Q1, 2023Q3, 2024Q1). Also: sensitivity break without ATT/COVID controls,
and with ATT quarters dropped (text of Section 5.4). Input: data/derived/quarterly.csv"""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"; HAND = ROOT / "data" / "hand_coded"; OUT = ROOT / "output"
DER.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
# -------------------------------------------------------------------------------------------------
import pandas as pd, numpy as np, statsmodels.formula.api as smf
df=pd.read_csv(DER/"quarterly.csv",index_col=0); df.index=pd.PeriodIndex(df.index,freq="Q")
df["att"]=((df.index>=pd.Period("2021Q3"))&(df.index<=pd.Period("2022Q4"))).astype(int)
df["covid"]=((df.index>=pd.Period("2020Q2"))&(df.index<=pd.Period("2021Q2"))).astype(int)
for b in ["2021Q1","2021Q3","2022Q1","2022Q3","2023Q1","2023Q3","2024Q1","2024Q3"]:
    d=df.copy(); d["post"]=(d.index>=pd.Period(b)).astype(int)
    m=smf.ols("g_s ~ g_m + g_m:post + att + covid + post",d).fit(cov_type="HAC",cov_kwds={"maxlags":4})
    print(b,"int=%.3f p=%.3f R2=%.3f AIC=%.1f"%(m.params["g_m:post"],m.pvalues["g_m:post"],m.rsquared,m.aic))
# without att/covid controls
d=df.copy(); d["post"]=(d.index>=pd.Period("2023Q1")).astype(int)
m=smf.ols("g_s ~ g_m + g_m:post + post",d).fit(cov_type="HAC",cov_kwds={"maxlags":4}); print("no controls",m.params.round(3).to_dict(),m.pvalues.round(3).to_dict())
# drop ATT quarters entirely
m=smf.ols("g_s ~ g_m + g_m:post + covid + post",d[d.att==0]).fit(cov_type="HAC",cov_kwds={"maxlags":4}); print("drop ATT",int(m.nobs),m.params.round(3).to_dict(),m.pvalues.round(3).to_dict())
