# Arrival-model comparison on the Azure traces (1-hour paths, 100 replications per model)

## Conversation trace

rate 5.53/s, mean service 6.91s (tau). rate-chain states (req/s): 4.0, 4.7, 5.4, 6.1, 7.5; stay-probabilities per 30 s: 0.61, 0.41, 0.37, 0.36, 0.78

| c | rho | arrivals | E[wait] mean | E[wait] median | P(wait>tau) mean | P 10-90% |
|---|---|---|---|---|---|---|
| 64 | 0.60 | real | 0.00 | - | 0.000 | - |
|  |  | block-boot | 0.01 | 0.01 | 0.000 | 0.000-0.000 |
|  |  | poisson | 0.00 | 0.00 | 0.000 | 0.000-0.000 |
|  |  | mmpp2 | 5.66 | 0.44 | 0.103 | 0.000-0.347 |
|  |  | rate-chain | 0.01 | 0.01 | 0.000 | 0.000-0.000 |
| 51 | 0.75 | real | 0.08 | - | 0.000 | - |
|  |  | block-boot | 1.91 | 1.82 | 0.122 | 0.017-0.216 |
|  |  | poisson | 0.01 | 0.01 | 0.000 | 0.000-0.000 |
|  |  | mmpp2 | 19.84 | 1.25 | 0.157 | 0.000-0.491 |
|  |  | rate-chain | 1.33 | 1.00 | 0.067 | 0.000-0.186 |
| 45 | 0.85 | real | 0.52 | - | 0.007 | - |
|  |  | block-boot | 11.87 | 9.59 | 0.318 | 0.081-0.549 |
|  |  | poisson | 0.17 | 0.17 | 0.000 | 0.000-0.000 |
|  |  | mmpp2 | 36.61 | 2.20 | 0.208 | 0.000-0.660 |
|  |  | rate-chain | 12.78 | 10.63 | 0.363 | 0.146-0.598 |
| 42 | 0.91 | real | 2.20 | - | 0.111 | - |
|  |  | block-boot | 27.24 | 20.76 | 0.499 | 0.210-0.767 |
|  |  | poisson | 0.62 | 0.60 | 0.003 | 0.000-0.008 |
|  |  | mmpp2 | 51.22 | 3.89 | 0.241 | 0.000-0.741 |
|  |  | rate-chain | 30.97 | 23.65 | 0.524 | 0.239-0.781 |

Servers needed for P(wait>tau) <= 5%: real replay 43; block-boot 53; poisson 41; mmpp2 72; rate-chain 52

## Code trace

rate 2.57/s, mean service 1.86s (tau). rate-chain states (req/s): 2.5, 0.0, 1.3, 3.3, 7.6; stay-probabilities per 30 s: 0.20, 0.52, 0.05, 0.18, 0.37

| c | rho | arrivals | E[wait] mean | E[wait] median | P(wait>tau) mean | P 10-90% |
|---|---|---|---|---|---|---|
| 9 | 0.53 | real | 23.25 | - | 0.829 | - |
|  |  | block-boot | 20.88 | 19.83 | 0.813 | 0.761-0.867 |
|  |  | poisson | 0.02 | 0.02 | 0.001 | 0.000-0.002 |
|  |  | mmpp2 | 32.47 | 30.09 | 0.625 | 0.500-0.737 |
|  |  | rate-chain | 17.42 | 15.26 | 0.703 | 0.597-0.804 |
| 8 | 0.60 | real | 30.84 | - | 0.875 | - |
|  |  | block-boot | 28.08 | 26.79 | 0.870 | 0.825-0.911 |
|  |  | poisson | 0.07 | 0.07 | 0.005 | 0.001-0.008 |
|  |  | mmpp2 | 43.04 | 38.74 | 0.664 | 0.536-0.774 |
|  |  | rate-chain | 28.13 | 24.38 | 0.753 | 0.645-0.849 |
| 7 | 0.68 | real | 43.11 | - | 0.925 | - |
|  |  | block-boot | 40.48 | 38.31 | 0.918 | 0.888-0.949 |
|  |  | poisson | 0.22 | 0.21 | 0.026 | 0.012-0.041 |
|  |  | mmpp2 | 61.40 | 54.06 | 0.715 | 0.576-0.827 |
|  |  | rate-chain | 49.21 | 38.07 | 0.813 | 0.712-0.910 |
| 6 | 0.80 | real | 112.21 | - | 0.975 | - |
|  |  | block-boot | 69.59 | 66.81 | 0.957 | 0.932-0.977 |
|  |  | poisson | 0.77 | 0.75 | 0.141 | 0.105-0.181 |
|  |  | mmpp2 | 101.78 | 83.05 | 0.786 | 0.633-0.909 |
|  |  | rate-chain | 91.98 | 68.38 | 0.888 | 0.809-0.956 |

Servers needed for P(wait>tau) <= 5%: real replay 38; block-boot 42; poisson 7; mmpp2 45; rate-chain 16
