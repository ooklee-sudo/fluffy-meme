# Marginal-cost calibration of the peak/off-peak price ratio

Prices include the serving cost c0 (units: service times of user delay cost; choke value P = 20).

## Code trace (c=7)

| c0 | tolls off-peak / peak | price ratio (peak/off-peak) | best flat price (incl. c0) | flat-price loss % of first best |
|---|---|---|---|---|
| 0 | 0.54 / 16.53 | 30.8x | 1.9 | 10.1% |
| 2 | 0.51 / 14.74 | 6.7x | 3.7 | 10.1% |
| 4 | 0.48 / 12.96 | 3.8x | 5.5 | 10.0% |
| 6 | 0.44 / 11.18 | 2.7x | 7.3 | 10.0% |
| 8 | 0.40 / 9.41 | 2.1x | 9.2 | 9.9% |
| 10 | 0.35 / 7.65 | 1.7x | 11.0 | 9.8% |
| 12 | 0.29 / 5.90 | 1.5x | 12.8 | 9.8% |
| 14 | 0.22 / 4.16 | 1.3x | 14.6 | 9.8% |
| 16 | 0.13 / 2.45 | 1.1x | 16.4 | 9.9% |
| 18 | 0.02 / 0.78 | 1.0x | 18.1 | 11.4% |

Price ratio 4x is reached at c0 ~ 3.9 (flat loss there ~ 10.0% of first best).

Price ratio 2x is reached at c0 ~ 8.4 (flat loss there ~ 9.9% of first best).

## Conversation trace (c=45)

| c0 | tolls off-peak / peak | price ratio (peak/off-peak) | best flat price (incl. c0) | flat-price loss % of first best |
|---|---|---|---|---|
| 0 | 1.19 / 8.63 | 7.2x | 6.4 | 6.4% |
| 2 | 1.06 / 7.68 | 3.2x | 7.7 | 6.3% |
| 4 | 0.93 / 6.74 | 2.2x | 9.0 | 6.1% |
| 6 | 0.79 / 5.79 | 1.7x | 10.3 | 6.0% |
| 8 | 0.65 / 4.85 | 1.5x | 11.5 | 5.8% |
| 10 | 0.50 / 3.90 | 1.3x | 12.8 | 5.6% |
| 12 | 0.34 / 2.96 | 1.2x | 14.1 | 5.3% |
| 14 | 0.19 / 2.01 | 1.1x | 15.4 | 4.8% |
| 16 | 0.05 / 1.07 | 1.1x | 16.8 | 3.9% |
| 18 | 0.00 / 0.15 | 1.0x | 18.1 | 0.8% |

Price ratio 4x is reached at c0 ~ 1.6 (flat loss there ~ 6.3% of first best).

Price ratio 2x is reached at c0 ~ 4.8 (flat loss there ~ 6.1% of first best).
