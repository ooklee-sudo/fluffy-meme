> Note: the column 'old kappa-only formula' omits the factor (1 + kappa t') and understates the loss by roughly an order of magnitude. The corrected local formula is Proposition 4 in paper_notes/theory.md and is checked in results/theory_verify.md.

# Analytic reinforcement: Harberger loss of flat pricing under bursty demand

## Conversation trace: quasi-static analysis (c=45)

### A  Flat-price loss vs. demand dispersion (spread 1 = fitted trace, 0 = Poisson)

| spread | CV of demand potential | std of Pigouvian toll | best flat p | exact loss | old kappa-only formula (SUPERSEDED: understates; see results/theory_verify.md) | loss % of first best | no-price loss % |
|---|---|---|---|---|---|---|---|
| 0.0 | 0.00 | 0.00 | 5.4 | 0.00 | 0.00 | 0.0% | 37.6% |
| 0.25 | 0.05 | 0.66 | 5.6 | 4.83 | 0.49 | 0.9% | 37.3% |
| 0.5 | 0.11 | 1.31 | 5.9 | 14.29 | 1.92 | 2.8% | 36.6% |
| 0.75 | 0.16 | 1.95 | 6.1 | 23.73 | 4.24 | 4.7% | 35.5% |
| 1.0 | 0.22 | 2.56 | 6.4 | 31.81 | 7.23 | 6.4% | 34.9% |

### B  Monopolist pricing (spread 1)

| policy | price(s) | profit rate | welfare |
|---|---|---|---|
| flat price | 9.7 | 283.7 | 421.0 |
| phase prices | 9.5, 9.5, 9.5, 9.5, 9.9 | 283.8 | 422.7 |
| (welfare first best) | - | - | 498.1 |

## Code trace: quasi-static analysis (c=7)

### A  Flat-price loss vs. demand dispersion (spread 1 = fitted trace, 0 = Poisson)

| spread | CV of demand potential | std of Pigouvian toll | best flat p | exact loss | old kappa-only formula (SUPERSEDED: understates; see results/theory_verify.md) | loss % of first best | no-price loss % |
|---|---|---|---|---|---|---|---|
| 0.0 | 0.00 | 0.00 | 6.1 | 0.00 | 0.00 | 0.0% | 35.5% |
| 0.25 | 0.54 | 2.03 | 5.0 | 2.66 | 0.73 | 3.8% | 27.4% |
| 0.5 | 1.08 | 2.70 | 3.6 | 3.72 | 1.29 | 5.8% | 15.5% |
| 0.75 | 1.61 | 3.18 | 2.4 | 4.43 | 1.79 | 7.8% | 10.1% |
| 1.0 | 2.15 | 3.48 | 1.9 | 4.83 | 2.13 | 10.1% | 11.1% |

### B  Monopolist pricing (spread 1)

| policy | price(s) | profit rate | welfare |
|---|---|---|---|
| flat price | 10.2 | 24.7 | 34.0 |
| phase prices | 16.6, 9.5 | 26.5 | 37.4 |
| (welfare first best) | - | - | 47.6 |

## C  Switching speed, code-trace MMPP (exact CTMC; f = dwell-time multiplier)

| f | mean burst length (service times) | best flat welfare | phase-dependent welfare | flat loss |
|---|---|---|---|---|
| 0.2 | 0.8 | 47.85 (p=8) | 54.55 | 12.3% |
| 1.0 | 4.1 | 39.07 (p=6) | 49.37 | 20.9% |
| 5.0 | 20.6 | 39.43 (p=4) | 47.76 | 17.5% |
