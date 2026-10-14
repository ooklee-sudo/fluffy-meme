# Discretionary vs essential retail sales around the 2026 fuel shock: analysis plan (fixed before any of these series is examined)

**Status.** Written 2026-10-14. Only NAICS codes and labels of the Census workbook were listed; no value of the series below was examined. The author's hypothesis (stated in the conversation) is that the war suppresses non-essential consumption, especially after the 2026 Iran war; the hypothesis is directional and pre-specified here. Restaurants (also a discretionary item) were already analysed with this method (`ANALYSIS_PLAN_MRTS.md`: no deviation).

**Data.** Census Monthly Retail Trade, `mrtssales92-present.xlsx`, not seasonally adjusted, monthly sales in millions of dollars, through July 2026 (last months preliminary). Same method as `ANALYSIS_PLAN_MRTS.md`.

**Category assignment (fixed now).**
- Discretionary set DISC = 442 furniture and home furnishings stores; 443 electronics and appliance stores; 448 clothing and clothing accessories stores; 451 sporting goods, hobby, musical instrument and book stores; 453 miscellaneous store retailers (gifts, novelty, used merchandise).
- Essential set ESS = 4451 grocery stores; 446 health and personal care stores.
- Reported separately and not part of either set: 441 motor vehicle and parts dealers; 444 building materials and garden equipment; 4522 department stores; 4523 general merchandise incl. warehouse clubs and supercenters; 447 gasoline stations; 454 nonstore retailers (including 4541 electronic shopping); 722 food services (already analysed).
Each category's choice does not depend on its outcome; categories with data missing in any needed window are dropped and listed.

**Method.** For year Y fit on the 36 months before March of Y: ln S_t = month effects + linear trend, forecast March–July of Y, D_Y = mean(actual − forecast) in logs. Shock year Y = 2026; placebo years {2012–2019, 2025} (COVID period excluded). Permutation p = share of the ten years with |D_Y| ≥ |D_2026|; one-sided rank p for the directional hypothesis = share of the ten values (shock year included) at most D_2026 (minimum 0.10).

**Outcomes.**
- Primary: R = ln(sum of DISC sales) − ln(sum of ESS sales). Hypothesis H_D1: D_2026(R) < 0 and its one-sided rank p ≤ 0.10 (i.e., the lowest of the ten).
- Secondary: D_2026 for ln(sum DISC), ln(sum ESS), and each category separately (descriptive, with rank). H_D2: discretionary categories fall relative to forecast on average (mean of the five category D values < 0).

**Checks fixed in advance.** Training windows 24 and 48 months; no trend; Mar–Jun only.

**Interpretation rules.** H_D1 is supported only if the one-sided rank p ≤ 0.10; with ten reference years power is low and a non-significant result is not evidence of no effect. Nominal sales mix price and quantity: price inflation (including tariffs) raises nominal sales of goods, which works against detecting a fall; no deflator is used (CPI could not be retrieved earlier; retry is not planned here).

**Limitations stated in advance.** National aggregates; one post window of five months; categories only approximate "discretionary" (e.g., electronics and clothing include necessities; sporting goods respond to weather); concurrent shocks (tariffs, labour market, sentiment, Easter timing) are not separated from fuel prices; the Census numbers are subject to revision.
