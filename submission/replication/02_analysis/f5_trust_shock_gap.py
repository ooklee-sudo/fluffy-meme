"""Figure 5: English minus other large Wikipedia editions, desktop, 2024 vs. same weekdays of 2023 (log points x 100),
centered 7-day moving average (min 4 obs), April 15 - July 31, 2024, and period means.
Input: output/trust/gap_desktop.csv (t15_trust_shock.py); falls back to the session copy in data/trust/.
Output: output/figure5_trust_gap.{csv,png} (plot re-implemented in matplotlib)."""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"; HAND = ROOT / "data" / "hand_coded"; OUT = ROOT / "output"
DER.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
# -------------------------------------------------------------------------------------------------
import pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
src=OUT/"trust"/"gap_desktop.csv"
if not src.exists(): src=ROOT/"data"/"trust"/"gap_desktop.csv"
g=pd.read_csv(src,index_col=0).iloc[:,0]*100
g=g.rolling(7,center=True,min_periods=4).mean()
F=pd.DataFrame({"d":[k[:10] for k in g.index],"v":g.round(2).values}); F.to_csv(OUT/"figure5_trust_gap.csv",index=False)
print(g.groupby(pd.cut(pd.to_datetime(g.index),pd.to_datetime(['2024-04-14','2024-05-13','2024-05-22','2024-05-31','2024-06-30','2024-07-31']))).mean().round(2))
fig,ax=plt.subplots(figsize=(8,4.5)); ax.plot(pd.to_datetime(F.d),F.v)
for dte,lab in [("2024-05-14","AI Overviews live"),("2024-05-23","Errors go viral")]:
    ax.axvline(pd.Timestamp(dte),ls="--",color="grey",lw=0.8); ax.text(pd.Timestamp(dte),ax.get_ylim()[1]*0.95,lab,fontsize=8)
ax.set_ylabel("English minus other large editions, YoY, %"); fig.tight_layout(); fig.savefig(OUT/"figure5_trust_gap.png",dpi=200)
