# Congestion wedge: measured throughput vs. welfare

## Code trace (c=7)

### Adoption sweep (per unit of capacity; a = mean demand potential / capacity)

| a | scenario | throughput Q/c | gross value V/c | waiting cost Dc/c | welfare W/c | Dc/V |
|---|---|---|---|---|---|---|
| 0.5 | bursty, no price | 0.28 | 3.29 | 1.03 | 2.26 | 31% |
|  | bursty, best flat (p=4.1) | 0.23 | 3.14 | 0.78 | 2.37 | 25% |
|  | bursty, phase-optimal | 0.27 | 3.23 | 0.32 | 2.90 | 10% |
| 0.5 | Poisson, no price | 0.47 | 4.99 | 0.48 | 4.50 | 10% |
|  | Poisson, best flat (p=0.1) | 0.47 | 4.98 | 0.48 | 4.50 | 10% |
|  | Poisson, phase-optimal | 0.47 | 4.98 | 0.48 | 4.50 | 10% |
| 0.8 | bursty, no price | 0.41 | 4.77 | 1.24 | 3.53 | 26% |
|  | bursty, best flat (p=2.6) | 0.36 | 4.65 | 1.06 | 3.59 | 23% |
|  | bursty, phase-optimal | 0.41 | 4.70 | 0.47 | 4.23 | 10% |
| 0.8 | Poisson, no price | 0.75 | 7.97 | 0.92 | 7.05 | 12% |
|  | Poisson, best flat (p=1.0) | 0.71 | 7.91 | 0.83 | 7.08 | 10% |
|  | Poisson, phase-optimal | 0.71 | 7.91 | 0.83 | 7.08 | 10% |
| 1.0 | bursty, no price | 0.51 | 5.74 | 1.36 | 4.38 | 24% |
|  | bursty, best flat (p=2.1) | 0.46 | 5.64 | 1.20 | 4.43 | 21% |
|  | bursty, phase-optimal | 0.50 | 5.67 | 0.56 | 5.10 | 10% |
| 1.0 | Poisson, no price | 0.90 | 9.90 | 1.81 | 8.08 | 18% |
|  | Poisson, best flat (p=2.6) | 0.80 | 9.61 | 1.09 | 8.52 | 11% |
|  | Poisson, phase-optimal | 0.80 | 9.60 | 1.08 | 8.52 | 11% |
| 1.2 | bursty, no price | 0.60 | 6.71 | 1.49 | 5.22 | 22% |
|  | bursty, best flat (p=1.9) | 0.54 | 6.60 | 1.32 | 5.28 | 20% |
|  | bursty, phase-optimal | 0.59 | 6.63 | 0.66 | 5.96 | 10% |
| 1.2 | Poisson, no price | 0.96 | 11.51 | 3.86 | 7.66 | 34% |
|  | Poisson, best flat (p=4.5) | 0.84 | 10.92 | 1.27 | 9.65 | 12% |
|  | Poisson, phase-optimal | 0.84 | 10.93 | 1.28 | 9.65 | 12% |
| 1.4 | bursty, no price | 0.69 | 7.67 | 1.63 | 6.04 | 21% |
|  | bursty, best flat (p=1.8) | 0.63 | 7.55 | 1.45 | 6.10 | 19% |
|  | bursty, phase-optimal | 0.66 | 7.57 | 0.78 | 6.79 | 10% |
| 1.4 | Poisson, no price | 0.97 | 12.70 | 5.93 | 6.78 | 47% |
|  | Poisson, best flat (p=6.1) | 0.86 | 11.91 | 1.40 | 10.51 | 12% |
|  | Poisson, phase-optimal | 0.86 | 11.92 | 1.41 | 10.51 | 12% |
| 1.8 | bursty, no price | 0.85 | 9.57 | 2.16 | 7.42 | 23% |
|  | bursty, best flat (p=2.5) | 0.75 | 9.32 | 1.67 | 7.66 | 18% |
|  | bursty, phase-optimal | 0.78 | 9.34 | 1.03 | 8.31 | 11% |
| 1.8 | Poisson, no price | 0.98 | 14.29 | 8.92 | 5.37 | 62% |
|  | Poisson, best flat (p=8.4) | 0.88 | 13.31 | 1.59 | 11.72 | 12% |
|  | Poisson, phase-optimal | 0.88 | 13.30 | 1.58 | 11.72 | 12% |
| 2.4 | bursty, no price | 0.96 | 12.01 | 4.78 | 7.23 | 40% |
|  | bursty, best flat (p=4.9) | 0.84 | 11.35 | 1.86 | 9.49 | 16% |
|  | bursty, phase-optimal | 0.85 | 11.36 | 1.33 | 10.03 | 12% |
| 2.4 | Poisson, no price | 0.99 | 15.68 | 11.62 | 4.06 | 74% |
|  | Poisson, best flat (p=10.6) | 0.89 | 14.55 | 1.74 | 12.81 | 12% |
|  | Poisson, phase-optimal | 0.89 | 14.52 | 1.72 | 12.81 | 12% |

### Dispersion sweep at a = 1.4 (0 = Poisson, 1 = fitted trace)

| spread | Dc/V no price | W/c no price | Dc/V best flat | W/c best flat |
|---|---|---|---|---|
| 0.0 | 46.7% | 6.78 | 11.7% | 10.51 |
| 0.25 | 39.4% | 7.27 | 14.9% | 9.63 |
| 0.5 | 28.2% | 7.75 | 16.4% | 8.64 |
| 0.75 | 21.6% | 7.27 | 17.6% | 7.46 |
| 1.0 | 21.3% | 6.04 | 19.2% | 6.10 |

## Conversation trace (c=45)

### Adoption sweep (per unit of capacity; a = mean demand potential / capacity)

| a | scenario | throughput Q/c | gross value V/c | waiting cost Dc/c | welfare W/c | Dc/V |
|---|---|---|---|---|---|---|
| 0.5 | bursty, no price | 0.47 | 4.99 | 0.48 | 4.51 | 10% |
|  | bursty, best flat (p=0.0) | 0.47 | 4.99 | 0.48 | 4.51 | 10% |
|  | bursty, phase-optimal | 0.47 | 4.99 | 0.47 | 4.51 | 10% |
| 0.5 | Poisson, no price | 0.47 | 4.99 | 0.48 | 4.51 | 10% |
|  | Poisson, best flat (p=0.0) | 0.47 | 4.99 | 0.48 | 4.51 | 10% |
|  | Poisson, phase-optimal | 0.47 | 4.99 | 0.47 | 4.51 | 10% |
| 0.8 | bursty, no price | 0.75 | 7.97 | 0.93 | 7.03 | 12% |
|  | bursty, best flat (p=1.3) | 0.71 | 7.89 | 0.75 | 7.13 | 10% |
|  | bursty, phase-optimal | 0.73 | 7.93 | 0.76 | 7.17 | 10% |
| 0.8 | Poisson, no price | 0.76 | 7.98 | 0.76 | 7.22 | 10% |
|  | Poisson, best flat (p=0.1) | 0.76 | 7.98 | 0.76 | 7.22 | 10% |
|  | Poisson, phase-optimal | 0.76 | 7.98 | 0.76 | 7.22 | 10% |
| 1.0 | bursty, no price | 0.88 | 9.77 | 2.00 | 7.76 | 21% |
|  | bursty, best flat (p=3.8) | 0.75 | 9.37 | 0.90 | 8.46 | 10% |
|  | bursty, phase-optimal | 0.84 | 9.65 | 0.91 | 8.73 | 9% |
| 1.0 | Poisson, no price | 0.94 | 9.96 | 1.14 | 8.82 | 11% |
|  | Poisson, best flat (p=1.2) | 0.89 | 9.87 | 0.94 | 8.93 | 10% |
|  | Poisson, phase-optimal | 0.89 | 9.87 | 0.95 | 8.93 | 10% |
| 1.2 | bursty, no price | 0.95 | 11.28 | 3.55 | 7.73 | 31% |
|  | bursty, best flat (p=5.1) | 0.80 | 10.67 | 1.18 | 9.50 | 11% |
|  | bursty, phase-optimal | 0.90 | 11.06 | 1.03 | 10.03 | 9% |
| 1.2 | Poisson, no price | 0.99 | 11.64 | 3.44 | 8.19 | 30% |
|  | Poisson, best flat (p=3.4) | 0.93 | 11.38 | 1.07 | 10.31 | 9% |
|  | Poisson, phase-optimal | 0.93 | 11.38 | 1.07 | 10.31 | 9% |
| 1.4 | bursty, no price | 0.98 | 12.48 | 5.28 | 7.21 | 42% |
|  | bursty, best flat (p=6.4) | 0.84 | 11.69 | 1.33 | 10.36 | 11% |
|  | bursty, phase-optimal | 0.93 | 12.18 | 1.11 | 11.07 | 9% |
| 1.4 | Poisson, no price | 1.00 | 12.83 | 5.75 | 7.08 | 45% |
|  | Poisson, best flat (p=5.4) | 0.94 | 12.47 | 1.13 | 11.34 | 9% |
|  | Poisson, phase-optimal | 0.94 | 12.49 | 1.14 | 11.34 | 9% |
| 1.8 | bursty, no price | 1.00 | 14.15 | 8.37 | 5.78 | 59% |
|  | bursty, best flat (p=8.4) | 0.88 | 13.20 | 1.55 | 11.66 | 12% |
|  | bursty, phase-optimal | 0.95 | 13.74 | 1.21 | 12.53 | 9% |
| 1.8 | Poisson, no price | 1.00 | 14.42 | 8.89 | 5.53 | 62% |
|  | Poisson, best flat (p=8.2) | 0.95 | 13.97 | 1.20 | 12.76 | 9% |
|  | Poisson, phase-optimal | 0.95 | 13.99 | 1.23 | 12.76 | 9% |
| 2.4 | bursty, no price | 1.00 | 15.61 | 11.26 | 4.35 | 72% |
|  | bursty, best flat (p=10.4) | 0.91 | 14.68 | 1.72 | 12.96 | 12% |
|  | bursty, phase-optimal | 0.96 | 15.12 | 1.28 | 13.85 | 8% |
| 2.4 | Poisson, no price | 1.00 | 15.81 | 11.66 | 4.15 | 74% |
|  | Poisson, best flat (p=10.7) | 0.96 | 15.30 | 1.28 | 14.03 | 8% |
|  | Poisson, phase-optimal | 0.96 | 15.31 | 1.29 | 14.03 | 8% |

### Dispersion sweep at a = 1.4 (0 = Poisson, 1 = fitted trace)

| spread | Dc/V no price | W/c no price | Dc/V best flat | W/c best flat |
|---|---|---|---|---|
| 0.0 | 44.8% | 7.08 | 9.1% | 11.34 |
| 0.25 | 44.6% | 7.10 | 9.5% | 11.22 |
| 0.5 | 43.9% | 7.15 | 10.1% | 10.96 |
| 0.75 | 42.9% | 7.22 | 10.8% | 10.66 |
| 1.0 | 42.3% | 7.21 | 11.4% | 10.36 |
