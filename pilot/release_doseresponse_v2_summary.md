# Release dose-response, improved controls (30 tags)

Exposure: tag accuracy averaged over three prompt formats (F1 system-role, F2 user-message, F3 bare question). Controls: previous-window trend, year-over-year trend, tag-specific linear trend over the 104 weeks before the pre window. Seasonal adjustment with 3 prior years; clustered by tag. Coefficient = change in mean ln(1+weekly new questions) per +1 SD of tag accuracy (7 weeks after vs 7 weeks before the release week).

| Release | Access | GPT-3.5 exposure beta (t) | placebo (t) | Llama 3.1 8B exposure beta (t) | placebo (t) | mean change |
|---|---|---|---|---|---|---|
| ChatGPT 2022-11-30 | free | -0.018 (-1.04) | -0.004 (-0.11) | -0.006 (-0.50) | -0.019 (-0.62) | -0.080 |
| GPT-4 2023-03-14 | paid | -0.028 (-2.23) | -0.003 (-0.27) | -0.005 (-0.31) | -0.029 (-3.49) | -0.326 |
| Claude 2 2023-07-11 | free | -0.005 (-0.28) | -0.009 (-0.90) | +0.009 (0.80) | -0.018 (-1.45) | +0.004 |
| GPT-4 Turbo 2023-11-06 | paid | -0.021 (-0.83) | -0.013 (-1.01) | -0.014 (-0.63) | -0.005 (-0.45) | -0.058 |
| Claude 3 2024-03-04 | partial | +0.005 (0.41) | -0.017 (-1.04) | +0.017 (1.50) | +0.004 (0.26) | -0.042 |
| GPT-4o 2024-05-13 | free | -0.036 (-1.75) | -0.045 (-2.47) | -0.028 (-1.26) | -0.038 (-2.14) | -0.193 |
| Claude 3.5 Sonnet 2024-06-20 | free | +0.012 (0.79) | -0.013 (-0.74) | +0.017 (1.00) | -0.000 (-0.02) | -0.159 |
| o1-preview 2024-09-12 | paid | -0.012 (-0.70) | -0.030 (-1.90) | -0.016 (-0.80) | -0.019 (-1.21) | -0.148 |

Stacked free-minus-paid: +0.032 (t 1.29) with GPT-3.5 exposure, +0.031 (t 1.23) with Llama exposure; H2 predicted a negative sign.

Reading: only the GPT-4 window shows a clean-placebo effect with GPT-3.5 exposure (about -2.8% questions per SD of accuracy, against a -33% average drop in that window); it does not replicate with the Llama exposure. 16 release-exposure tests, so one |t| > 2 is expected by chance (about 20% chance of at least one among 8). No robust dose-response.
