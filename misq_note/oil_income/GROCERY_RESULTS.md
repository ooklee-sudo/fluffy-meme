# Grocery-store sales after the March 2026 war onset (Census MRTS; extension of the grocery control in `ANALYSIS_PLAN_MRTS.md`, exploratory; `analysis_grocery.py`, `results_grocery.json`)
Method as in the MRTS plan (rolling-origin deviation vs a 36-month month-effects + trend forecast; Post = Mar–Jul 2026; ten reference years; data through July 2026, preliminary; nominal unless stated). Census had no newer release (July 2026 is the latest).
- **Grocery stores (4451): −1.1%** (perm p = 0.5; placebo range −2.3% to +2.4%); July alone −0.9%. Food and beverage stores (445): −0.9%. Supermarkets (44511): −1.4%. None significant.
- **Deflated by CPI food at home (NSA, FRED CUUR0000SAF11; YoY +1.9% Mar to +2.9% Apr, +2.7% Jul 2026): −1.8%** (Mar–Jul; one-sided low-tail p = 0.10, the lowest of the ten years); July alone −1.7% (p = 0.3). Real grocery sales are therefore not higher than trend; they are at the low end of the range of past years, not significantly.
- Beer, wine and liquor stores (4453): **+2.7%** (Mar–Jul; two-sided perm p = 0.10, highest of ten) and +5.8% in July. Warehouse clubs and supercenters (452311): +0.7%. Nonstore retailers (454): +4.0% (p = 0.10).
- Grocery relative to restaurants (4451 vs 7225): −1.7% (p = 0.3); i.e., no shift from eating out to groceries.
- Monthly grocery deviations 2026 (Mar–Jul): −2.4%, −0.4%, −0.1%, −1.9%, −0.9%, all within the placebo-year range for each month.
**Reading.** There is no significant decline in grocery sales and no increase either: grocery sales in March–July 2026 are about 1% (nominal) to 2% (real) below the pre-war trend, within normal variation. The hypothesis that people shifted from restaurants to groceries is not visible in the national data. Offsetting movements are in alcohol stores and online/nonstore retail. SNAP participation fell ≈12% year over year over the same months (`../snap/RESULTS.md`), a possible contributor to weak grocery sales.

## Addendum: beer, wine and liquor stores (4453) (exploratory; `analysis_liquor.py`, `results_liquor.json`)
- Mar–Jul 2026: +2.7% above the pre-war trend, the highest of the ten reference years (others −1.3% to +1.9%); two-sided permutation p = 0.10, the minimum attainable with ten years, so the test cannot be more decisive. 24-month training +2.6% (p = 0.10); 48-month +2.0% (p = 0.30); Mar–Jun only +2.0% (p = 0.30); **without a trend −1.8% (p = 1.0)**.
- Monthly deviation: Mar −0.7%, Apr +2.6%, May +2.7%, Jun +3.4%, Jul +5.6%; July is above the highest July of the reference years (+3.8%), the other months are inside their ranges.
- Relative to grocery stores (4453 vs 4451): +3.9% (p = 0.10).
- Nominal sales; no alcohol price index was used.
**Reading.** Liquor-store sales are at the top of their historical range, rising month by month through July, but the evidence is fragile (depends on the trend model; ten reference years); not established as a significant increase.
