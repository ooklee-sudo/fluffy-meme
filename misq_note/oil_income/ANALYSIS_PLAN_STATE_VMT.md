# Iran-war fuel shock and state restaurant employment, driving-exposure design: analysis plan (fixed before any employment value is examined)

**Status.** Written 2026-10-14, after the author supplied an event-study design memo (state panel, exposure to fuel prices through driving). The FRED state employment files were being downloaded when this was written; none of their values, and no exposure value, has been looked at. This plan modifies `ANALYSIS_PLAN.md` (which used poverty as the exposure): the primary exposure is now driving intensity (as in the memo); poverty is kept as a secondary exposure. The memo's primary outcome (state × week card spending) has no public source for 2026 (`../oi_tracker/DATA_AVAILABILITY_STATE_DESIGN.md`), so state **restaurant employment** (monthly) is the outcome; it is a labour-demand proxy, not spending.

**Shock.** War onset 28 Feb 2026; oil reacted 2 Mar 2026. The CES reference week includes the 12th of the month, so Feb 2026 is the last pre-war month (reference, k = −1) and March 2026 is the first post month (k = 0). Post = March–August 2026.

**Outcome.** ln employment in Food Services and Drinking Places (NAICS 722), not seasonally adjusted, FRED `SMU{FIPS}000007072200001`, 50 states + DC, Jan 2023–Aug 2026 (latest months preliminary). Secondary: ln total nonfarm employment `SMU{FIPS}000000000000001`.

**Exposure (pre-war, standardized across states).** E1 (primary) = 2023 vehicle-miles travelled per resident: FHWA Highway Statistics 2023 Table VM-2 (total, millions of miles) divided by 2023 state population (FRED `{ST}POP`, thousands). E2 (secondary) = state poverty rate, as in `ANALYSIS_PLAN.md` (FRED SAIPE, latest year). Commute-mode and fuel-spending shares from ACS/CEX are not used (not retrieved).

**Estimator.** ln Y_st = α_{s,m(t)} + γ_t + δ_s·t + β·(E_s × Post_t) + e_st, with state × calendar-month effects (seasonality), year-month effects (national shocks), state-specific linear trends, window Jan 2023–Aug 2026, standard errors clustered by state (51). Event study: monthly interactions E_s × 1(t = k), k = −13..+5 relative to March 2026, reference k = −1 (February 2026), same fixed effects. Randomization inference: p-value from 5,000 random permutations of the exposure across states.

**Hypotheses.**
- V1 (primary, directional): β < 0 for E1 × Post on restaurant employment (states where driving is more intensive lose more restaurant jobs after the fuel-price shock).
- V2 (specificity): the same on total nonfarm employment is smaller in magnitude than on restaurants; also the restaurant share (ln restaurants − ln nonfarm) as outcome.
- V3 (secondary): E2 (poverty) × Post < 0 for restaurant employment.

**Checks fixed in advance.** (i) Placebo shock March 2025 (Post = Mar–Aug 2025, window Jan 2022–Aug 2025) with the same specification; (ii) exclude March 2026 from Post; (iii) drop DC and the five largest states by restaurant employment; (iv) drop Alaska, Hawaii, DC (VMT/geography outliers); (v) no state trends; (vi) event-study pre-war coefficients (k = −13..−2) jointly not different from zero (Wald test).

**Interpretation rules.** V1 is supported only if β < 0 with cluster p < 0.05 **and** the permutation p < 0.10 **and** the March-2025 placebo is not significant with the same sign **and** pre-war event-study coefficients show no trend in the same direction. Otherwise "not supported". Exposure-specific effects cannot be attributed to fuel prices alone (the war also moves sentiment, tariffs, etc.), and driving exposure is also correlated with rurality, tourism, and region.

**Limitations stated in advance.** Employment responds to demand with lags and reflects labour-market conditions; 51 units; exposure is a state average (VMT includes freight and through-traffic); CES state data are revised; no state fuel price; no spending outcome.
