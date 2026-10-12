# Results of the new analyses

Panel: 19 repositories, 3432 repository-weeks, 2456 releases (1389 regular, 1067 hot-fix under the 7-day rule).

## A. Accumulated changes as the state

Discrete-time logit of a regular release on work age (merged PRs since the last regular release, through the previous week, divided by the repository's mean weekly merges) and calendar age since the last regular release, both in weeks and capped at 8, with a linear trend. Cycle-bootstrap SEs, DerSimonian-Laird pooling. A change-based state rule predicts that work age matters and calendar age does not once both are included; a Taylor cadence predicts the reverse.

| Specification | Variable | Pooled | 95% CI | tau2 |
|---|---|---|---|---|
| age only | calendar age | 0.173 | 0.079 to 0.267 | 0.020 |
| changes only | work age | 0.223 | 0.132 to 0.314 | 0.017 |
| both | work age | 0.182 | 0.029 to 0.335 | 0.040 |
| both | calendar age | 0.065 | -0.089 to 0.219 | 0.051 |

Median within-repository correlation between calendar and work age: 0.74; median coefficient of variation of weekly merges: 0.83. The higher the correlation, the less the data can separate the two rules.

- both|work: 3 repositories significantly positive, 0 significantly negative.
- both|age: 3 repositories significantly positive, 0 significantly negative.

Linear probability model with repository fixed effects, work age and calendar age entered together, wild cluster restricted bootstrap p-values (Webb weights, clusters = repositories):

- work age: 0.0290 (cluster SE 0.0133; wild bootstrap p = 0.087)
- calendar age: -0.0180 (cluster SE 0.0107; wild bootstrap p = 0.180)

Share of releases that are patch-only by the version rule alone (no 7-day window), by age of the previous release:

| Age | Share patch-only | Releases |
|---|---|---|
| 1 | 0.64 | 1646 |
| 2 | 0.60 | 328 |
| 3 | 0.54 | 160 |
| 4 | 0.57 | 94 |
| 5 | 0.40 | 47 |
| 6 | 0.56 | 48 |
| 7 | 0.48 | 31 |
| 8 | 0.40 | 78 |

## B. Upstream model launches as state shocks

- **any_rel, all events** (38 events, 323 treated and 197 control repository-event blocks; treated pre-launch weekly rate 0.42): weeks 0-4 -0.002 (SE 0.018; wild bootstrap p = 0.934), weeks 5-8 -0.011 (SE 0.024); pre-trend Wald = 6.25 on 3 df.
- **any_rel, open_weights events** (22 events, 233 treated and 173 control repository-event blocks; treated pre-launch weekly rate 0.39): weeks 0-4 0.009 (SE 0.019; wild bootstrap p = 0.626), weeks 5-8 0.004 (SE 0.025); pre-trend Wald = 7.00 on 3 df.
- **any_rel, api events** (16 events, 90 treated and 198 control repository-event blocks; treated pre-launch weekly rate 0.51): weeks 0-4 -0.027 (SE 0.030; wild bootstrap p = 0.364), weeks 5-8 -0.050 (SE 0.025); pre-trend Wald = 1.83 on 3 df.
- **any_reg, all events** (38 events, 323 treated and 197 control repository-event blocks; treated pre-launch weekly rate 0.32): weeks 0-4 -0.017 (SE 0.024; wild bootstrap p = 0.492), weeks 5-8 -0.027 (SE 0.026); pre-trend Wald = 6.31 on 3 df.
- **any_reg, open_weights events** (22 events, 233 treated and 173 control repository-event blocks; treated pre-launch weekly rate 0.30): weeks 0-4 -0.029 (SE 0.027; wild bootstrap p = 0.318), weeks 5-8 -0.021 (SE 0.034); pre-trend Wald = 5.84 on 3 df.
- **any_reg, api events** (16 events, 90 treated and 198 control repository-event blocks; treated pre-launch weekly rate 0.38): weeks 0-4 -0.021 (SE 0.032; wild bootstrap p = 0.526), weeks 5-8 -0.056 (SE 0.025); pre-trend Wald = 1.93 on 3 df.

Event-time coefficients (any release, all events; week -1 omitted):

| Week | Coef | SE |
|---|---|---|
| -4 | -0.013 | 0.048 |
| -3 | 0.021 | 0.055 |
| -2 | -0.093 | 0.051 |
| 0 | 0.057 | 0.045 |
| 1 | -0.041 | 0.063 |
| 2 | -0.046 | 0.041 |
| 3 | -0.095 | 0.037 |
| 4 | 0.009 | 0.041 |
| 5 | -0.056 | 0.053 |
| 6 | 0.022 | 0.052 |
| 7 | -0.053 | 0.044 |
| 8 | -0.043 | 0.060 |

## C. Release notes that mention the new model (exposed repositories, 8 weeks before vs after launch)

- Repository-event pairs: 334; with at least one mentioning release within 8 weeks after launch: 143 (42.8%).
- Mentioning releases before launch: 26 of 1871; after launch: 287 of 1901.
- Days from launch to first mentioning release: median 10, interquartile range 1 to 24.

Check a sample of matches by hand: keyword patterns such as 'thinking' or 'responses' can match unrelated text.
