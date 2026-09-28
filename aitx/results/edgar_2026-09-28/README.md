# EDGAR run, 2026-09-28

Output of `edgar-search`, `edgar-verify`, `firm-info`, and `build --source edgar` run against the live
SEC servers on 2026-09-28 (window 2023-01-01 to 2026-09-28). These are the numbers in Section 5.2 of
the manuscript ("Preliminary evidence from the EDGAR measure", Table 2a).

| File | Contents |
|---|---|
| `edgar_hits.csv` | every EDGAR full-text search hit |
| `edgar_docs_v1.csv` | rule check before the negation rule |
| `edgar_docs.csv` | rule check with the negation rule (used for the panel) |
| `firms.csv` | SIC and fiscal 2022 total assets |
| `events_edgar.csv`, `firm_month_edgar.csv` | risk set and firm-month panel (R1–R4 applied; R4 by SIC 357x, 367x, 737x) |
| `summarize.py` → `summary.json` | every number quoted in the manuscript |

No step uses hand coding: signals come from the rules in `aitx/keywords.py`, and supplier exclusion (R4)
from SIC codes (`aitx/panel.py`, `SUPPLIER_SIC`).
