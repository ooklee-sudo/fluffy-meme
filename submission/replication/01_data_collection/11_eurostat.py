"""Eurostat dissemination API (JSON-stat):
  isoc_ai_iaiu   - individuals who used generative AI tools in the last 3 months, % of individuals 16-74, 2025
  isoc_ci_ifp_fu - individuals using the internet daily (I_IDAY), % of individuals, 2022
Outputs: data/raw/eurostat_genai.json, data/raw/eurostat_ifu.json,
         data/raw/eurostat_genai_2025.csv, data/raw/eurostat_daily_internet_2022.csv  (Table 4, Test B)"""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"
RAW.mkdir(parents=True, exist_ok=True); DER.mkdir(parents=True, exist_ok=True)
UA_STRING = "ResearchBot/1.0 (contact: REPLACE_WITH_YOUR_EMAIL)"  # SEC EDGAR and Wikimedia ask for a contact address
# -------------------------------------------------------------------------------------------------
import json, requests, pandas as pd
def dl(url,fn):
    r=requests.get(url,timeout=60); print(r.status_code,fn); open(RAW/fn,"wb").write(r.content)
dl("https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/isoc_ai_iaiu?format=JSON&lang=EN","eurostat_genai.json")
dl("https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/isoc_ci_ifp_fu?format=JSON&lang=EN&time=2022&indic_is=I_IDAY&ind_type=IND_TOTAL&unit=PC_IND","eurostat_ifu.json")
def parse(f):
    j=json.load(open(f)); ids=j["id"]; size=j["size"]; inv=[{v:k for k,v in j["dimension"][d]["category"]["index"].items()} for d in ids]
    rows=[]
    for k,v in j["value"].items():
        k=int(k); idx=[]
        for s in reversed(size): idx.append(k%s); k//=s
        idx=list(reversed(idx)); rows.append({ids[i]:inv[i][idx[i]] for i in range(len(ids))}|{"v":v})
    return pd.DataFrame(rows)
d=parse(RAW/"eurostat_genai.json")
x=d[(d.ind_type=="IND_TOTAL")&(d.indic_is=="I_IUAI")&(d.unit=="PC_IND")][["geo","v"]].sort_values("v")
print(x.to_string(index=False)); x.to_csv(RAW/"eurostat_genai_2025.csv",index=False)
d=parse(RAW/"eurostat_ifu.json"); print(d[["geo","v"]].sort_values("v").to_string(index=False)); d[["geo","v"]].to_csv(RAW/"eurostat_daily_internet_2022.csv",index=False)
