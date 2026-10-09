# Equilibrium demand on trace-calibrated bursty arrivals

## Code trace: fitted MMPP(2)

c=7, unpriced demand = 1.4x capacity, choke value P=20 service times. Planner optimum welfare (trace_pricing.py): 49.37.

| policy | price by phase | equilibrium rate by phase | rho | sojourn by phase | welfare | top mass |
|---|---|---|---|---|---|---|
| no price | 0.0, 0.0 | 24.6, 3.7 | 0.67 | 15.2, 5.0 | 29.30 | 9.4e-13 |
| burst-blind flat (Poisson-optimal p=6) | 6.0, 6.0 | 20.2, 2.9 | 0.53 | 10.1, 2.6 | 39.78 | 2.4e-16 |
| best flat (p=8) | 8.0, 8.0 | 18.3, 2.6 | 0.48 | 8.4, 2.0 | 40.09 | -6.7e-16 |
| phase prices implementing planner optimum | 14.9, 0.7 | 10.2, 4.5 | 0.68 | 3.1, 1.3 | 49.37 | 7.8e-16 |

Loss vs implemented optimum: no price 41%, burst-blind flat 19%, best flat 19%. Implied optimal phase prices (before clipping at 0): 14.9, 0.7

## Conversation trace: 5-state rate chain

c=45, unpriced demand = 1.4x capacity, choke value P=20 service times. Planner optimum welfare (trace_pricing.py): 497.82.

| policy | price by phase | equilibrium rate by phase | rho | sojourn by phase | welfare | top mass |
|---|---|---|---|---|---|---|
| no price | 0.0, 0.0, 0.0, 0.0, 0.0 | 36.0, 40.5, 44.1, 47.1, 49.6 | 0.97 | 3.9, 4.7, 5.5, 6.5, 8.3 | 307.04 | 2.6e-03 |
| burst-blind flat (Poisson-optimal p=0) | 0.0, 0.0, 0.0, 0.0, 0.0 | 36.0, 40.5, 44.1, 47.1, 49.6 | 0.97 | 3.9, 4.7, 5.5, 6.5, 8.3 | 307.04 | 2.6e-03 |
| best flat (p=6) | 6.0, 6.0, 6.0, 6.0, 6.0 | 29.1, 34.0, 38.5, 42.7, 47.5 | 0.86 | 1.1, 1.2, 1.3, 1.7, 2.9 | 466.71 | 4.4e-07 |
| phase prices implementing planner optimum | 1.9, 2.8, 4.8, 6.8, 8.8 | 38.2, 42.3, 42.6, 41.7, 42.5 | 0.92 | 1.1, 1.2, 1.2, 1.2, 1.2 | 497.82 | -5.3e-15 |

Loss vs implemented optimum: no price 38%, burst-blind flat 38%, best flat 6%. Implied optimal phase prices (before clipping at 0): 1.9, 2.8, 4.8, 6.8, 8.8
