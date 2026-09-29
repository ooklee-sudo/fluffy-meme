# Job-posting run, 2026-09-28 to 2026-09-29

Common Crawl inventory of Greenhouse, Lever, Ashby, Workday, iCIMS, and SmartRecruiters job pages
(36 crawls, January 2023 to September 2026), matched to current S&P 1500 constituents and classified
with the RAG/FT rules in `aitx/keywords.py`. These are the numbers in Section 5.2 of the manuscript
("Preliminary evidence from the job-posting measure", Table 2a; Table 3 in the JMIS version).

| File | Contents |
|---|---|
| `universe.csv` | S&P 500/400/600 constituents with CIK (`sp1500`) |
| `ats_map.csv` | firm-to-board links from `cc-match` (full-name rule, ambiguous slugs dropped) |
| `postings.csv.gz` | every unique posting of the linked boards; `skipped = 1` rows were not fetched (non-technology title) |
| `firms.csv` | SIC and fiscal 2022 total assets |
| `events_postings*.csv`, `firm_month_postings*.csv` | risk set and firm-month panel, baseline and alternative R4 SIC ranges |
| `governance.csv` | loss-aversion and CIO-power proxies (`governance` command): impairment delay `lam`, MD&A negative-word share `lam_text` (set to missing when the MD&A has fewer than 2,000 words), CIO indicators and `theta` |
| `hypothesis_models_exploratory.json` | exploratory Cox models for H1, H2, H4 proxies (one to three covariates; 9-10 events) |
| `summarize.py` -> `summary.json` | every number quoted in the manuscript, including the Cox models and Kaplan-Meier shares (needs statsmodels) |

The full inventory (`cc_inventory.csv`, 850 MB) is not stored; rerun `cc-inventory` to rebuild it.
Posting dates come from structured data when present and otherwise from the first capture, so they are
accurate only to the interval between crawls.
