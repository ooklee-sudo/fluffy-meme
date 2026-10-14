# OI tracker: gasoline prices and food-service spending by neighbourhood income, 2021-07 to 2024-06 (plan `ANALYSIS_PLAN.md` with Amendment 1)

Sample: 154 weeks; script `analysis_oi.py`; output `results_oi.json`.

**G1 (primary) not supported.** Cumulative (lags 0–3) effect of a log-point change in gasoline price on the weekly change in the food-service spending gap (q1 − q4 neighbourhood income): β = −0.029 (se 0.039, p = 0.46, n = 150). Separately: q1 −0.026 (p = 0.82), q4 +0.003 (p = 0.98); grocery gap +0.046 (p = 0.41, no specificity contrast).
**G2 (event window).** Gap fell from 0.071 to 0.052 (−0.019) between Jan–Feb 2022 and May–June 2022 (gasoline $3.38 → $4.62), but this is unremarkable among 130 same-length windows (one-sided rank p = 0.15; reference range −0.036 to +0.038).
**Checks.** Lags 0–6: −0.015 (p = 0.78); 4-week non-overlapping differences: −0.049 (p = 0.35, n = 38); excluding 2021 H2: −0.027 (p = 0.52). The descriptive levels regression on ln(gas) with trend gives −0.081 (p < 0.001) — this is the spurious-trend risk named in the plan (both series trend) and is not evidence.

**Reading.** In 2021-07 to 2024-06 national card data, the 2022 gasoline surge shows no detectable relative decline in food-service spending of low-income-ZIP neighbourhoods. Caveats from the plan: nominal spending, ZIP-level income, one episode, weak power; accommodation included; a null here does not rule out effects in 2026 or in fast food specifically. Together with the Census and chain-comps results, the evidence for a fuel-price effect on low-income restaurant spending is null in all three tests.
