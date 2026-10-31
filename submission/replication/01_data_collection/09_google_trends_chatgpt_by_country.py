"""Google Trends interest in the ChatGPT *topic* (Knowledge Graph entity) by country, 2023-01-01 to 2026-10-29.
Used for the worldwide robustness sample of Test B (22 Wikipedia editions). Output: data/raw/chatgpt_topic_by_country.csv
The per-edition values actually used are hard-coded in 02_analysis/t04b2_test_b_worldwide_trends.py
(see data/hand_coded/wiki_edition_chatgpt_interest.csv); only Poland is read from this file."""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"
RAW.mkdir(parents=True, exist_ok=True); DER.mkdir(parents=True, exist_ok=True)
UA_STRING = "ResearchBot/1.0 (contact: REPLACE_WITH_YOUR_EMAIL)"  # SEC EDGAR and Wikimedia ask for a contact address
# -------------------------------------------------------------------------------------------------
from pytrends.request import TrendReq
import time, pandas as pd
p=TrendReq(hl='en-US',tz=0)
s=p.suggestions('ChatGPT'); print(s[:4])
mid=[x for x in s if 'ChatGPT' in x['title']][0]['mid']; print('mid',mid)
time.sleep(5)
p.build_payload([mid],timeframe='2023-01-01 2026-10-29',geo='')
d=p.interest_by_region(resolution='COUNTRY',inc_low_vol=True); d.columns=['chatgpt_topic']; d.to_csv(RAW/'chatgpt_topic_by_country.csv')
c=['Germany','France','Japan','South Korea','Italy','Spain','Mexico','Brazil','Poland','Netherlands','Sweden','Türkiye','Turkey','Indonesia','Vietnam','Thailand','Russia','Iran','Taiwan','Hong Kong','Ukraine','Czechia','Israel','Saudi Arabia','Egypt','United States','United Kingdom','China']
print(d.loc[[x for x in c if x in d.index]].T.to_string())
