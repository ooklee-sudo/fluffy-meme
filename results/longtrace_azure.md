# Longer-trace calibration: Azure LLM Inference 2024 (code)

16,803,695 requests over 7.0 days; mean rate 27.784/s; mean service 1.94s (assumed token coefficients); offered load 53.8 servers; service cs2 = 1.65.

Hour-of-day rate / mean: peak 2.15, trough 0.24; profile (x mean): 0.78, 0.75, 0.70, 0.59, 0.48, 0.39, 0.33, 0.27, 0.24, 0.24, 0.25, 0.37, 0.67, 1.13, 1.60, 1.76, 1.68, 1.91, 2.11, 2.15, 2.04, 1.53, 1.15, 0.89

Residual IDC after removing the hour-of-day profile (Poisson / NHPP = 1): w=1s: 9.79, w=10s: 86.84, w=60s: 499.08, w=300s: 2445.18, w=900s: 7269.08, w=3600s: 28439.10

| mean rho | c | arrivals | E[wait] (s) | P(wait>tau) | P(wait>10 tau) |
|---|---|---|---|---|---|
| 0.50 | 108 | real | 2043.17 | 0.6607 | 0.6419 |
| 0.50 | 108 | Poisson | 0.00 | 0.0000 | 0.0000 |
| 0.50 | 108 | hour-of-day NHPP | 86.27 | 0.3061 | 0.2963 |
| 0.70 | 77 | real | 8727.10 | 0.7960 | 0.7872 |
| 0.70 | 77 | Poisson | 0.00 | 0.0000 | 0.0000 |
| 0.70 | 77 | hour-of-day NHPP | 3374.73 | 0.8055 | 0.8022 |
| 0.84 | 64 | real | 23424.07 | 0.8456 | 0.8443 |
| 0.84 | 64 | Poisson | 0.02 | 0.0000 | 0.0000 |
| 0.84 | 64 | hour-of-day NHPP | 7640.74 | 0.8678 | 0.8656 |

- Pricing with 24 hourly phases (c=77): hourly first-best prices range 0.00-12.29; best flat price 9.65 loses 14.7% of first-best welfare; best two-level schedule (14 off-peak hours at 2.2, 10 peak hours at 10.8) loses 4.6%; no price loses 44.1%.