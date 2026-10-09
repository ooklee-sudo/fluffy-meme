# MMPP vs. Poisson in inference serving: numerical results

## E1  Delay at equal utilisation (c=8 replicas, mu=1; time in mean service times)

Burst process: 20% of time in burst, rate k x off-rate, mean burst length T service times.

| rho | arrivals | IDC(inf) | E[sojourn] | ratio vs Poisson | P(wait>1.0) | tail ratio |
|---|---|---|---|---|---|---|
| 0.5 | Poisson | 1.0 | 1.01 | 1.00 | 0.0011 | 1.0 |
| 0.5 | MMPP k=3,T=2 | 5.2 | 1.17 | 1.15 | 0.0563 | 52.1 |
| 0.5 | MMPP k=3,T=20 | 42.8 | 2.01 | 1.98 | 0.2623 | 242.5 |
| 0.5 | MMPP k=6,T=2 | 13.8 | 1.76 | 1.73 | 0.2540 | 234.9 |
| 0.5 | MMPP k=6,T=20 | 129.0 | 8.96 | 8.83 | 0.5901 | 545.7 |
| 0.5 | MMPP k=6,T=100 | 641.0 | 40.96 | 40.37 | 0.6502 | 601.2 |
| 0.7 | Poisson | 1.0 | 1.11 | 1.00 | 0.0245 | 1.0 |
| 0.7 | MMPP k=3,T=2 | 6.9 | 1.88 | 1.69 | 0.2784 | 11.3 |
| 0.7 | MMPP k=3,T=20 | 59.5 | 8.75 | 7.87 | 0.5202 | 21.2 |
| 0.7 | MMPP k=6,T=2 | 18.9 | 3.93 | 3.53 | 0.5431 | 22.1 |
| 0.7 | MMPP k=6,T=20 | 180.2 | 30.31 | 27.24 | 0.7400 | 30.1 |
| 0.7 | MMPP k=6,T=100 | 897.0 | 136.90 | 123.03 | 0.7613 | 31.0 |
| 0.8 | Poisson | 1.0 | 1.29 | 1.00 | 0.0924 | 1.0 |
| 0.8 | MMPP k=3,T=2 | 7.7 | 2.91 | 2.26 | 0.4486 | 4.9 |
| 0.8 | MMPP k=3,T=20 | 67.9 | 17.61 | 13.69 | 0.6360 | 6.9 |
| 0.8 | MMPP k=6,T=2 | 21.5 | 6.77 | 5.26 | 0.6847 | 7.4 |
| 0.8 | MMPP k=6,T=20 | 205.8 | 57.15 | 44.44 | 0.8157 | 8.8 |
| 0.8 | MMPP k=6,T=100 | 1025.0 | 204.75 | 159.21 | 0.8183 | 8.9 |
| 0.9 | Poisson | 1.0 | 1.88 | 1.00 | 0.3152 | 1.0 |
| 0.9 | MMPP k=3,T=2 | 8.5 | 6.11 | 3.25 | 0.6759 | 2.1 |
| 0.9 | MMPP k=3,T=20 | 76.2 | 44.31 | 23.61 | 0.7860 | 2.5 |
| 0.9 | MMPP k=6,T=2 | 24.0 | 15.36 | 8.18 | 0.8341 | 2.6 |
| 0.9 | MMPP k=6,T=20 | 231.4 | 127.51 | 67.93 | 0.8993 | 2.9 |
| 0.9 | MMPP k=6,T=100 | 1153.0 | 271.60 | 144.71 | 0.8707 | 2.8 |

## E2  Replicas needed for P(wait > 1.0) <= 0.01 at mean load 10.0 (mu=1)

| arrivals | IDC(inf) | replicas needed | extra | extra % |
|---|---|---|---|---|
| Poisson | 1.0 | 14 | 0 | 0% |
| MMPP k=2,T=5 | 9.9 | 19 | 5 | 36% |
| MMPP k=3,T=5 | 27.1 | 23 | 9 | 64% |
| MMPP k=3,T=20 | 105.5 | 24 | 10 | 71% |
| MMPP k=6,T=5 | 81.0 | 32 | 18 | 129% |
| MMPP k=6,T=20 | 321.0 | 33 | 19 | 136% |

## E3  Congestion externality per request (cost unit: one service time of one user's delay), rho=0.8, c=8

| arrivals | mean toll / arrival | vs Poisson | toll in burst | toll off-burst |
|---|---|---|---|---|
| Poisson | 2.22 | 2.22 | - | - |
| MMPP k=3,T=5 | 28.23 (fd 28.38) | 12.7x | 49.09 | 12.59 |
| MMPP k=3,T=20 | 106.58 (fd 107.12) | 48.0x | 191.07 | 43.21 |
| MMPP k=6,T=5 | 82.23 (fd 82.64) | 37.0x | 109.17 | 41.81 |
| MMPP k=6,T=20 | 322.21 (fd 323.83) | 145.0x | 430.74 | 159.42 |

## E4  Welfare under elastic demand (c=4, unpriced demand = 1.4 x capacity, P_max = 20 service-time delay costs)

| arrivals | W burst-blind flat | W best flat | W burst-aware 2-price | loss of blind flat | loss of best flat | tolls H/L |
|---|---|---|---|---|---|---|
| k=1,T=5 | 40.23 | 40.23 | 40.17 | -0.1% | -0.1% | 9.0/8.0 |
| k=3,T=5 | 24.11 | 32.96 | 37.33 | 35.4% | 11.7% | 13.0/6.0 |
| k=3,T=20 | -23.55 | 28.23 | 36.85 | 163.9% | 23.4% | 14.0/5.0 |
| k=6,T=20 | -173.84 | 21.07 | 30.81 | 664.2% | 31.6% | 15.0/3.0 |
