"""StatCounter Global Stats, search engine market share (monthly CSV export).
  (a) worldwide desktop, worldwide mobile, United States all devices, 2019-01 to 2026-09
      -> data/raw/sc_desktop.csv, sc_mobile.csv, sc_us.csv           (Table 9, Figure 4)
  (b) 2022 home-market shares, all devices, for KR JP CZ CN RU US FR DE and worldwide
      -> data/raw/sc22_<code>.csv                                    (2022 shares in Table 10)
(The original session used curl; this is an equivalent Python port of the same URLs.)"""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"
RAW.mkdir(parents=True, exist_ok=True); DER.mkdir(parents=True, exist_ok=True)
UA_STRING = "ResearchBot/1.0 (contact: REPLACE_WITH_YOUR_EMAIL)"  # SEC EDGAR and Wikimedia ask for a contact address
# -------------------------------------------------------------------------------------------------
import requests, time, pandas as pd
H={"User-Agent":"Mozilla/5.0"}
for dev in ["desktop","mobile"]:
    u=(f"https://gs.statcounter.com/search-engine-market-share/{dev}/worldwide/chart.php?device_hidden={dev}&statType_hidden=search_engine"
       f"&region_hidden=ww&granularity=monthly&statType=Search%20Engine&region=Worldwide&fromInt=201901&toInt=202609&fromMonthYear=2019-01&toMonthYear=2026-09&csv=1")
    open(RAW/f"sc_{dev}.csv","wb").write(requests.get(u,headers=H,timeout=60).content)
u=("https://gs.statcounter.com/search-engine-market-share/all/united-states-of-america/chart.php?device_hidden=desktop%2Bmobile%2Btablet%2Bconsole"
   "&statType_hidden=search_engine&region_hidden=US&granularity=monthly&statType=Search%20Engine&region=United%20States%20of%20America"
   "&fromInt=201901&toInt=202609&fromMonthYear=2019-01&toMonthYear=2026-09&csv=1")
open(RAW/"sc_us.csv","wb").write(requests.get(u,headers=H,timeout=60).content)
for pair in ["south-korea:KR:South%20Korea","japan:JP:Japan","czech-republic:CZ:Czech%20Republic","china:CN:China","russian-federation:RU:Russian%20Federation",
             "united-states-of-america:US:United%20States%20of%20America","france:FR:France","germany:DE:Germany","worldwide:ww:Worldwide"]:
    slug,code,name=pair.split(":")
    u=(f"https://gs.statcounter.com/search-engine-market-share/all/{slug}/chart.php?device_hidden=desktop%2Bmobile%2Btablet%2Bconsole&statType_hidden=search_engine"
       f"&region_hidden={code}&granularity=monthly&statType=Search%20Engine&region={name}&fromInt=202201&toInt=202212&fromMonthYear=2022-01&toMonthYear=2022-12&csv=1")
    open(RAW/f"sc22_{code}.csv","wb").write(requests.get(u,headers=H,timeout=60).content)
    d=pd.read_csv(RAW/f"sc22_{code}.csv"); print("==",code, d.drop(columns='Date').mean().sort_values(ascending=False).head(6).round(2).to_dict())
    time.sleep(1)
