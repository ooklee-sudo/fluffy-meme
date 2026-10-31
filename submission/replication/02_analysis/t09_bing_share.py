"""Table 9: Bing's share trend (pp per month) by period; segmented trend with breaks at Bing Chat (2023-02),
AI Overviews (2024-06) and AI Mode (2025-06); Newey-West (6 lags); StatCounter 2019-01 to 2026-08 (N = 92;
September 2026 excluded as an outlier). Inputs: data/raw/sc_desktop.csv, data/raw/sc_us.csv"""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"; HAND = ROOT / "data" / "hand_coded"; OUT = ROOT / "output"
DER.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
# -------------------------------------------------------------------------------------------------
import pandas as pd, numpy as np, statsmodels.formula.api as smf
for f in ["desktop","us"]:
    d=pd.read_csv(RAW/f"sc_{f}.csv"); d=d[d.Date<"2026-09"]; d["m"]=pd.PeriodIndex(d.Date,freq="M")
    d["t"]=np.arange(len(d)); 
    for nm,st in [("post","2023-02"),("aio","2024-06"),("mode","2025-06")]:
        d[nm]=(d.m>=pd.Period(st,"M")).astype(int); d["k_"+nm]=np.where(d[nm]==1,d.t-d[d[nm]==1].t.min(),0)
    m=smf.ols("bing ~ t + post + k_post + aio + k_aio + mode + k_mode",d).fit(cov_type="HAC",cov_kwds={"maxlags":6})
    sl={"pre":m.params.t,"after Bing Chat":m.params.t+m.params.k_post,"after AIO":m.params.t+m.params.k_post+m.params.k_aio,"after AI Mode":m.params.t+m.params.k_post+m.params.k_aio+m.params.k_mode}
    print(f, "slopes pp/month:",{k:round(v,3) for k,v in sl.items()})
    print("  coefs",{k:(round(m.params[k],3),round(m.pvalues[k],3)) for k in ["t","post","k_post","aio","k_aio","mode","k_mode"]}, "N",int(m.nobs))
