"""Figure 4: Bing's search engine market share, StatCounter, worldwide desktop and United States (all devices),
monthly 2019-01 to 2026-09, with the Bing Chat (2023-02), AI Overviews (2024-06) and AI Mode (2025-06) dates.
Inputs: data/raw/sc_desktop.csv, data/raw/sc_us.csv. Output: output/figure4_bing_share.{csv,png} (plot re-implemented)."""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"; HAND = ROOT / "data" / "hand_coded"; OUT = ROOT / "output"
DER.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
# -------------------------------------------------------------------------------------------------
import pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
rows=[]
for f,lab,slug in [("desktop","Worldwide desktop","ww"),("us","United States, all devices","us")]:
    d=pd.read_csv(RAW/f"sc_{f}.csv")
    for _,r in d.iterrows(): rows.append(dict(m=r.Date,series=lab,slug=slug,v=round(r.bing,2)))
F=pd.DataFrame(rows); F.to_csv(OUT/"figure4_bing_share.csv",index=False); print(len(F))
fig,ax=plt.subplots(figsize=(8,4.5))
for lab,g in F.groupby("series",sort=False): ax.plot(pd.to_datetime(g.m),g.v,label=lab)
for dte,lab in [("2023-02-01","Bing Chat"),("2024-06-01","AI Overviews"),("2025-06-01","AI Mode")]:
    ax.axvline(pd.Timestamp(dte),ls="--",color="grey",lw=0.8); ax.text(pd.Timestamp(dte),ax.get_ylim()[1]*0.97,lab,fontsize=8)
ax.set_ylabel("Bing share of search referrals, %"); ax.legend(loc="upper left"); fig.tight_layout(); fig.savefig(OUT/"figure4_bing_share.png",dpi=200)
