# Iran-war fuel shock and restaurant sales (limited- vs full-service): analysis plan (fixed before any restaurant series is examined)

**Status.** Written 2026-10-14 after the author pointed out that restaurant *sales* (especially fast food) are public. Only the structure of the Census workbook was inspected (sheet names, row codes, month headers); no restaurant series value was looked at. This plan supersedes the state-employment plan (`ANALYSIS_PLAN.md`), which could not be run because FRED/BLS access was blocked from the analysis environment; that plan remains valid if the data are supplied.

**Question.** Does the 2026 fuel-price shock (war onset 28 Feb 2026; effect on disposable income, especially for low-income households) change restaurant sales, and does it shift spending from sit-down to fast-food (trade-down) or reduce both?

**Data.** US Census Bureau, Monthly Retail Trade Survey, workbook `mrtssales92-present.xlsx` (downloaded 2026-10-14): monthly sales in millions of dollars, not seasonally adjusted, by kind of business: NAICS 722511 Full service restaurants; 722513/722514/722515 Limited service eating places (fast food and counter service); 7224 Drinking places; 7225 Restaurants and other eating places; 722 Food services and drinking places; control series: grocery stores (NAICS 4451). Coverage through July 2026 (the last months are preliminary and subject to revision). National only; **no income split exists in these data**. Limited-service share is used as an assumption-laden proxy for lower-income demand (lower-income households are assumed to be over-represented at fast-food outlets).

**Windows.** The COVID period (March 2020 to December 2021) is excluded. Post = March to July 2026.

**Method (rolling-origin deviation and placebo years).** For a year Y, fit on the 36 months before March of year Y (March Y−3 through February Y) the model ln S_t = a_{month(t)} + b·t + e_t (month-of-year effects and a linear trend), forecast March to July of year Y, and define D_Y as the mean of actual minus forecast log sales over those five months. Do this for Y = 2026 (the shock year) and for placebo years Y ∈ {2012, …, 2019, 2025} (windows that do not touch the COVID period). Inference is by permutation: the placebo p-value is the share of the ten years (the shock year included) whose |D_Y| is at least |D_2026|.

**Outcomes.** (a) Primary: the log ratio of limited-service to full-service sales, LSR = ln(722513-5) − ln(722511); positive D means trade-down toward limited-service, negative D means the opposite (low-income customers cut fast food more than sit-down spending falls). (b) Log sales of limited-service; (c) full-service; (d) drinking places; (e) restaurants total (7225); (f) grocery (control; a rise would be consistent with substitution from eating out to eating at home).

**Hypotheses.**
- S1 (primary, two-sided): D_2026 for LSR differs from zero by more than placebo years (permutation p < 0.10 with n = 10; the minimum attainable p is 0.10 and equals 0.10 only if 2026 is the largest of the ten).
- S2 (descriptive): signs and sizes of D_2026 for the other outcomes, reported with their placebo-year ranks.
- No directional claim is made: trade-down and fast-food cutbacks both occur in the press, and the data cannot separate them from income effects.

**Checks fixed in advance.** (i) Window length of the training period 24 and 48 months instead of 36 (for years where the COVID period is not touched). (ii) Trend-free model (month effects only). (iii) Post = March to June only. (iv) A deflated version using the CPI is **not** done (CPI could not be retrieved); all series are nominal, which mainly matters for levels and less for the LSR ratio.

**Limitations stated in advance.** National aggregates, no income split and no chain or location detail; nominal sales mix price and quantity (fuel-driven inflation and menu-price changes); preliminary and revised numbers; the number of comparable placebo years is small (ten), so the permutation test has little resolving power; other concurrent shocks (tariffs, labor costs, sentiment, weather) cannot be separated; the proxy relation between limited-service outlets and low-income customers is an assumption, not an observation.

**Not in scope here (possible extensions with other open data).** Chain-level same-store sales from SEC filings and earnings releases (e.g., fast-food chains) matched to public estimates of customers' income mix; state or county sales-tax data by NAICS (e.g., California CDTFA) which are quarterly and lagged; licensed mobility or card-spending data with neighborhood income (not available to the author).
