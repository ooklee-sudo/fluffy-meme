# Held-out replication (N = 1,000 fresh SQuAD 2.0 questions); judge = smollm1.7b (slow verdicts credited; exploratory)

## Qwen2.5-0.5B  (n questions = 1000, hallucinations = 619, correct answers = 379)

| measure | held-out | 95% CI | original (300 q) |
|---|---|---|---|
| hallucination rate % | 61.9 | | 60.3 |
| L2 clearance c2 % | 91.3 | [88.9, 93.4] | 89.5 |
| L3 clearance c3 % | 98.9 | [98.1, 99.7] | 58.0 |
| L2 false-block % | 24.0 | [19.9, 28.6] | 15.1 |
| L3 false-block % | 99.2 | [98.2, 100.0] | 24.4 |
| judge failure rate % | 94.8 | | 25-30 |
| phi(L2, L3 catch) | 0.02 | [-0.04, 0.14] | 0.11-0.15 |  (Fisher p = 0.474)
| passing both: observed (full) / independence % | 0.2 / 0.1 | | |
| ratio observed/independence (full) | 1.64 | [0.00, 5.29] | 1.5 |
| ratio observed/independence (routed) | 50.76 | [27.10, 145.37] | 2.1 |
| k* none / L2 / L2+L3 routed (200 q/day) | 142 / 16 / 11 | [136, 149] / [13, 20] / [8, 14] | 139 / 19 / 17 |
| capacity reduction by L2 % | 88.7 | [85.9, 90.8] | |

## SmolLM2-360M  (n questions = 1000, hallucinations = 658, correct answers = 313)

| measure | held-out | 95% CI | original (300 q) |
|---|---|---|---|
| hallucination rate % | 65.8 | | 65.0 |
| L2 clearance c2 % | 97.7 | [96.6, 98.8] | 96.9 |
| L3 clearance c3 % | 99.8 | [99.5, 100.0] | 48.2 |
| L2 false-block % | 75.1 | [70.1, 79.6] | 70.9 |
| L3 false-block % | 98.7 | [97.4, 99.7] | 16.5 |
| judge failure rate % | 96.2 | | 25-30 |
| phi(L2, L3 catch) | -0.01 | [-0.01, 0.00] | 0.11-0.15 |  (Fisher p = 1.000)
| passing both: observed (full) / independence % | 0.0 / 0.0 | | |
| ratio observed/independence (full) | 0.00 | [0.00, 0.00] | 1.6 |
| ratio observed/independence (routed) | 131.60 | [0.00, 254.50] | 1.9 |
| k* none / L2 / L2+L3 routed (200 q/day) | 151 / 6 / 2 | [144, 157] / [4, 8] / [0, 4] | 149 / 8 / 8 |
| capacity reduction by L2 % | 96.0 | [94.6, 97.4] | |

## Qwen2.5-1.5B  (n questions = 1000, hallucinations = 478, correct answers = 470)

| measure | held-out | 95% CI | original (300 q) |
|---|---|---|---|
| hallucination rate % | 47.8 | | 47.0 |
| L2 clearance c2 % | 87.4 | [84.3, 90.4] | 81.6 |
| L3 clearance c3 % | 99.2 | [98.3, 99.8] | 58.9 |
| L2 false-block % | 18.7 | [15.4, 22.1] | 15.4 |
| L3 false-block % | 98.9 | [97.9, 99.8] | 22.8 |
| judge failure rate % | 91.1 | | 25-30 |
| phi(L2, L3 catch) | 0.03 | [-0.04, 0.17] | 0.11-0.15 |  (Fisher p = 0.416)
| passing both: observed (full) / independence % | 0.2 / 0.1 | | |
| ratio observed/independence (full) | 1.99 | [0.00, 7.41] | 1.3 |
| ratio observed/independence (routed) | 93.61 | [46.05, 384.47] | 2.3 |
| k* none / L2 / L2+L3 routed (200 q/day) | 112 / 18 / 15 | [105, 118] / [14, 22] / [11, 18] | 110 / 24 / 24 |
| capacity reduction by L2 % | 83.9 | [80.7, 87.3] | |
