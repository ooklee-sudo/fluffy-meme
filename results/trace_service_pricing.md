# Pricing under non-exponential service times (simulation, equilibrium demand)

## Code trace: fitted MMPP(2)

c=7, horizon 40000 service times, unpriced demand 1.4x capacity, P=20. Welfare by policy (equilibrium demand) and loss relative to the best phase-dependent welfare.

| service cs2 | no price | Poisson-blind flat | best flat | phase-dependent | implied phase prices | loss: none / blind / flat |
|---|---|---|---|---|---|---|
| 0.5 | 30.8 | 40.6 (p=6) | 40.6 (p=6) | 49.7 | 15.1, 0.8 | 38% / 18% / 18% |
| 1.0 | 29.8 | 40.3 (p=6) | 40.3 (p=6) | 49.6 | 15.1, 0.8 | 40% / 19% / 19% |
| 4.0 | 30.2 | 40.0 (p=6) | 40.0 (p=6) | 48.9 | 15.0, 0.6 | 38% / 18% / 18% |
| 16.0 | 29.1 | 39.5 (p=8) | 39.7 (p=6) | 47.9 | 15.0, 2.6 | 39% / 18% / 17% |
