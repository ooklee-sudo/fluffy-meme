"""Google Trends (pytrends), monthly interest for 'how to', 'what is', 'weather', 'near me', 'ChatGPT'
in one request per geography (United States and 51 states incl. DC), 2019-01-01 to 2026-10-29.
Output: data/raw/trends/<geo>.csv. Used by Table 4, Test A.
Google Trends is rate-limited (HTTP 429); the script retries and can be restarted (it skips finished states).
Google Trends values are re-normalized samples: re-downloading will give slightly different numbers."""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"
RAW.mkdir(parents=True, exist_ok=True); DER.mkdir(parents=True, exist_ok=True)
UA_STRING = "ResearchBot/1.0 (contact: REPLACE_WITH_YOUR_EMAIL)"  # SEC EDGAR and Wikimedia ask for a contact address
# -------------------------------------------------------------------------------------------------
import time, os, pandas as pd, random
from pytrends.request import TrendReq
KW=["how to","what is","weather","near me","ChatGPT"]
states=["US"]+["US-"+s for s in "AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY".split()]
(RAW/"trends").mkdir(exist_ok=True)
p=TrendReq(hl='en-US',tz=0)
for g in states:
    f=RAW/"trends"/f"{g}.csv"
    if os.path.exists(f): continue
    for k in range(5):
        try:
            p.build_payload(KW,timeframe='2019-01-01 2026-10-29',geo=g)
            d=p.interest_over_time(); d.to_csv(f); print(g,len(d),flush=True); break
        except Exception as e:
            print(g,"err",str(e)[:80],flush=True); time.sleep(20*(k+1))
    time.sleep(random.uniform(4,8))
