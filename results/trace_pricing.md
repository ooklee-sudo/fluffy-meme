> Note: in this file the 'flat' policy forces the same *marginal-benefit level* (full cost incl. delay) in every phase, which is not a posted price and
> overstates the flat-pricing loss. The posted-price (equilibrium) comparison is in results/trace_equilibrium.md and results/trace_service_pricing.md;
> use those numbers.

# Pricing on trace-calibrated bursty arrivals

## Conversation trace: 5-state rate chain

c=45, mean load 38.5 (rho=0.86); phase rates (per service time): 27.5, 32.3, 37.2, 42.5, 51.9; phase probabilities: 0.18, 0.21, 0.21, 0.19, 0.21; E[sojourn] bursty 3.53 vs Poisson 1.03

### E3  Pigouvian toll per request (units: one service time of delay)

Poisson (same mean): 0.59; bursty average: 37.0 (62x); by phase 3.0, 5.3, 11.9, 30.5, 95.2

### E4  Welfare under elastic demand (tolls in service-time delay costs)

| policy | welfare | loss vs phase-dependent | tolls by phase |
|---|---|---|---|
| burst-blind flat (lower bound on loss: queue cap reached) | 245.09 | 50.8% | 6.9, 6.9, 6.9, 6.9, 6.9 |
| best flat | 453.21 | 9.0% | 9.2, 9.2, 9.2, 9.2, 9.2 |
| phase-dependent | 497.82 | 0.0% | 3.0, 4.0, 6.0, 8.0, 10.0 |

## Code trace: fitted MMPP(2)

c=7, mean load 4.8 (rho=0.68); phase rates (per service time): 49.6, 2.4; phase probabilities: 0.05, 0.95; E[sojourn] bursty 37.63 vs Poisson 1.12

### E3  Pigouvian toll per request (units: one service time of delay)

Poisson (same mean): 0.73; bursty average: 119.2 (163x); by phase 182.4, 51.0

### E4  Welfare under elastic demand (tolls in service-time delay costs)

| policy | welfare | loss vs phase-dependent | tolls by phase |
|---|---|---|---|
| burst-blind flat (lower bound on loss: queue cap reached) | -489.82 | 1092.1% | 7.6, 7.6 |
| best flat | 23.79 | 51.8% | 15.8, 15.8 |
| phase-dependent | 49.37 | 0.0% | 18.0, 2.0 |
