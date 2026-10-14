# Fast-food chains' US same-store sales around the 2026 fuel shock: analysis plan (fixed before any chain figure is extracted)

**Status.** Written 2026-10-14, before extracting comparable-sales figures from company filings. Earlier, unverified press-based figures for several chains were seen in search results (e.g., Burger King strong, Wendy's weak); they are not used as data and are only used afterwards as a cross-check. The author said that income splits are not important for this analysis and that a price-tier split is not needed; neither an income nor a price-tier split is used.

**Question.** Did national fast-food sales, as reported by listed chains, deviate from their recent path after the war-driven fuel-price increase (war onset 28 Feb 2026)

**Data (primary source).** US same-store (comparable) sales growth, year over year, for fiscal quarters from 2023Q1 to 2026Q2, taken from earnings press releases (SEC EDGAR 8-K, Exhibit 99.1) of 13 chains: McDonald's (US comparable sales), Wendy's (US same-restaurant sales), Restaurant Brands International (Burger King US), Yum! Brands (Taco Bell US), Domino's (US same-store sales), Wingstop (domestic same-store sales), Chipotle (comparable restaurant sales), Starbucks (US comparable store sales), Jack in the Box (Jack in the Box brand same-store sales), Papa John's (North America comparable sales), Shake Shack (same-Shack sales), CAVA (same restaurant sales), Sweetgreen (same-store sales). Where a company reports several measures, the system-wide US measure is used; if only company-operated is reported, that is used and flagged. Each figure is stored with the quoted sentence and the filing URL. Calendar alignment: fiscal quarters are mapped to the calendar quarter in which most weeks fall; Starbucks and Yum fiscal calendars are mapped explicitly in the data file.
Complementary national series: Census Monthly Retail Trade (see `ANALYSIS_PLAN_MRTS.md`), already analyzed.

**Timing.** Post = calendar 2026Q2 (April to June; fully after the war onset). 2026Q1 is a transitional quarter (the war began 28 February) and is not part of the pre-war reference. Third-quarter 2026 results are not yet published.

**Primary outcome and test.** For each chain c and quarter t, Δ_{c,t} = comps_{c,t} − comps_{c,t−1} (change in year-over-year comparable sales growth from the previous quarter), and Δ_t = the unweighted mean across chains with both quarters available. Primary statistic: Δ_2026Q2 (2026Q2 minus 2026Q1). Reference distribution: Δ_t for t = 2023Q2 to 2025Q4 (11 placebo quarters). Rank-based (permutation) p-value: the share of the 12 values (the 11 placebo quarters and the shock quarter) that are at most Δ_2026Q2 (one-sided, because the hypothesis is a deterioration; the minimum attainable p is 1/12 = 0.083).
Hypothesis H_C1 (directional): the average chain's comps growth falls from 2026Q1 to 2026Q2 by more than in placebo quarters (Δ_2026Q2 is among the lowest of the 12).

**Secondary outcomes.**
- C2 (level shift): mean comps in 2026Q2 minus the mean of the previous four quarters (2025Q1 to 2025Q4), and the same statistic for every earlier quarter with four preceding quarters available (2024Q1 to 2025Q4), with the same rank-based p-value.
- C3 (cross-chain): the cross-chain mean of Δ_{c,2026Q2} with a t statistic (n = number of chains) and the share of chains with a decrease.

**Checks fixed in advance.** (i) Excluding chains whose 2026Q2 figure is distorted by a disclosed one-off (e.g., a food-safety event, extreme weather or divestiture reported in the release). (ii) Using the two-year stacked comps (current plus year-ago growth) to net out base effects, where the year-ago figure is available. (iii) Weighted mean by 2025 system-wide US sales if available (otherwise unweighted only).

**Interpretation rules.** H_C1 is supported only if the one-sided rank p ≤ 0.10. Because the number of reference quarters is small (11), a non-significant result is not evidence of no effect.

**Limitations stated in advance.** Comparable sales mix price, quantity and mix; promotions, menu changes, calendar shifts and base effects differ by chain; the sample is 13 listed chains; no traffic (transaction) data for most chains; a single post quarter; no heterogeneity analysis by income or price tier; fuel prices cannot be separated from other concurrent shocks.
