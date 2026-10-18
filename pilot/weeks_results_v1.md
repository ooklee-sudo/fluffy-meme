# Weekly XML analysis (cross-fitted baseline, within-group comparisons) — run on the user's computer, 1,000 docs per week

Baseline week_210408 (2021-04-08 publication): 990 docs (US 481, non-US 509), 5-fold cross-fitted. Machine docs 4,954 (draft+expand). Vocabulary 6,000.

Calibration (true share -> alpha-hat): 0.00->0.023, 0.02->0.040, 0.05->0.063, 0.10->0.104, 0.15->0.145, 0.20->0.186, 0.30->0.264, 0.40->0.349, 0.50->0.429, 0.70->0.593, 1.00->0.847

## A. Baseline alpha-hat by applicant group
| group | docs | alpha-hat (95% CI) | 99th pct of alpha-hat in 100-doc groups |
|---|---|---|---|
| US | 481 | 0.036 (0.019–0.055) | 0.090 |
| non-US | 509 | 0.008 (0.002–0.016) | 0.030 |
| all | 990 | 0.021 (0.012–0.030) | 0.060 |

## B. Each 2026 week versus the same-group baseline
| week | group | docs | alpha-hat (95% CI) | baseline | difference (95% CI) | calibrated share |
|---|---|---|---|---|---|---|
| 260108 | all | 995 | 0.046 (0.035–0.059) | 0.021 | +0.025 (+0.009 to +0.042) | 0.029 |
| 260108 | US | 382 | 0.070 (0.048–0.100) | 0.036 | +0.033 (+0.003 to +0.064) | 0.058 |
| 260108 | non-US | 613 | 0.032 (0.020–0.048) | 0.008 | +0.024 (+0.009 to +0.041) | 0.010 |
| 260409 | all | 996 | 0.070 (0.054–0.087) | 0.021 | +0.049 (+0.030 to +0.066) | 0.058 |
| 260409 | US | 487 | 0.100 (0.075–0.127) | 0.036 | +0.064 (+0.029 to +0.095) | 0.095 |
| 260409 | non-US | 509 | 0.041 (0.024–0.058) | 0.008 | +0.034 (+0.014 to +0.054) | 0.022 |
| 261008 | all | 991 | 0.064 (0.049–0.078) | 0.021 | +0.043 (+0.025 to +0.059) | 0.051 |
| 261008 | US | 446 | 0.099 (0.072–0.126) | 0.036 | +0.063 (+0.030 to +0.094) | 0.093 |
| 261008 | non-US | 545 | 0.036 (0.023–0.053) | 0.008 | +0.029 (+0.011 to +0.046) | 0.016 |

## C. By filing quarter (mixed groups; at least 60 docs): alpha-hat ranges 0.014–0.123 with no monotone trend (2024Q3–2025Q2 filings 0.05–0.12; 2026Q1–Q2 filings 0.05–0.08).
