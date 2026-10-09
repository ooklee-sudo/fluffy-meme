# Flat-price loss vs. switching speed (code-trace MMPP, exact CTMC)

| f (dwell multiplier) | mean burst (service times) | best flat welfare | phase-dependent welfare | flat loss |
|---|---|---|---|---|
| 0.005 | 0.02 | 71.01 (p=6) | 71.20 | 0.28% |
| 0.01 | 0.04 | 68.94 (p=7) | 69.44 | 0.72% |
| 0.02 | 0.08 | 65.94 (p=7) | 66.82 | 1.32% |
| 0.05 | 0.21 | 59.91 (p=7) | 62.19 | 3.66% |
| 0.1 | 0.41 | 54.12 (p=8) | 58.22 | 7.05% |
| 0.2 | 0.82 | 48.40 (p=8) | 54.55 | 11.27% |
| 0.5 | 2.06 | 42.25 (p=7) | 50.93 | 17.03% |
| 1.0 | 4.12 | 39.99 (p=7) | 49.37 | 19.01% |
| 2.0 | 8.23 | 40.18 (p=8) | 48.36 | 16.91% |
| 5.0 | 20.58 | 39.63 (p=5) | 47.76 | 17.03% |

Log-log slope of the loss against f over f = 0.005..0.05: 1.09 (about 1, i.e. roughly linear in f; a quadratic rate was conjectured but is NOT supported). Planner/flat grids limit the resolution to about +/-1-2 percentage points (f=1 gave 20.9% in results/theory_check.md Part C with a different grid).
