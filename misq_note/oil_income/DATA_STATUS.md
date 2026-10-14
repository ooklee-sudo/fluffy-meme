# Data access status (2026-10-14)

| Source | Result from the analysis environment |
|---|---|
| FRED `fredgraph.csv` endpoint | Worked for 6 series, then every request timed out (0 of 204 series downloaded in 25+ minutes); likely rate-limited or blocked from this IP |
| BLS public API (v1) | Daily request threshold reached |
| BLS static files (download.bls.gov) | Access Denied |
| DBnomics BLS mirror (`BLS/sm`) | Reachable, but last observation is 2024-12 (indexed 2026-01), too old for the 2026 shock |
| Census API (state poverty) | No response |

**How to continue.** (1) Retry the download later (`python fetch_fred.py DIR`; resumes, ~7 minutes if FRED responds). (2) Or download the 204 series yourself from FRED (ids in `SERIES_LIST.csv`; FRED lets you add many series to a graph and download one CSV) and put the files in one folder with the file names `<series_id>.csv` (columns `observation_date,<series_id>`); the analysis script reads that folder.
