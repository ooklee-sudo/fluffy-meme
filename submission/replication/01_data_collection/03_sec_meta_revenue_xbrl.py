"""Meta Platforms revenue from SEC XBRL company-concept API (CIK 0001326801).
Output: data/raw/meta_Revenues.csv, data/raw/meta_RevenueFromContractWithCustomerExcludingAssessedTax.csv"""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"
RAW.mkdir(parents=True, exist_ok=True); DER.mkdir(parents=True, exist_ok=True)
UA_STRING = "ResearchBot/1.0 (contact: REPLACE_WITH_YOUR_EMAIL)"  # SEC EDGAR and Wikimedia ask for a contact address
# -------------------------------------------------------------------------------------------------
import requests,pandas as pd
UA={"User-Agent":UA_STRING}
for c in ["Revenues","RevenueFromContractWithCustomerExcludingAssessedTax"]:
    r=requests.get(f"https://data.sec.gov/api/xbrl/companyconcept/CIK0001326801/us-gaap/{c}.json",headers=UA)
    if r.status_code!=200: print(c,r.status_code); continue
    d=pd.DataFrame(r.json()["units"]["USD"]); d["start"]=pd.to_datetime(d["start"]); d["end"]=pd.to_datetime(d["end"])
    d["days"]=(d.end-d.start).dt.days
    print(c, d.end.min(), d.end.max(), len(d))
    d.to_csv(RAW/f"meta_{c}.csv",index=False)
