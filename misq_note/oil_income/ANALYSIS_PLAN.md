# Iran-war fuel shock and restaurant employment by state income level: analysis plan (fixed before any estimation)

**Status.** Written 2026-10-14. The only data inspected were the existence and last observation date of the series (FRED, through 2026-08) and one example level for two states to check that series download; no regression or state comparison has been run. The earlier Airbnb study of the same shock (`../oil/`) ended as a null result; this study asks a different question with different data.

**Motivation.** Fuel price increases reduce disposable income, and low-income households spend a larger share of their budgets on fuel and food, so dining-out demand should fall more where poverty is more common (press reports and a New York Fed analysis describe larger fuel-budget burdens for low-income households; these are not verified here). Public restaurant data split by household income are not available for 2026; state-level employment in restaurants is the finest public outcome that covers the post-war months.

**Shock.** US-Israeli strikes on Iran on 28 Feb 2026; oil prices reacted on 2 Mar 2026; US regular gasoline (FRED GASREGW) rose from about 2.98 USD before the conflict to about 4.35 USD in early October 2026 (AAA/FRED; levels not used in estimation). The shock is national and common to all states; identification uses pre-determined differences between states.

**Outcome (FRED, from BLS Current Employment Statistics).** Monthly employment in Food Services and Drinking Places (NAICS 722), not seasonally adjusted, series `SMU{FIPS}000007072200001`, for the 50 states and DC, January 2023 to August 2026 (44 months). Secondary outcome: total nonfarm employment `SMU{FIPS}000000000000001` (to net out general labor-market conditions). The state CES reference period includes the 12th of the month, so March 2026 is the first post month. The latest months are preliminary and subject to revision.

**Exposure (pre-determined).** State poverty rate, all ages (FRED `PPAA{ST}{FIPS}000A156NCEN`, SAIPE, latest year available, 2024), standardized across states (mean 0, SD 1). Secondary exposure: state median household income (FRED `MEHOINUS{ST}A646N`, latest year), standardized and sign-reversed in the interpretation (lower income = more exposed).

**Hypotheses.**
- F1 (primary, directional): after the war onset, restaurant employment falls more (or rises less) in states with higher poverty rates: β < 0 for Poverty × Post.
- F2 (secondary): the same with median household income (expected β > 0).
- F3 (specificity): the Poverty × Post effect on total nonfarm employment is smaller in magnitude than on restaurant employment (i.e., the result is not a general labor-market difference between poorer states).

**Estimator.** Linear panel, outcome log employment, state × calendar-month effects (absorbing state-specific seasonality), year-month effects (absorbing national shocks, including the oil shock itself), state-specific linear trends estimated jointly (equivalent to allowing each state its own pre-period growth path), and the single interaction β·(Poverty_s × Post_t). Post = March to August 2026. Standard errors clustered by state (51 clusters); wild-cluster bootstrap p-value as a robustness check because the number of clusters is moderate. Window 2023-01 to 2026-08.
F3 uses the same specification with log total nonfarm employment, and a combined specification with the restaurant share of nonfarm employment (log restaurants minus log nonfarm) as the outcome.

**Checks fixed in advance.** (i) Placebo with a fake shock on 2025-03 (Post = 2025-03 to 2025-08; window 2022-01 to 2025-08). (ii) Excluding March 2026 from Post. (iii) Dropping DC and the five largest states by restaurant employment. (iv) Event study: monthly interactions of Poverty with month, reference February 2026. (v) Median-income exposure (F2).

**Interpretation rules.** F1 is supported only if the estimate is negative, the placebo is not distinguishable from zero, and the pre-war event-study coefficients are not trending in the same direction; otherwise it is reported as not supported. Estimates are ecological (state poverty, not individual income) and cannot attribute effects to fuel prices separately from the war's other effects.

**Limitations stated in advance.** State employment measures the supply side of restaurants (jobs), responds with lags and to labor-market conditions, and is far from the household-level income response the theory describes; 51 states give little power; poverty is correlated with region, industry mix, tourism dependence and rurality; gas-price changes differ by state but state gas prices are not available to us for all states, so exposure is not a measure of each state's gasoline price change; revisions to preliminary data; no restaurant-level or neighborhood-income data for 2026 (these require licensed mobility or card-spending data).
