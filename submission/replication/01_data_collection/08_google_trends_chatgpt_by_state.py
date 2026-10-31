"""Google Trends search interest in 'ChatGPT' by U.S. state, 2023-01-01 to 2026-10-29 (treatment intensity, Test A).
Output: data/raw/chatgpt_by_state.csv"""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"
RAW.mkdir(parents=True, exist_ok=True); DER.mkdir(parents=True, exist_ok=True)
UA_STRING = "ResearchBot/1.0 (contact: REPLACE_WITH_YOUR_EMAIL)"  # SEC EDGAR and Wikimedia ask for a contact address
# -------------------------------------------------------------------------------------------------
from pytrends.request import TrendReq
import time
p=TrendReq(hl='en-US',tz=0)
for k in range(5):
  try:
    p.build_payload(['ChatGPT'],timeframe='2023-01-01 2026-10-29',geo='US')
    d=p.interest_by_region(resolution='REGION',inc_low_vol=True); d.to_csv(RAW/'chatgpt_by_state.csv'); print(d.sort_values('ChatGPT').iloc[[0,1,-2,-1]]); print(len(d)); break
  except Exception as e: print('err',e); time.sleep(40)
