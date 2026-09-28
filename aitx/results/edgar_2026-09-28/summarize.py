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
for code in ("R1", "R2", "R3"):
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

# single-coder audit of 40 + 40 confirmed documents drawn from the first verification pass
r40 = v1[v1.rag].sample(40, random_state=7)
f40 = v1[v1.ft].sample(40, random_state=7)
FT_CODE = {  # index in f40 -> category, from reading each snippet
    **{i: "own" for i in (1, 2, 3, 8, 11, 12, 14, 16, 23, 27, 35, 38, 39)},
    **{i: "supplier" for i in (4, 6, 7, 9, 10, 15, 18, 20, 26, 29, 32, 34, 36, 37)},
    **{i: "generic" for i in (0, 5, 13, 17, 19, 21, 22, 24, 25, 30, 31)},
    **{i: "non_ai" for i in (28, 33)},
}
assert len(FT_CODE) == 40
RAG_CODE = {
    **{i: "supplier" for i in (1, 2, 5, 6, 9, 10, 11, 15, 18, 19, 21, 22, 23, 24, 25, 27, 28, 29,
                                30, 31, 32, 33, 36, 37, 38, 39)},
    **{i: "software" for i in (3, 4, 8, 12, 13, 16, 20, 26, 34)},
    **{i: "own" for i in (14, 17, 35)},
    **{i: "other" for i in (0, 7)},
}
assert len(RAG_CODE) == 40
S["audit_rag"] = pd.Series(RAG_CODE).value_counts().to_dict()
S["audit_ft"] = pd.Series(FT_CODE).value_counts().to_dict()
key = ["cik", "adsh", "filename"]
still = f40.reset_index(drop=True).merge(v2[key + ["ft"]], on=key, how="left", suffixes=("", "_v2"))
still["cat"] = still.index.map(FT_CODE)
S["audit_ft_after_negation"] = still[still.ft_v2 == True].cat.value_counts().to_dict()  # noqa: E712
print(json.dumps(S, indent=1, default=str))
json.dump(S, open(os.path.join(D, "summary.json"), "w"), indent=1, default=str)
