"""Table 11: Spearman rank correlation between 2022 legacy share and months until full AI answers.
Input: data/derived/firm_panel.csv (from t10_engine_formats.py). In the session this ran in the same block as Table 10."""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"; HAND = ROOT / "data" / "hand_coded"; OUT = ROOT / "output"
DER.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)
# -------------------------------------------------------------------------------------------------
import pandas as pd, numpy as np
from scipy import stats
D=pd.read_csv(DER/"firm_panel.csv")
start=pd.Period("2022-12","M")
def sp(d,lab):
    r=stats.spearmanr(d.share,d.mA); print(f"{lab:62s} N={len(d):2d} rho={r.statistic:+.2f} p={r.pvalue:.3f}")
sp(D,"All 17")
sp(D[D.share>0],"Excl. AI-natives")
sp(D[(D.share>0)&(D.mkt!="CN")],"Excl. AI-natives and China")
sp(D[D.llm==1],"Firms with in-house frontier LLM")
sp(D[(D.llm==1)&(D.mkt!="CN")],"In-house LLM, excl. China")
d2=D.copy(); d2.loc[d2.firm=="Baidu","mA"]=(pd.Period("2025-07","M")-start).n
sp(d2[d2.llm==1],"In-house LLM, Baidu A = Jul 2025 default-search overhaul")
sp(D[D.llm==0],"Firms without in-house LLM")
