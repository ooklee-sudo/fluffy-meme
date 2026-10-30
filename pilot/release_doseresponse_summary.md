# Dose-response around eight model releases (exposure = tag-level accuracy on pre-2022 questions)

Weekly new questions per tag: HF dump (weeks before 2023-01-23) + Stack Exchange API (from 2023-01-23). 50 tags, 7 weeks before vs 7 weeks after each release week, seasonally adjusted with the 3 prior years, controls: previous-window trend and year-over-year trend. Standard errors clustered by tag. Coefficient = effect on mean ln(1+n) per +1 SD of tag accuracy.

| Release | Access | GPT-3.5 exposure beta (t) | placebo beta (t) | Llama 3.1 8B exposure beta (t) | placebo beta (t) |
|---|---|---|---|---|---|
| ChatGPT 2022-11-30 | free | +0.006 (0.35) | -0.046 (-2.57) | +0.009 (0.66) | -0.023 (-0.90) |
| GPT-4 2023-03-14 | paid | -0.048 (-4.45) | -0.017 (-2.12) | -0.021 (-1.56) | -0.027 (-2.45) |
| Claude 2 2023-07-11 | free | -0.019 (-2.15) | -0.011 (-1.22) | -0.008 (-0.70) | -0.012 (-1.33) |
| GPT-4 Turbo 2023-11-06 | paid | -0.016 (-0.91) | -0.000 (-0.05) | -0.012 (-0.69) | +0.001 (0.20) |
| Claude 3 2024-03-04 | partial | +0.001 (0.07) | -0.034 (-3.40) | +0.008 (0.84) | -0.006 (-0.48) |
| GPT-4o 2024-05-13 | free | -0.026 (-2.19) | -0.037 (-2.22) | -0.014 (-1.02) | -0.026 (-2.01) |
| Claude 3.5 Sonnet 2024-06-20 | free | -0.002 (-0.11) | -0.028 (-1.62) | +0.015 (1.33) | -0.014 (-0.83) |
| o1-preview 2024-09-12 | paid | -0.028 (-1.46) | -0.051 (-4.27) | -0.035 (-2.60) | -0.023 (-1.78) |

Stacked, free minus paid (H2 predicts negative): GPT-3.5 exposure +0.018 (t 2.01); Llama exposure +0.023 (t 2.39). Wrong sign, and release timing is confounded with the 2023H1 collapse.

Caveats: placebo coefficients are often significantly negative, so tag-specific trends correlated with accuracy remain; exposure is a level, not the change in accuracy at each release; 16 tests without multiplicity correction.
