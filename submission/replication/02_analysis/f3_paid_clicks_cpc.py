"""Figure 3: year-over-year change in paid clicks and cost-per-click, Google Search & other, 2021-2026 (10-Q).
Input: data/derived/clicks_panel.csv (t08_cpc_regressions.py). Output: output/figure3_paid_clicks_cpc.{csv,png}
(Plot re-implemented in matplotlib.)"""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"; HAND = ROOT / "data" / "hand_coded"; OUT = ROOT / "output"
DER.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
# -------------------------------------------------------------------------------------------------
import pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
d=pd.read_csv(DER/"clicks_panel.csv")
F=d[["q","clicks","cpc"]].astype({"clicks":int,"cpc":int}); F.to_csv(OUT/"figure3_paid_clicks_cpc.csv",index=False); print(F.to_string(index=False))
fig,ax=plt.subplots(figsize=(8,4.5)); x=range(len(F))
ax.plot(x,F.clicks,"o-",label="Paid clicks"); ax.plot(x,F.cpc,"o-",label="Cost-per-click"); ax.axhline(0,color="k",lw=0.5)
ax.set_xticks(list(x)); ax.set_xticklabels(F.q,rotation=60,fontsize=8); ax.set_ylabel("Year-over-year change, %"); ax.legend()
fig.tight_layout(); fig.savefig(OUT/"figure3_paid_clicks_cpc.png",dpi=200)
