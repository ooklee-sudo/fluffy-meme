# Held-out replication (N = 1,000 fresh SQuAD 2.0 questions); judge = gemma27b (slow verdicts credited; exploratory)

## Qwen2.5-0.5B  (n questions = 1000, hallucinations = 619, correct answers = 379)

| measure | held-out | 95% CI | original (300 q) |
|---|---|---|---|
| hallucination rate % | 61.9 | | 60.3 |
| L2 clearance c2 % | 91.3 | [88.9, 93.4] | 89.5 |
| L3 clearance c3 % | 61.2 | [57.5, 65.5] | 58.0 |
| L2 false-block % | 24.0 | [19.9, 28.6] | 15.1 |
| L3 false-block % | 3.2 | [1.6, 5.2] | 24.4 |
| judge failure rate % | 0.0 | | 25-30 |
| phi(L2, L3 catch) | 0.24 | [0.16, 0.31] | 0.11-0.15 |  (Fisher p = 0.000)
| passing both: observed (full) / independence % | 6.6 / 3.4 | | |
| ratio observed/independence (full) | 1.96 | [1.64, 2.29] | 1.5 |
| ratio observed/independence (routed) | 2.48 | [2.23, 2.78] | 2.1 |
| k* none / L2 / L2+L3 routed (200 q/day) | 142 / 16 / 16 | [136, 149] / [13, 20] / [13, 20] | 139 / 19 / 17 |
| capacity reduction by L2 % | 88.7 | [85.9, 90.8] | |

## SmolLM2-360M  (n questions = 1000, hallucinations = 658, correct answers = 313)

| measure | held-out | 95% CI | original (300 q) |
|---|---|---|---|
| hallucination rate % | 65.8 | | 65.0 |
| L2 clearance c2 % | 97.7 | [96.6, 98.8] | 96.9 |
| L3 clearance c3 % | 68.5 | [65.1, 72.2] | 48.2 |
| L2 false-block % | 75.1 | [70.1, 79.6] | 70.9 |
| L3 false-block % | 5.8 | [3.3, 8.3] | 16.5 |
| judge failure rate % | 0.0 | | 25-30 |
| phi(L2, L3 catch) | 0.09 | [0.00, 0.17] | 0.11-0.15 |  (Fisher p = 0.023)
| passing both: observed (full) / independence % | 1.4 / 0.7 | | |
| ratio observed/independence (full) | 1.91 | [1.04, 2.69] | 1.6 |
| ratio observed/independence (routed) | 2.12 | [1.38, 2.85] | 1.9 |
| k* none / L2 / L2+L3 routed (200 q/day) | 151 / 6 / 5 | [144, 157] / [4, 8] / [3, 6] | 149 / 8 / 8 |
| capacity reduction by L2 % | 96.0 | [94.6, 97.4] | |

## Qwen2.5-1.5B  (n questions = 1000, hallucinations = 478, correct answers = 470)

| measure | held-out | 95% CI | original (300 q) |
|---|---|---|---|
| hallucination rate % | 47.8 | | 47.0 |
| L2 clearance c2 % | 87.4 | [84.3, 90.4] | 81.6 |
| L3 clearance c3 % | 54.0 | [49.7, 58.3] | 58.9 |
| L2 false-block % | 18.7 | [15.4, 22.1] | 15.4 |
| L3 false-block % | 2.1 | [0.9, 3.5] | 22.8 |
| judge failure rate % | 0.0 | | 25-30 |
| phi(L2, L3 catch) | 0.22 | [0.14, 0.31] | 0.11-0.15 |  (Fisher p = 0.000)
| passing both: observed (full) / independence % | 9.4 / 5.8 | | |
| ratio observed/independence (full) | 1.63 | [1.40, 1.88] | 1.3 |
| ratio observed/independence (routed) | 2.10 | [1.90, 2.33] | 2.3 |
| k* none / L2 / L2+L3 routed (200 q/day) | 112 / 18 / 17 | [105, 118] / [14, 22] / [14, 21] | 110 / 24 / 24 |
| capacity reduction by L2 % | 83.9 | [80.7, 87.3] | |
