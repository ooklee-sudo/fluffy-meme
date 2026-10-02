## Break-even flexibility premium (person-weeks), by effort reduction, vendor-price correlation and volume

Premium below the value is worth paying: expected saving over 36 months from halving (phi) the migration effort and choosing the cheaper vendor at retirement, no early switching.

| Tokens/month | Alt. price correlation | phi=0.3 | phi=0.5 | phi=0.8 |
|---|---|---|---|---|
| 100 M | 0.0 | 37.5 [35.8, 39.3] | 32.9 [31.1, 34.6] | 25.4 [23.7, 27.2] |
| 100 M | 0.5 | 31.7 [30.2, 33.2] | 27.1 [25.6, 28.6] | 19.6 [18.1, 21.1] |
| 100 M | 1.0 | 19.1 [18.8, 19.5] | 14.5 [14.2, 14.8] | 7.0 [6.8, 7.2] |
| 1000 M | 0.0 | 203.1 [185.8, 220.4] | 198.4 [181.2, 215.7] | 191.0 [173.7, 208.2] |
| 1000 M | 0.5 | 145.0 [130.4, 159.6] | 140.3 [125.8, 154.9] | 132.9 [118.3, 147.5] |
| 1000 M | 1.0 | 19.1 [18.8, 19.5] | 14.5 [14.2, 14.8] | 7.0 [6.8, 7.2] |
| 10000 M | 0.0 | 1858.7 [1686.1, 2031.2] | 1854.0 [1681.5, 2026.6] | 1846.6 [1674.0, 2019.1] |
| 10000 M | 0.5 | 1277.8 [1132.2, 1423.4] | 1273.1 [1127.5, 1418.7] | 1265.7 [1120.1, 1411.3] |
| 10000 M | 1.0 | 19.1 [18.8, 19.5] | 14.5 [14.2, 14.8] | 7.0 [6.8, 7.2] |

## Break-even with no price shock at retirement (successor price unchanged), labor effect only

| Effort (triangular weeks) | phi=0.3 | phi=0.5 | phi=0.8 |
|---|---|---|---|
| (2, 4, 10) | 19.6 [19.2, 19.9] | 14.8 [14.5, 15.1] | 7.3 [7.1, 7.4] |
| (4, 8, 20) | 85.4 [83.7, 87.2] | 73.0 [71.5, 74.5] | 38.5 [37.7, 39.3] |

Mean number of forced retirements in 36 months (base): 4.41.

## Switching rules: threshold (real-options) versus simple net-present-value rule, paired difference in cost (USD, positive = threshold cheaper)

| Scenario | NPV rule cost | Threshold cost | Difference [95% CI] | Early switches NPV | Early switches threshold |
|---|---|---|---|---|---|
| price-gap volatility 0.05/month (theta 1.5) | 379,401 | 390,898 | -11,498 [-29,711, 6,715] | 1.0 | 0.7 |
| 0.10 (theta 2.1) | 327,059 | 352,640 | -25,581 [-40,154, -11,009] | 1.7 | 0.8 |
| 0.20 (theta 4.2) | 251,262 | 309,605 | -58,343 [-68,680, -48,005] | 2.5 | 0.7 |
| 0.36 (theta 9.7) | 187,709 | 291,481 | -103,772 [-111,715, -95,829] | 2.7 | 0.4 |
| 0.10, no price shock at retirement | 102,484 | 102,703 | -219 [-240, -199] | 0.3 | 0.0 |
