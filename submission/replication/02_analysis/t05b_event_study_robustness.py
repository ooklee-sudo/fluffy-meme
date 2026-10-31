"""Table 5 robustness (not tabulated): daily returns around GML 2025 and the Jan 2026 OpenAI ads announcement;
GOOGL CARs with SPY vs. QQQ benchmarks and windows [0,0], [0,+1], [-1,+1]. Input: data/raw/prices.csv"""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"; HAND = ROOT / "data" / "hand_coded"; OUT = ROOT / "output"
DER.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
# -------------------------------------------------------------------------------------------------
import pandas as pd, numpy as np
P=pd.read_csv(RAW/"prices.csv",index_col=0,parse_dates=True); R=np.log(P).diff()*100
print(R.loc["2025-05-16":"2025-05-23",["GOOGL","META","SPY"]].round(2))
print(R.loc["2026-01-14":"2026-01-21",["GOOGL","META","SPY"]].round(2))
# robustness: QQQ benchmark, windows [0,0] and [-1,+1]
events=["2022-11-30","2025-05-07","2026-10-29","2024-05-21","2025-05-21","2026-01-16","2026-02-09","2026-07-23"]
for mk in ["SPY","QQQ"]:
  for (s,e) in [(0,0),(0,1),(-1,1)]:
    out=[]
    for d in events:
        r=R[["GOOGL",mk]].dropna(); pos=r.index.searchsorted(pd.Timestamp(d))
        est=r.iloc[pos-280:pos-30]; b,a=np.polyfit(est[mk],est["GOOGL"],1); sig=(est.GOOGL-a-b*est[mk]).std()
        w=r.iloc[pos+s:pos+e+1]; c=(w.GOOGL-a-b*w[mk]).sum(); out.append(f"{c:6.2f}({c/(sig*np.sqrt(len(w))):5.2f})")
    print(mk,(s,e)," ".join(out))
