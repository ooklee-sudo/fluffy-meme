"""Daily adjusted closing prices, 2021-01-04 to 2026-10-30 (Yahoo Finance chart API).
Output: data/raw/prices.csv. Used by Table 5 (event study) and the Bing event returns (Section 5.6)."""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"
RAW.mkdir(parents=True, exist_ok=True); DER.mkdir(parents=True, exist_ok=True)
UA_STRING = "ResearchBot/1.0 (contact: REPLACE_WITH_YOUR_EMAIL)"  # SEC EDGAR and Wikimedia ask for a contact address
# -------------------------------------------------------------------------------------------------
import requests, pandas as pd, time
UA={"User-Agent":"Mozilla/5.0"}
tick=["GOOGL","META","SPY","QQQ","BIDU","035420.KS","^KS11","MSFT","AMZN"]
out={}
for t in tick:
    u=f"https://query1.finance.yahoo.com/v8/finance/chart/{t}?period1=1609459200&period2=1793404800&interval=1d&events=div,splits"
    j=requests.get(u,headers=UA,timeout=30).json()["chart"]["result"][0]
    ts=pd.to_datetime(j["timestamp"],unit="s").normalize()
    adj=j["indicators"]["adjclose"][0]["adjclose"]
    out[t]=pd.Series(adj,index=ts)
    time.sleep(1)
df=pd.DataFrame(out)
df.to_csv(RAW/"prices.csv")
print(df.tail(3)); print(df.index.min(), df.index.max(), df.notna().sum().to_dict())
