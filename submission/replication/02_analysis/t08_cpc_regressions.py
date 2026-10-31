"""Table 8: CPC growth regressed on paid-click growth, controlling for advertiser demand (Meta revenue growth,
converted to simple % growth). HAC standard errors, 2 lags. Columns: (1) 'cpc ~ clicks + gm_pct' 2021-2026;
(2) '+ post' 2021-2026; (3) 'cpc ~ clicks + gm_pct' 2023-2026 (printed as 'post 2023Q1+', SEs in the last block).
The 2022-06-30 10-Q could not be parsed; its values (paid clicks +12%, CPC 0%) are set by hand below.
Inputs: data/raw/clicks.csv, data/derived/quarterly.csv. Output: data/derived/clicks_panel.csv"""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"; HAND = ROOT / "data" / "hand_coded"; OUT = ROOT / "output"
DER.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
# -------------------------------------------------------------------------------------------------
import pandas as pd, numpy as np, statsmodels.formula.api as smf
c=pd.read_csv(RAW/"clicks.csv"); c.loc[c.period=="2022-06-30",["clicks","cpc"]]=[12,0]
c["q"]=pd.PeriodIndex(pd.to_datetime(c.period),freq="Q").astype(str)
q=pd.read_csv(DER/"quarterly.csv",index_col=0)
# simple % growth for meta to match reported % changes
q["gm_pct"]=(np.exp(q.g_m/100)-1)*100
d=c.merge(q[["gm_pct"]],left_on="q",right_index=True)
d["post"]=(d.q>="2023Q1").astype(int)
print(d[["q","clicks","cpc","gm_pct"]].round(1).to_string(index=False))
for f in ["cpc ~ clicks","cpc ~ clicks + gm_pct","cpc ~ clicks + gm_pct + post"]:
    m=smf.ols(f,d).fit(cov_type="HAC",cov_kwds={"maxlags":2})
    print(f,"N",int(m.nobs),"R2 %.2f"%m.rsquared); print(m.summary2().tables[1][["Coef.","Std.Err.","P>|z|"]].round(3))
print(d.groupby(d.q.str[:4])[["clicks","cpc"]].mean().round(1))
d.to_csv(DER/"clicks_panel.csv",index=False)

print("\n---- sub-samples")
d=pd.read_csv(DER/"clicks_panel.csv")
for sub,name in [(d[d.post==1],"post 2023Q1+"),(d[d.q>="2023Q3"],"2023Q3+"),(d[d.q>="2022Q1"],"2022Q1+")]:
    m=smf.ols("cpc ~ clicks + gm_pct",sub).fit(cov_type="HAC",cov_kwds={"maxlags":2})
    print(name,int(m.nobs),"R2 %.2f"%m.rsquared,m.params.round(3).to_dict(),m.pvalues.round(3).to_dict())
    m=smf.ols("cpc ~ clicks + gm_pct",sub).fit()
    print("  OLS se p",m.pvalues.round(3).to_dict())

print("\n---- column (3) with standard errors")
d=pd.read_csv(DER/"clicks_panel.csv"); m=smf.ols("cpc ~ clicks + gm_pct",d[d.post==1]).fit(cov_type="HAC",cov_kwds={"maxlags":2})
print(m.params.round(3).to_dict(), m.bse.round(3).to_dict(), round(m.rsquared,3))
