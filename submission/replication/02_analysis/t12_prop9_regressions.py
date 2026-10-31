"""Table 12: months until full AI answers on legacy share, share squared and an in-house-model indicator,
15 legacy search engines (AI-natives excluded), HC1 standard errors; (4) Baidu coded at its July 2025 search
overhaul (month 31); (5) excluding China. The numerical example of Proposition 9 that ran in the same session
block is in 03_model/prop9_numerical_example.py. Input: data/derived/firm_panel.csv"""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"; HAND = ROOT / "data" / "hand_coded"; OUT = ROOT / "output"
DER.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
# -------------------------------------------------------------------------------------------------
import numpy as np, pandas as pd, statsmodels.formula.api as smf
# Empirical: quadratic in share, with in-house model dummy, excluding AI-natives
D=pd.read_csv(DER/"firm_panel.csv"); E=D[D.share>0].copy(); E["s"]=E.share/100
for f in ["mA ~ s","mA ~ s + I(s**2)","mA ~ s + I(s**2) + llm","mA ~ llm"]:
    m=smf.ols(f,E).fit(cov_type="HC1"); print(f,"N",int(m.nobs),"R2 %.2f"%m.rsquared,{k:(round(v,1),round(m.pvalues[k],3)) for k,v in m.params.items()})
E2=E.copy(); E2.loc[E2.firm=="Baidu","mA"]=31
m=smf.ols("mA ~ s + I(s**2) + llm",E2).fit(cov_type="HC1"); print("Baidu=Jul2025",{k:(round(v,1),round(m.pvalues[k],3)) for k,v in m.params.items()})
E3=E[E.mkt!="CN"]; m=smf.ols("mA ~ s + I(s**2) + llm",E3).fit(cov_type="HC1"); print("excl China N",int(m.nobs),{k:(round(v,1),round(m.pvalues[k],3)) for k,v in m.params.items()})
print(E.groupby("llm").mA.mean().round(1))
