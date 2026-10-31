"""Builds the quarterly panel used in Tables 6-8 and Figure 2:
Google Search & other revenue (from 8-K exhibits) and Meta quarterly revenue (XBRL; Q4 = annual - 9 months).
g_s, g_m = 100 x log difference over four quarters. Output: data/derived/quarterly.csv"""
# ---- package-relative paths (replace the scratch directory used in the original session) ----
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"; DER = ROOT / "data" / "derived"
RAW.mkdir(parents=True, exist_ok=True); DER.mkdir(parents=True, exist_ok=True)
UA_STRING = "ResearchBot/1.0 (contact: REPLACE_WITH_YOUR_EMAIL)"  # SEC EDGAR and Wikimedia ask for a contact address
# -------------------------------------------------------------------------------------------------
import pandas as pd, numpy as np
# Meta quarterly
d=pd.read_csv(RAW/"meta_RevenueFromContractWithCustomerExcludingAssessedTax.csv",parse_dates=["start","end"])
d=d.drop_duplicates(["start","end"])
q=d[(d.days>80)&(d.days<100)].set_index("end")["val"]
a=d[(d.days>350)&(d.days<380)].set_index("end")["val"]
for e,v in a.items():
    if e not in q.index:
        nine=d[(d.end==e-pd.offsets.QuarterEnd(1))&(d.days>260)&(d.days<285)]
        if len(nine): q.loc[e]=v-nine.val.iloc[0]
q=q.sort_index(); q.index=q.index.to_period("Q")
meta=q[~q.index.duplicated()]
# Google search
s=pd.read_csv(RAW/"search_raw.csv").dropna()
s["filed"]=pd.to_datetime(s.filed)
s["q"]=(s.filed-pd.Timedelta(days=40)).dt.to_period("Q")
cur=pd.Series(s.cur.str.replace(",","").astype(float).values,index=s.q)
prev=pd.Series(s.prev.str.replace(",","").astype(float).values,index=s.q-4)
srch=pd.concat([cur,prev]); srch=srch[~srch.index.duplicated()].sort_index()
df=pd.DataFrame({"search":srch,"meta":meta/1e6}).dropna()
df["g_s"]=np.log(df.search).diff(4)*100
df["g_m"]=np.log(df.meta).diff(4)*100
df=df.dropna(); df.to_csv(DER/"quarterly.csv"); print(df.round(1).to_string())
