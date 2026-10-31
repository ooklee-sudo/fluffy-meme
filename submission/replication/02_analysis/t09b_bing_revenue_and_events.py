"""Section 5.6 (text, 'Revenue and market value'): Microsoft search advertising revenue growth (ex TAC) vs. Google
Search & other growth before/after 2023 (HAC, 2 lags), and one-day abnormal returns (market model, SPY) for GOOGL and
MSFT around the Bing Chat announcements.
The Microsoft growth rates (dict 'ms') were read by hand from the 10-Q/10-K text snippets collected by
01_data_collection/06_sec_microsoft_search_revenue.py (also in data/hand_coded/msft_search_growth.csv).
In the session this code ran in the same block as an earlier version of the Bing share model; that earlier
version is superseded by t09_bing_share.py and omitted here.
Inputs: data/derived/quarterly.csv, data/raw/prices.csv. Output: data/derived/msft_vs_google.csv"""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"; HAND = ROOT / "data" / "hand_coded"; OUT = ROOT / "output"
DER.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
# -------------------------------------------------------------------------------------------------
import pandas as pd, numpy as np, statsmodels.formula.api as smf
# MSFT vs Google growth
ms={"2021Q3":40,"2021Q4":32,"2022Q1":23,"2022Q3":16,"2022Q4":10,"2023Q1":10,"2023Q3":10,"2023Q4":8,"2024Q1":12,"2024Q3":18,"2024Q4":21,"2025Q1":21,"2025Q3":16,"2025Q4":10,"2026Q1":12}
q=pd.read_csv(DER/"quarterly.csv",index_col=0); q["gs"]=(np.exp(q.g_s/100)-1)*100
D=pd.DataFrame({"msft":pd.Series(ms)}).join(q[["gs"]]); D["gap"]=D.msft-D.gs
D["post"]=(D.index>="2023Q1").astype(int); print(D.round(1).to_string()); print(D.groupby("post")[["msft","gs","gap"]].mean().round(1))
m=smf.ols("gap ~ post",D).fit(cov_type="HAC",cov_kwds={"maxlags":2}); print("gap post",m.params.round(2).to_dict(),m.pvalues.round(3).to_dict())
D.to_csv(DER/"msft_vs_google.csv")
# event study
P=pd.read_csv(RAW/"prices.csv",index_col=0,parse_dates=True); R=np.log(P).diff()*100
for d0,lab in [("2023-02-07","Bing Chat announced"),("2023-02-08","Google Bard demo (control)"),("2023-03-29","Ads in Bing Chat announced"),("2023-05-04","Bing Chat open to all")]:
    out=[]
    for f in ["GOOGL","MSFT"]:
        r=R[[f,"SPY"]].dropna(); pos=r.index.searchsorted(pd.Timestamp(d0))
        est=r.iloc[pos-280:pos-30]; b,a=np.polyfit(est.SPY,est[f],1); sig=(est[f]-a-b*est.SPY).std()
        w=r.iloc[pos:pos+1]; c=(w[f]-a-b*w.SPY).sum(); out.append(f"{f} AR0 {c:+.2f}% (t {c/sig:+.2f})")
    print(d0,lab," | ".join(out))
