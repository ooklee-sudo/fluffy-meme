# Texas sales-tax receipts from eating and drinking places around the 2026 fuel shock: analysis plan (fixed before the series is examined)

**Status.** Written 2026-10-14. Only the workbook structure (sheet names, industry names, month headers) was inspected; no receipts value was examined. Press releases of the Texas Comptroller (restaurant receipts up 4%, 7%, 4.8% year-on-year in Feb, Mar, Jun 2026) were seen in a search result and are **not** used as data; they suggest the result may be non-negative.

**Data.** Texas Comptroller, Historical Sales Tax Revenue by Industry (`sales-tax-naics-historical.xlsx`), monthly state sales-tax receipts (dollars) by industry for fiscal years 2004–2026, through August 2026 collections. Series: "Eating and Drinking Places" (E) and "Retail Trade" (R, comparison). One state; nominal; taxpayers self-assign NAICS codes; receipts in collection month t reflect sales in month t−1, so the series is shifted back one month and indexed by sales month (sales Feb 2004–Jul 2026). Sales tax applies to restaurant meals at the state rate.

**Method.** Identical to `ANALYSIS_PLAN_MRTS.md`: rolling-origin deviation D_Y: fit ln S_t = month effects + linear trend on the 36 sales months before March of Y, forecast Mar–Jul of Y, D_Y = mean(actual − forecast); placebo years {2012–2019, 2025} (COVID period excluded); permutation p = share of the ten years with |D_Y| ≥ |D_2026|.
**Outcomes.** Primary: ln E. Secondary: ln R and ln E − ln R (restaurants relative to retail).
**Checks fixed in advance.** Training windows 24 and 48 months; no trend; Mar–Jun only.
**Hypothesis.** H_T: D_2026 for ln E is negative and large relative to placebo years (one-sided is not used; two-sided |D| rank as in the MRTS analysis, but the sign is reported).
**Limitations.** One state (energy-producing, with high driving; gasoline price changes may raise state income); nominal receipts include menu-price inflation; self-assigned NAICS; revisions; five post months; ten reference years.
