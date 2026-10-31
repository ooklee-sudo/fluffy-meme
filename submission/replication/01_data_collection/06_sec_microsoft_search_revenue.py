"""Microsoft 'Search and news advertising revenue excluding TAC' growth statements from Forms 10-Q/10-K
(SEC EDGAR, CIK 0000789019). Output: data/raw/msft_search_raw.csv (text snippets).
The quarterly growth rates used in 02_analysis/t09b_bing_revenue_and_events.py were read from these
snippets by hand (see data/hand_coded/msft_search_growth.csv)."""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"
RAW.mkdir(parents=True, exist_ok=True); DER.mkdir(parents=True, exist_ok=True)
UA_STRING = "ResearchBot/1.0 (contact: REPLACE_WITH_YOUR_EMAIL)"  # SEC EDGAR and Wikimedia ask for a contact address
# -------------------------------------------------------------------------------------------------
import requests, re, time, html as H, pandas as pd
UA={"User-Agent":UA_STRING}
def get(u):
    for k in range(6):
        r=requests.get(u,headers=UA,timeout=60)
        if r.status_code==200 and r.text.strip(): return r
        time.sleep(2*(k+1))
rows=[]
for url in ["https://data.sec.gov/submissions/CIK0000789019.json"]:
    j=get(url).json(); r=j["filings"]["recent"]
    for f,d,acc,doc,rp in zip(r["form"],r["filingDate"],r["accessionNumber"],r["primaryDocument"],r["reportDate"]):
        if f in ("10-Q","10-K") and rp>="2019-06-30": rows.append((rp,f,acc,doc))
out=[]
for rp,f,acc,doc in sorted(rows):
    t=get(f"https://www.sec.gov/Archives/edgar/data/789019/{acc.replace('-','')}/{doc}").text
    t=H.unescape(re.sub(r"<[^>]+>"," ",t)); t=re.sub(r"\s+"," ",t.replace("\xa0"," "))
    ms=[t[m.start()-30:m.start()+260] for m in re.finditer(r"[Ss]earch and news advertising revenue",t)]
    hit=[s for s in ms if re.search(r"(increased|decreased)\s+\$?[\d,.]+\s*(million|billion)?\s*or\s+\d+%|(increased|decreased)\s+\d+%",s)]
    out.append(dict(period=rp,form=f,snip=(hit or ms or [""])[0]))
    print(rp,f,(hit or ms or [""])[0][:260],flush=True); time.sleep(0.4)
pd.DataFrame(out).to_csv(RAW/"msft_search_raw.csv",index=False)
