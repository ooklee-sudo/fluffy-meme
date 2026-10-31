"""Table 10: AI search formats by search engine (17 engines), ordered by 2022 legacy home-market share.
Hand-coded from company announcements and trade press (sources linked in Table 10 of the paper):
share = StatCounter 2022 average home-market share, all devices (01_data_collection/12_statcounter.py);
H = first public month with an AI summary above links; A = first public month with full AI answers;
llm = in-house frontier model. Months counted from 2022-12; Daum (A not launched) coded at 46 (2026-10).
Same data: data/hand_coded/search_engines_ai_formats.csv. Output: data/derived/firm_panel.csv"""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"; HAND = ROOT / "data" / "hand_coded"; OUT = ROOT / "output"
DER.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
# -------------------------------------------------------------------------------------------------
import pandas as pd, numpy as np
from scipy import stats
D=pd.DataFrame([
 ("Google","US",87.21,"2024-05","2025-05",1,"H->A"),
 ("Baidu","CN",72.14,"2023-08","2023-08",1,"same month (China batch approval)"),
 ("Yandex","RU",49.22,"2024-02","2024-04",1,"H->A"),
 ("Naver","KR",23.98,"2025-03","2026-06",1,"H->A"),
 ("Yahoo! JAPAN","JP",15.85,"2024-10","2024-10",0,"same day"),
 ("Seznam","CZ",12.22,"2025-01","2026-05",1,"H->A"),
 ("Sogou","CN",7.58,"2026-10","2026-10",0,"same month"),
 ("Bing","US",6.91,"","2023-02",1,"A first"),
 ("360 Search","CN",3.41,"2023-09","2024-01",1,"H?->A"),
 ("Yahoo (US)","US",3.09,"","2026-01",0,"A only (beta)"),
 ("DuckDuckGo","US",2.40,"2023-03","2024-06",0,"H->A"),
 ("Daum","KR",1.55,"2026-07","",0,"H only; A not launched"),
 ("Ecosia","DE",0.95,"2025-12","2025-12",0,"same day (A beta)"),
 ("Qwant","FR",0.79,"","2026-01",0,"A; H unverified"),
 ("Brave","US",0.10,"2023-03","2024-11",0,"H->A"),
 ("Perplexity","US",0.0,"","2022-12",0,"AI-native"),
 ("You.com","US",0.0,"","2022-12",0,"AI-native"),
],columns=["firm","mkt","share","H","A","llm","note"])
start=pd.Period("2022-12","M"); end=pd.Period("2026-10","M")
mo=lambda a,default: (pd.Period(a,"M")-start).n if a else default
D["mA"]=D.A.apply(lambda a: mo(a,(end-start).n)); D["mH"]=D.H.apply(lambda a: mo(a,np.nan))
print(D[["firm","share","H","A","mH","mA","llm","note"]].to_string(index=False))
# order: did dominant firms do H strictly before A?
D["Hfirst"]=(D.mH<D.mA).astype(int); print(D.groupby(pd.cut(D.share,[-1,5,20,100]))[["Hfirst"]].agg(["mean","count"]))
D.to_csv(DER/"firm_panel.csv",index=False)
