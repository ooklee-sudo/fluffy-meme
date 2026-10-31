"""Figure 1: event study of the AI Overviews launch, August/September 2024 cohort (Callaway-Sant'Anna,
not-yet-treated controls), desktop vs. all platforms, ATT in % with 95% intervals (att +/- 1.96 se).
Inputs: output/cs_es_desktop.csv and output/cs_es_all.csv written by run_t04c.sh
(EMIN=-8 EMAX=6 ONLYG=2024-09). Output: output/figure1_aio_event_study.{csv,png}
The data-preparation step is the session's; the published chart was drawn in the document editor,
so the matplotlib rendering below is a re-implementation of the plot only."""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"; HAND = ROOT / "data" / "hand_coded"; OUT = ROOT / "output"
DER.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
# -------------------------------------------------------------------------------------------------
import pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
rows=[]
for p,lab,slug in [("desktop","Desktop","desktop"),("all","All platforms","all")]:
    d=pd.read_csv(OUT/f"cs_es_{p}.csv")
    for _,r in d.iterrows():
        rows.append(dict(e=int(r.e),series=lab,slug=slug,att=round(r.att*100,1),lo=round((r.att-1.96*r.se)*100,1),hi=round((r.att+1.96*r.se)*100,1)))
F=pd.DataFrame(rows); F.to_csv(OUT/"figure1_aio_event_study.csv",index=False); print(F.to_string(index=False))
fig,ax=plt.subplots(figsize=(8,4.5))
for (lab,g),off in zip(F.groupby("series",sort=False),[-0.12,0.12]):
    ax.errorbar(g.e+off,g.att,yerr=[g.att-g.lo,g.hi-g.att],fmt="o-",capsize=2,label=lab)
ax.axhline(0,color="grey",lw=0.8); ax.axvline(-0.5,color="grey",ls="--",lw=0.8)
ax.set_xlabel("Months relative to AI Overviews launch"); ax.set_ylabel("Effect on Wikipedia views (%)"); ax.legend()
fig.tight_layout(); fig.savefig(OUT/"figure1_aio_event_study.png",dpi=200)
