"""Year-over-year change in paid clicks and cost-per-click (Google Search & other), three months ended
March/June/September, from Alphabet Forms 10-Q 2021-2026 ('Monetization Metrics'). Output: data/raw/clicks.csv
NOTE: the parser fails for the 10-Q for 2022-06-30 (table layout); the values for that quarter
(paid clicks +12%, CPC 0%) were read from the filing by hand and are set in 02_analysis/t08_cpc_regressions.py."""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"
RAW.mkdir(parents=True, exist_ok=True); DER.mkdir(parents=True, exist_ok=True)
UA_STRING = "ResearchBot/1.0 (contact: REPLACE_WITH_YOUR_EMAIL)"  # SEC EDGAR and Wikimedia ask for a contact address
# -------------------------------------------------------------------------------------------------
import requests, re, time, html as H, pandas as pd
def get(u):
    for k in range(6):
        r=requests.get(u,headers={"User-Agent":UA_STRING},timeout=60)
        if r.status_code==200 and r.text.strip(): return r
        time.sleep(2*(k+1))
rows=[]
for url in ["https://data.sec.gov/submissions/CIK0001652044.json","https://data.sec.gov/submissions/CIK0001652044-submissions-001.json"]:
    j=get(url).json(); r=j["filings"]["recent"] if "filings" in j else j
    for f,d,acc,doc,rp in zip(r["form"],r["filingDate"],r["accessionNumber"],r["primaryDocument"],r["reportDate"]):
        if f=="10-Q" and rp>="2021-01-01": rows.append((rp,acc,doc))
num=r"\(?\d+\)?\s?%?"
out=[]
for rp,acc,doc in sorted(set(rows)):
    t=get(f"https://www.sec.gov/Archives/edgar/data/1652044/{acc.replace('-','')}/{doc}").text
    t=H.unescape(re.sub(r"<[^>]+>"," ",t)); t=re.sub(r"\s+"," ",t.replace("\xa0"," "))
    m=re.search(r"Paid clicks change\s*(\(?\d+\)?)\s*%?.{0,40}?Cost-per-click change\s*(\(?\d+\)?)",t)
    seg=re.search(r"Google Search & other Paid clicks",t) is not None
    v=lambda s: -int(s.strip("()")) if s.startswith("(") else int(s)
    out.append(dict(period=rp,clicks=v(m.group(1)) if m else None,cpc=v(m.group(2)) if m else None,search_seg=seg,raw=m.group(0)[:120] if m else t[t.find("Paid clicks change")-100:t.find("Paid clicks change")+200]))
    time.sleep(0.4)
df=pd.DataFrame(out); print(df.to_string()); df.to_csv(RAW/"clicks.csv",index=False)
