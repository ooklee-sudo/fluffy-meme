## Table 2. Base configuration (beta = 0, equal-link budget, 30 paired replications)

| | Concentrated | Distributed |
|---|---|---|
| Mean cumulative adopters at 1 h | 37 | 17 |
| Mean cumulative adopters at 2 h | 66 | 28 |
| Mean cumulative adopters at 3 h | 91 | 36 |
| Mean cumulative adopters at 6 h | 135 | 47 |
| Mean cumulative adopters at 12 h | 149 | 49 |
| Mean cumulative adopters at 48 h | 152 | 50 |
| SD of final adopters | 34 | 8 |
| Minimum of final adopters | 96 | 32 |
| CVaR_0.2 (mean of worst 20%) | 112 | 39 |
| Mean t50 (h) | 2.39 | 1.70 |
| Number of seeds (mean) | 3 | 622 |

Paired difference in final adopters: 102 [90, 115]; concentrated ahead in 30 of 30 replications.
Paired difference in t50 (concentrated minus distributed): 0.69 [0.50, 0.87] h.
- Discounted reach, delta = 0.0: C 151.5, D 50.0, paired diff 101.5 [89.4, 114.3]
- Discounted reach, delta = 0.25: C 84.4, D 31.4, paired diff 53.0 [46.4, 60.5]
- Discounted reach, delta = 0.5: C 56.8, D 22.7, paired diff 34.1 [29.6, 39.1]
- Discounted reach, delta = 1.0: C 34.0, D 14.6, paired diff 19.4 [16.7, 22.3]
- Discounted reach, delta = 2.0: C 19.1, D 8.5, paired diff 10.6 [9.0, 12.2]
- First-order stochastic dominance of concentrated on final adopters (all empirical quantiles): True
- Mean cumulative adopters higher for concentrated at 48 of 48 hourly points (all hours: True)
- Distributed strictly ahead after 1 h in 0% of replications
- Distributed strictly ahead after 2 h in 0% of replications

## Table 3. Concentrated minus distributed under alternative schedulers (beta = 0, 18:00 injection)

| Scheduler | Adopters (C / D) | Ratio C/D | Delta adopters (SE) [95% CI] | Delta t50, h (SE) [95% CI] | CVaR_0.2 (C / D) |
|---|---|---|---|---|---|
| Event-driven IPP (proposed) | 152 / 50 | 3.03 | 102 (6.3) [90, 115] | 0.69 (0.10) [0.50, 0.88] | 112 / 39 |
| Circadian-only IPP | 328 / 80 | 4.10 | 248 (18.4) [212, 287] | 0.97 (0.11) [0.76, 1.19] | 205 / 67 |
| Homogeneous Poisson | 276 / 77 | 3.57 | 199 (14.2) [172, 228] | 1.46 (0.15) [1.16, 1.77] | 184 / 65 |
| Fixed-period polling | 277 / 71 | 3.88 | 205 (14.7) [177, 235] | 1.25 (0.16) [0.95, 1.56] | 178 / 61 |

Volume-matching multiplier from pilot runs without a campaign: 2.00

## Table 4. Effect of injection time

| Injection | Scheduler | Adopters (C / D) | Delta adopters (SE) [95% CI] | t50, h (C / D) |
|---|---|---|---|---|
| 03:00 | Event-driven IPP | 80 / 28 | 52 (5.0) [43, 62] | 2.32 / 2.05 |
| 03:00 | Circadian-only | 256 / 59 | 197 (22.5) [154, 242] | 7.38 / 4.60 |
| 09:00 | Event-driven IPP | 111 / 47 | 65 (9.2) [48, 84] | 2.49 / 2.17 |
| 09:00 | Circadian-only | 338 / 83 | 255 (19.3) [219, 296] | 3.71 / 2.30 |
| 18:00 | Event-driven IPP | 159 / 50 | 108 (8.8) [92, 127] | 2.50 / 1.71 |
| 18:00 | Circadian-only | 342 / 81 | 260 (25.0) [214, 310] | 2.60 / 1.54 |

## Table 5. Hybrid portfolios (beta = 0)

| Pricing C(f) | k | Seeds | Mean adopters (SD) | CVaR_0.2 | V(delta=1/h) | t50 (h) |
|---|---|---|---|---|---|---|
| f (equal links) | 0 | 629 | 50 (9) | 38 | 15 | 1.71 |
|  | 1 | 378 | 84 (27) | 60 | 23 | 1.85 |
|  | 2 | 180 | 133 (40) | 85 | 30 | 2.33 |
|  | 3 | 3 | 159 (38) | 114 | 35 | 2.50 |
| f^0.7 (concave) | 0 | 134 | 16 (5) | 10 | 5 | 1.76 |
|  | 1 | 84 | 78 (44) | 34 | 16 | 2.33 |
|  | 2 | 41 | 116 (36) | 70 | 25 | 2.33 |
|  | 3 | 3 | 159 (38) | 114 | 35 | 2.50 |
| 10 + f (fixed fee) | 0 | 90 | 9 (5) | 4 | 3 | 1.65 |
|  | 1 | 55 | 77 (43) | 38 | 17 | 2.19 |
|  | 2 | 27 | 126 (55) | 76 | 27 | 2.31 |
|  | 3 | 3 | 159 (38) | 114 | 35 | 2.50 |

## Table 6. Concentrated vs. distributed seeding by engagement elasticity beta (equal-link budget)

| beta | Replications | Adopters (C / D) | Delta adopters (SE) [95% CI] | P(C > D) | Delta V(delta=1/h) (SE) [95% CI] | CVaR_0.2 (C / D) | Adopters at 1 h (C / D) |
|---|---|---|---|---|---|---|---|
| 0.00 | 15 | 157 / 53 | 104 (8.8) [86, 121] | 1.00 | 18.2 (1.9) [14.4, 21.9] | 108 / 42 | 37 / 18 |
| 0.05 | 15 | 139 / 47 | 92 (9.9) [73, 112] | 1.00 | 17.1 (1.9) [13.3, 20.6] | 95 / 38 | 34 / 16 |
| 0.10 | 15 | 117 / 59 | 58 (8.1) [41, 74] | 0.93 | 11.5 (1.3) [8.7, 14.2] | 83 / 45 | 31 / 20 |
| 0.15 | 15 | 128 / 61 | 68 (11.5) [46, 92] | 1.00 | 7.8 (2.2) [3.7, 12.5] | 76 / 48 | 26 / 21 |
| 0.20 | 15 | 106 / 63 | 43 (8.1) [28, 59] | 0.93 | 3.2 (1.6) [0.0, 6.4] | 74 / 49 | 24 / 20 |
| 0.25 | 15 | 110 / 65 | 46 (10.4) [27, 68] | 0.87 | 1.3 (1.1) [-0.9, 3.5] | 64 / 55 | 22 / 22 |
| 0.30 | 15 | 84 / 66 | 18 (7.6) [3, 33] | 0.67 | -1.8 (1.6) [-5.0, 1.3] | 57 / 54 | 20 / 23 |
| 0.35 | 30 | 79 / 70 | 9 (6.3) [-2, 22] | 0.47 | -5.0 (0.9) [-6.7, -3.2] | 48 / 59 | 16 / 24 |
| 0.40 | 30 | 68 / 73 | -5 (5.5) [-15, 7] | 0.27 | -6.2 (0.9) [-7.9, -4.4] | 41 / 59 | 14 / 22 |
| 0.45 | 30 | 66 / 73 | -7 (5.3) [-17, 3] | 0.27 | -8.8 (1.0) [-10.6, -6.9] | 35 / 61 | 13 / 24 |
| 0.50 | 15 | 55 / 74 | -19 (8.3) [-33, -1] | 0.13 | -11.6 (1.2) [-13.9, -9.2] | 33 / 59 | 11 / 25 |
| 0.60 | 30 | 47 / 80 | -33 (4.3) [-41, -24] | 0.07 | -13.2 (0.9) [-14.9, -11.5] | 27 / 60 | 9 / 25 |
| 0.66 | 15 | 69 / 82 | -13 (12.2) [-36, 12] | 0.27 | -14.2 (0.8) [-15.8, -12.7] | 28 / 71 | 9 / 26 |

Eq. (2) check: R0 = 3.03, mean followers per concentrated seed f_C = 335, beta* ~ ln R0 / ln(f_C/10) = 0.32
