# 2022 gasoline-price surge and state card spending, driving-exposure design: analysis plan (fixed before any state spending value is examined)

**Status.** Written 2026-10-14. The author decided to drop the 2026 Iran-war analysis and study the 2022–23 gasoline-price surge instead. Already done and seen (national, not state): `RESULTS.md` (income-quartile gap in food-service spending vs gasoline price: null). No state × week value of any spending category, no state exposure value, and no state regression has been examined. Only column names and the dictionary definitions of categories were read.

**Shock.** Gasoline price path (FRED GASREGW): rise after Russia's invasion of Ukraine (24 Feb 2022), peak mid-June 2022, decline to the end of 2022, plateau in 2023. A continuous dose G_t = ln(national weekly regular gasoline price) is used in the primary model; no dating of the shock is needed.

**Data.** Opportunity Insights Economic Tracker, Affinity Solutions card spending by state (`Affinity - State - Daily.csv`; daily through 2022-06-05, weekly afterwards, see Amendment 1 of `ANALYSIS_PLAN.md`): spending relative to Jan 2020, seasonally adjusted. Weeks ending Sunday; sample 2021-07-11 to 2024-06-16 (same as the national plan). Categories: `spend_acf` (accommodation and food service; primary), `spend_aap` apparel, `spend_aer` arts/entertainment/recreation, `spend_sgh` sporting goods and hobby (discretionary set DISC = mean of aap, aer, sgh, acf), `spend_grf` grocery, `spend_hcs` health care (essential set ESS = mean of grf and hcs), and total `spend_all`. State-by-income-quartile totals `spend_all_q1..q4` for a secondary income test. States with fewer than 90% non-missing weeks in the sample are dropped (listed).

**Exposure (pre-war/pre-shock, standardized across states).** E1 = vehicle miles travelled per resident in 2019: FHWA Highway Statistics 2019 Table VM-2 (total, millions of miles) divided by 2019 state population (FRED `{ST}POP`, thousands). E2 = 2019 state poverty rate (FRED SAIPE). Exposure defined before the shock; no outcome data used.

**Model.** Y_st = α_s + γ_t + β·(E_s × G_t) + e_st; state fixed effects α_s, week fixed effects γ_t (absorb G_t itself and every national shock), standard errors clustered by state. β is the extra change in spending, in percentage points of the Jan-2020 baseline, for a one-SD higher exposure and a one-log-point higher gasoline price. Event study (secondary): Y_st = α_s + γ_t + Σ_k β_k (E_s × 1[t in 8-week bin k]) + e, bins relative to 2022-01-02..2022-02-27 (reference, 8 weeks), bins from 2021-07 to 2023-06.

**Hypotheses.**
- W1 (primary, directional): β < 0 for `spend_acf` with E1 (states where driving is more important cut accommodation/food-service spending more when gasoline is expensive).
- W2: the same β is negative for the discretionary composite DISC and the individual discretionary categories aap, aer, sgh.
- W3 (specificity): β on the essential composite ESS (grocery and health care) is not negative (zero or positive).
- W4 (income): β for E2 (poverty) on `spend_acf` is negative, and the effect of E1 is larger on q1 (lowest-income ZIPs) total spending than on q4: β(q1) − β(q4) < 0 (secondary).

**Checks fixed in advance.** (i) Randomization inference: p-value from 5,000 permutations of E across states; (ii) drop DC, Alaska, Hawaii; (iii) drop the five states with the largest population; (iv) sample restricted to 2021-07..2023-06; (v) replace G_t with the change in gasoline price over the previous 8 weeks; (vi) event-study pre-period coefficients (before 2022-02) jointly zero (Wald).

**Interpretation rules.** W1 is supported only if β < 0, the cluster-robust p < 0.05, the permutation p < 0.10, and the event-study pre-period shows no trend in the same direction. If W1 holds but W3 fails (grocery falls equally), the effect is general rather than discretionary. A null is not evidence of no effect (51 units; one episode).

**Limitations stated in advance.** Gasoline prices differ by state but only the national price is used (state price dynamics are mostly common and cannot be assigned reliably); VMT per capita correlates with rurality, income, and region; nominal spending; ZIP-level income is an ecological proxy; Affinity's card panel is not representative; the tracker's weekly/daily format changes in June 2022 mid-shock; accommodation is bundled with food service.
