"""Figure 2: year-over-year growth of Google Search & other revenue and Meta revenue (100 x log difference), quarterly.
Input: data/derived/quarterly.csv. Output: output/figure2_quarterly_growth.{csv,png}
(Plot re-implemented in matplotlib; the published chart was drawn in the document editor from the same series.)"""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"; HAND = ROOT / "data" / "hand_coded"; OUT = ROOT / "output"
DER.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
# -------------------------------------------------------------------------------------------------
import pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
d=pd.read_csv(DER/"quarterly.csv",index_col=0)
F=d[["g_s","g_m"]].round(1); F.to_csv(OUT/"figure2_quarterly_growth.csv"); print(F.to_string())
fig,ax=plt.subplots(figsize=(8,4.5)); x=range(len(F))
ax.axvspan(list(F.index).index("2021Q3")-0.5,list(F.index).index("2022Q4")+0.5,color="grey",alpha=0.12,label="Apple ATT hits Meta")
ax.plot(x,F.g_s,"o-",lw=2.5,label="Google Search & other"); ax.plot(x,F.g_m,"o-",color="grey",label="Meta (ad-cycle benchmark)")
ax.axvline(list(F.index).index("2023Q1")-0.5,ls="--",color="k",lw=0.8); ax.axhline(0,color="k",lw=0.5)
ax.set_xticks([i for i,q in enumerate(F.index) if q.endswith("Q1")]); ax.set_xticklabels([q[:4] for q in F.index if q.endswith("Q1")])
ax.set_ylabel("Year-over-year growth, log %"); ax.legend(); fig.tight_layout(); fig.savefig(OUT/"figure2_quarterly_growth.png",dpi=200)
