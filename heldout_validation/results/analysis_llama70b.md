# Held-out replication (N = 1,000 fresh SQuAD 2.0 questions); judge = llama70b

## Qwen2.5-0.5B  (n questions = 1000, hallucinations = 619, correct answers = 379)

| measure | held-out | 95% CI | original (300 q) |
|---|---|---|---|
| hallucination rate % | 61.9 | | 60.3 |
| L2 clearance c2 % | 91.3 | [88.9, 93.4] | 89.5 |
| L3 clearance c3 % | 84.0 | [81.2, 86.9] | 58.0 |
| L2 false-block % | 24.0 | [19.9, 28.6] | 15.1 |
| L3 false-block % | 10.0 | [7.2, 13.3] | 24.4 |
| judge failure rate % | 0.0 | | 25-30 |
| phi(L2, L3 catch) | 0.22 | [0.12, 0.34] | 0.11-0.15 |  (Fisher p = 0.000)
| passing both: observed (full) / independence % | 3.7 / 1.4 | | |
| ratio observed/independence (full) | 2.66 | [1.91, 3.56] | 1.5 |
| ratio observed/independence (routed) | 4.98 | [4.13, 6.16] | 2.1 |
| k* none / L2 / L2+L3 routed (200 q/day) | 142 / 16 / 14 | [136, 149] / [13, 20] / [11, 17] | 139 / 19 / 17 |
| capacity reduction by L2 % | 88.7 | [85.9, 90.8] | |

## SmolLM2-360M  (n questions = 1000, hallucinations = 658, correct answers = 313)

| measure | held-out | 95% CI | original (300 q) |
|---|---|---|---|
| hallucination rate % | 65.8 | | 65.0 |
| L2 clearance c2 % | 97.7 | [96.6, 98.8] | 96.9 |
| L3 clearance c3 % | 86.0 | [83.4, 88.6] | 48.2 |
| L2 false-block % | 75.1 | [70.1, 79.6] | 70.9 |
| L3 false-block % | 13.7 | [10.1, 17.6] | 16.5 |
| judge failure rate % | 0.0 | | 25-30 |
| phi(L2, L3 catch) | 0.14 | [0.03, 0.25] | 0.11-0.15 |  (Fisher p = 0.002)
| passing both: observed (full) / independence % | 1.1 / 0.3 | | |
| ratio observed/independence (full) | 3.34 | [1.49, 5.28] | 1.6 |
| ratio observed/independence (routed) | 3.81 | [1.94, 5.70] | 1.9 |
| k* none / L2 / L2+L3 routed (200 q/day) | 151 / 6 / 4 | [144, 157] / [4, 8] / [2, 6] | 149 / 8 / 8 |
| capacity reduction by L2 % | 96.0 | [94.6, 97.4] | |

## Qwen2.5-1.5B  (n questions = 1000, hallucinations = 478, correct answers = 470)

| measure | held-out | 95% CI | original (300 q) |
|---|---|---|---|
| hallucination rate % | 47.8 | | 47.0 |
| L2 clearance c2 % | 87.4 | [84.3, 90.4] | 81.6 |
| L3 clearance c3 % | 78.2 | [74.2, 81.9] | 58.9 |
| L2 false-block % | 18.7 | [15.4, 22.1] | 15.4 |
| L3 false-block % | 9.8 | [7.2, 12.5] | 22.8 |
| judge failure rate % | 0.0 | | 25-30 |
| phi(L2, L3 catch) | 0.31 | [0.21, 0.41] | 0.11-0.15 |  (Fisher p = 0.000)
| passing both: observed (full) / independence % | 6.9 / 2.7 | | |
| ratio observed/independence (full) | 2.53 | [2.04, 3.16] | 1.3 |
| ratio observed/independence (routed) | 4.37 | [3.67, 5.24] | 2.3 |
| k* none / L2 / L2+L3 routed (200 q/day) | 112 / 18 / 17 | [105, 118] / [14, 22] / [14, 21] | 110 / 24 / 24 |
| capacity reduction by L2 % | 83.9 | [80.7, 87.3] | |
