# Longer-trace calibration: BurstGPT v2.0 file 1

1,429,737 requests over 61.0 days; mean rate 0.271/s; mean service 4.00s (assumed token coefficients); offered load 1.1 servers; service cs2 = 4.14.

Hour-of-day rate / mean: peak 1.84, trough 0.16; profile (x mean): 0.96, 0.91, 0.59, 0.53, 0.38, 0.35, 0.20, 0.16, 0.18, 0.43, 0.90, 1.32, 1.79, 1.54, 1.84, 1.43, 1.51, 1.39, 1.21, 1.61, 1.39, 1.20, 1.16, 1.05

Residual IDC after removing the hour-of-day profile (Poisson / NHPP = 1): w=1s: 3.76, w=10s: 24.00, w=60s: 133.69, w=300s: 619.48, w=900s: 1673.65, w=3600s: 5059.62

| mean rho | c | arrivals | E[wait] (s) | P(wait>tau) | P(wait>10 tau) |
|---|---|---|---|---|---|
| 0.36 | 3 | real | 31408.47 | 0.5602 | 0.5264 |
| 0.36 | 3 | Poisson | 0.46 | 0.0355 | 0.0001 |
| 0.36 | 3 | hour-of-day NHPP | 1.52 | 0.1046 | 0.0022 |
| 0.54 | 2 | real | 93380.96 | 0.7370 | 0.6928 |
| 0.54 | 2 | Poisson | 4.00 | 0.2260 | 0.0156 |
| 0.54 | 2 | hour-of-day NHPP | 24.96 | 0.4691 | 0.1892 |
| 0.54 | 2 | real | 93380.96 | 0.7370 | 0.6928 |
| 0.54 | 2 | Poisson | 4.00 | 0.2254 | 0.0159 |
| 0.54 | 2 | hour-of-day NHPP | 26.87 | 0.4693 | 0.1888 |

- Pricing with 24 hourly phases (c=2): hourly first-best prices range 0.09-10.84; best flat price 8.35 loses 4.9% of first-best welfare; best two-level schedule (11 off-peak hours at 4.5, 13 peak hours at 9.2) loses 1.8%; no price loses 42.6%.