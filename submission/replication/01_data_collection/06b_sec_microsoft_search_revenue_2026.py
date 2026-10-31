"""Prints Microsoft 'Search advertising' segment lines from 2026 Forms 10-Q/10-K (used in Section 5.6:
search advertising revenue of $3.8 billion in January-March 2026). Prints only; no output file."""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"
RAW.mkdir(parents=True, exist_ok=True); DER.mkdir(parents=True, exist_ok=True)
UA_STRING = "ResearchBot/1.0 (contact: REPLACE_WITH_YOUR_EMAIL)"  # SEC EDGAR and Wikimedia ask for a contact address
# -------------------------------------------------------------------------------------------------
import requests,re,html as H
UA={"User-Agent":UA_STRING}
j=requests.get("https://data.sec.gov/submissions/CIK0000789019.json",headers=UA).json()["filings"]["recent"]
for f,acc,doc,rp in zip(j["form"],j["accessionNumber"],j["primaryDocument"],j["reportDate"]):
    if f in("10-Q","10-K") and rp>="2026-01-01":
        t=requests.get(f"https://www.sec.gov/Archives/edgar/data/789019/{acc.replace('-','')}/{doc}",headers=UA).text
        t=H.unescape(re.sub(r"<[^>]+>"," ",t)); t=re.sub(r"\s+"," ",t.replace("\xa0"," "))
        for m in list(re.finditer(r"[Ss]earch( and news)? advertising",t))[:4]: print(rp,f,"|",t[m.start()-60:m.start()+220])
        print("---")
