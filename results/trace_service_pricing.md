# Pricing under non-exponential service times (simulation, equilibrium demand)

## Code trace: fitted MMPP(2)

c=7, horizon 40000 service times, unpriced demand 1.4x capacity, P=20. Welfare by policy (equilibrium demand) and loss relative to the best phase-dependent welfare.

| service cs2 | no price | Poisson-blind flat | best flat | phase-dependent | implied phase prices | loss: none / blind / flat |
|---|---|---|---|---|---|---|
| 0.5 | 30.8 | 40.6 (p=6) | 40.6 (p=6) | 49.7 | 15.1, 0.8 | 38% / 18% / 18% |
| 1.0 | 29.8 | 40.3 (p=6) | 40.3 (p=6) | 49.6 | 15.1, 0.8 | 40% / 19% / 19% |
| 4.0 | 30.2 | 40.0 (p=6) | 40.0 (p=6) | 48.9 | 15.0, 0.6 | 38% / 18% / 18% |
| 16.0 | 29.1 | 39.5 (p=8) | 39.7 (p=6) | 47.9 | 15.0, 2.6 | 39% / 18% / 17% |

## Conversation trace: 5-state rate chain

c=45, horizon 15000 service times, unpriced demand 1.4x capacity, P=20. Welfare by policy (equilibrium demand) and loss relative to the best phase-dependent welfare.

| service cs2 | no price | Poisson-blind flat | best flat | phase-dependent | implied phase prices | loss: none / blind / flat |
|---|---|---|---|---|---|---|
| 0.5 | 146.1 | 382.9 (p=2) | 467.2 (p=6) | 499.8 | 0.9, 2.9, 4.8, 6.9, 8.8 | 71% / 23% / 7% |
| 1.0 | 165.6 | 378.0 (p=2) | 467.0 (p=6) | 497.8 | 0.9, 2.8, 4.8, 6.8, 8.8 | 67% / 24% / 6% |
| 4.0 | 191.1 | 465.4 (p=6) | 465.4 (p=6) | 492.6 | 0.8, 2.7, 4.6, 6.7, 8.6 | 61% / 6% / 6% |
| 16.0 | 274.4 | 461.7 (p=6) | 461.7 (p=6) | 479.8 | 0.6, 2.6, 4.6, 8.8, 8.6 | 43% / 4% / 4% |
