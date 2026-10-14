# Data check for the state-by-week event-study design (uploaded design memo, 2026-10-14)

| Item in the design | Status |
|---|---|
| State weekly card spending on restaurants, 2026 | **Not available as open data.** Opportunity Insights tracker ends 2024-06-16 (and has no state × industry × income cells); BEA Near Real-Time Spending (Fiserv, state × food services & drinking places, weekly) was discontinued: archive 2020-06-12 to 2024-04-30, last updated 2024-05-07. Connecticut open-data copy of the Affinity series is total spending only (dataset id not confirmed). |
| Gasoline prices | FRED GASREGW (national weekly, through 2026-10-05) and WTI DCOILWTICO (daily) accessible. EIA weekly prices by PADD page reachable (not yet downloaded); state prices: EIA publishes a few states only. |
| Consumer sentiment | FRED UMCSENT accessible (through 2026-08). |
| State restaurant employment (FRED/CES `SMU{FIPS}000007072200001`) | **Now accessible** (e.g. Texas and California through 2026-08), so the earlier `oil_income/ANALYSIS_PLAN.md` state-employment plan can be run. Employment is a proxy, not spending. |
| State restaurant sales | Texas Comptroller sales-tax receipts by industry, monthly, FY2004–FY2026 (xlsx `sales-tax-naics-historical.xlsx`): sector level only (industry names incl. retail/accommodation & food; no 722 subsector in the workbook); one state. Press releases give restaurant receipts YoY (Feb +4%, Mar +7%, Jun +4.8% 2026), which are secondary. Other states (e.g. California CDTFA) not checked. |
| Exposure variables | FHWA state vehicle-miles page reachable; ACS (commute mode) via Census API not tested (redirect); CEX/BEA state PCE not tested. |
| Census MRTS NAICS 722 (national) | Already analysed (`ANALYSIS_PLAN_MRTS.md`): no deviation. |

Bottom line: the memo's primary outcome (state × week card spending, 2026) has no public source; feasible substitutes are state restaurant employment (FRED), Texas/California sales tax, and national series already analysed.
