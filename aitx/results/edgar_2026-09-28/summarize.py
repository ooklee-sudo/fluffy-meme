"""Compute every number quoted in the manuscript insert from the pipeline outputs."""
import json
import os

import pandas as pd

D = os.path.dirname(os.path.abspath(__file__))
hits = pd.read_csv(f"{D}/edgar_hits.csv")
v1 = pd.read_csv(f"{D}/edgar_docs_v1.csv")
v2 = pd.read_csv(f"{D}/edgar_docs.csv")
ev = pd.read_csv(f"{D}/events_edgar.csv")
fm = pd.read_csv(f"{D}/firm_month_edgar.csv")
ev["exclusion"] = ev["exclusion"].fillna("")

S = {}
S["phrases_rag"] = int(hits.loc[hits.kind == "rag", "phrase"].nunique())
S["phrases_ft"] = int(hits.loc[hits.kind == "ft", "phrase"].nunique())
S["search_docs"] = len(v2)
S["search_filings"] = int(v2.adsh.nunique())
S["search_firms"] = int(v2.cik.nunique())
S["rag_docs"] = int(v2.rag.sum())
S["ft_docs"] = int(v2.ft.sum())
S["rag_firms"] = int(v2.loc[v2.rag, "cik"].nunique())
S["ft_firms"] = int(v2.loc[v2.ft, "cik"].nunique())
S["ft_docs_v1"] = int(v1.ft.sum())
S["ft_firms_v1"] = int(v1.loc[v1.ft, "cik"].nunique())

rag_firms = ev[ev.status.isin(["at_risk", "ft_first"])]
S["ft_first"] = int((ev.status == "ft_first").sum())
risk = ev[ev.status == "at_risk"]
S["risk_entered"] = len(risk)
S["risk_events_pre_excl"] = int(risk.event.sum())
for code in ("R1", "R2", "R3", "R4"):
    S[f"excl_{code}"] = int(risk.exclusion.str.startswith(code).sum())
a = risk[risk.exclusion == ""]
S["an_firms"] = len(a)
S["an_events"] = int(a.event.sum())
S["an_fm"] = len(fm)
S["cohorts"] = {str(int(k)): int(v) for k, v in a.cohort.value_counts().sort_index().items()}
S["T_median"] = round(float(a["T"].median()), 1)
S["assets_median_bn"] = round(float(a.assets_base.median() / 1e9), 2)
S["sic73"] = int((a.sic // 100 == 73).sum())
S["S_mean"] = round(float(fm.S_share.mean()), 3)
S["S_median"] = round(float(fm.S_share.median()), 3)
S["S_max"] = round(float(fm.S_share.max()), 3)
S["events"] = a[a.event == 1][["cik", "name", "entry", "ft_date", "T"]].to_dict("records")

# composition by supplier SIC (mechanical, no hand coding)
import sys  # noqa: E402
sys.path.insert(0, os.path.join(D, "..", ".."))
from aitx.panel import is_supplier_sic  # noqa: E402

firms = pd.read_csv(f"{D}/firms.csv")
for k in ("rag", "ft"):
    c = v2[v2[k]].drop_duplicates("cik")[["cik"]].merge(firms[["cik", "sic"]], on="cik", how="left")
    S[f"{k}_firms_supplier_sic"] = int(is_supplier_sic(c.sic).sum())
S["excl_R4"] = int(risk.exclusion.str.startswith("R4").sum())
S["events_removed_by_R4"] = risk[risk.exclusion.str.startswith("R4") & (risk.event == 1)]["name"].tolist()
# robustness: R4 under alternative SIC ranges (build --supplier-sic NAME)
S["sic_specs"] = {}
for spec, fname in [("none", "events_edgar_none"), ("narrow", "events_edgar_narrow"),
                    ("baseline", "events_edgar"), ("broad", "events_edgar_broad")]:
    e = pd.read_csv(f"{D}/{fname}.csv")
    e["exclusion"] = e["exclusion"].fillna("")
    r = e[(e.status == "at_risk") & (e.exclusion == "")]
    S["sic_specs"][spec] = {"firms": len(r), "events": int(r.event.sum()),
                            "event_firms": sorted(r.loc[r.event == 1, "name"].tolist())}
print(json.dumps(S, indent=1, default=str))
json.dump(S, open(os.path.join(D, "summary.json"), "w"), indent=1, default=str)
