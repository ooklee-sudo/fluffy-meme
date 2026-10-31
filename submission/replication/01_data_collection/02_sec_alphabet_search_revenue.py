"""Quarterly 'Google Search & other' revenue from every Alphabet earnings release
(Form 8-K, Item 2.02, Exhibit 99.1), SEC EDGAR, 2018-2026.
Output: data/raw/search_raw.csv (filing date, prior-year-quarter value, current-quarter value, $ millions)."""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"
RAW.mkdir(parents=True, exist_ok=True); DER.mkdir(parents=True, exist_ok=True)
UA_STRING = "ResearchBot/1.0 (contact: REPLACE_WITH_YOUR_EMAIL)"  # SEC EDGAR and Wikimedia ask for a contact address
# -------------------------------------------------------------------------------------------------
import requests, re, time, pandas as pd, html as H
def get(u,H2=None):
    for k in range(6):
        r=requests.get(u,headers={"User-Agent":UA_STRING},timeout=30)
        if r.status_code==200 and r.text.strip(): return r
        time.sleep(2*(k+1))
    raise SystemExit("fail "+u+" "+str(r.status_code))
UA={"User-Agent":UA_STRING}
rows=[]
for url in ["https://data.sec.gov/submissions/CIK0001652044.json","https://data.sec.gov/submissions/CIK0001652044-submissions-001.json"]:
    j=requests.get(url,headers=UA).json(); r=j["filings"]["recent"] if "filings" in j else j
    for f,d,acc,items in zip(r["form"],r["filingDate"],r["accessionNumber"],r["items"]):
        if f=="8-K" and "2.02" in items and d>="2018-01-01": rows.append((d,acc))
rows=sorted(set(rows)); print(len(rows))
res=[]
for d,acc in rows:
    a=acc.replace("-","")
    idx=get(f"https://www.sec.gov/Archives/edgar/data/1652044/{a}/index.json").json()
    names=[i["name"] for i in idx["directory"]["item"] if i["name"].endswith(".htm")]
    ex=[n for n in names if re.search(r"99",n)] or names
    out=None
    for n in ex:
        t=get(f"https://www.sec.gov/Archives/edgar/data/1652044/{a}/{n}").text
        t=H.unescape(re.sub(r"<[^>]+>"," ",t)); t=re.sub(r"\s+"," ",t.replace("\xa0"," "))
        m=re.search(r"Google [Ss]earch & other \$ ?([\d,]+) \$ ?([\d,]+)",t)
        if m: out=m; break
    res.append(dict(filed=d,prev=out.group(1) if out else None,cur=out.group(2) if out else None))
    time.sleep(0.6)
df=pd.DataFrame(res); print(df.to_string()); df.to_csv(RAW/"search_raw.csv",index=False)
