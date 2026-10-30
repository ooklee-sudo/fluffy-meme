# Held-out replication (N = 1,000 fresh SQuAD 2.0 questions); judge = qwen1.5b

## Qwen2.5-0.5B  (n questions = 1000, hallucinations = 619, correct answers = 379)

| measure | held-out | 95% CI | original (300 q) |
|---|---|---|---|
| hallucination rate % | 61.9 | | 60.3 |
| L2 clearance c2 % | 91.3 | [88.9, 93.4] | 89.5 |
| L3 clearance c3 % | 24.7 | [21.6, 28.0] | 58.0 |
| L2 false-block % | 24.0 | [19.9, 28.6] | 15.1 |
| L3 false-block % | 2.9 | [1.4, 4.7] | 24.4 |
| judge failure rate % | 26.8 | | 25-30 |
| phi(L2, L3 catch) | 0.18 | [0.15, 0.21] | 0.11-0.15 |  (Fisher p = 0.000)
| passing both: observed (full) / independence % | 8.7 / 6.6 | | |
| ratio observed/independence (full) | 1.33 | [1.28, 1.39] | 1.5 |
| ratio observed/independence (routed) | 1.33 | [1.28, 1.39] | 2.1 |
| k* none / L2 / L2+L3 routed (200 q/day) | 142 / 16 / 16 | [136, 149] / [13, 20] / [13, 20] | 139 / 19 / 17 |
| capacity reduction by L2 % | 88.7 | [85.9, 90.8] | |

## SmolLM2-360M  (n questions = 1000, hallucinations = 658, correct answers = 313)

| measure | held-out | 95% CI | original (300 q) |
|---|---|---|---|
| hallucination rate % | 65.8 | | 65.0 |
| L2 clearance c2 % | 97.7 | [96.6, 98.8] | 96.9 |
| L3 clearance c3 % | 20.1 | [17.0, 23.1] | 48.2 |
| L2 false-block % | 75.1 | [70.1, 79.6] | 70.9 |
| L3 false-block % | 1.3 | [0.3, 2.7] | 16.5 |
| judge failure rate % | 30.6 | | 25-30 |
| phi(L2, L3 catch) | 0.08 | [0.06, 0.10] | 0.11-0.15 |  (Fisher p = 0.051)
| passing both: observed (full) / independence % | 2.3 / 1.8 | | |
| ratio observed/independence (full) | 1.25 | [1.21, 1.30] | 1.6 |
| ratio observed/independence (routed) | 1.25 | [1.21, 1.30] | 1.9 |
| k* none / L2 / L2+L3 routed (200 q/day) | 151 / 6 / 6 | [144, 157] / [4, 8] / [4, 8] | 149 / 8 / 8 |
| capacity reduction by L2 % | 96.0 | [94.6, 97.4] | |

## Qwen2.5-1.5B  (n questions = 1000, hallucinations = 478, correct answers = 470)

| measure | held-out | 95% CI | original (300 q) |
|---|---|---|---|
| hallucination rate % | 47.8 | | 47.0 |
| L2 clearance c2 % | 87.4 | [84.3, 90.4] | 81.6 |
| L3 clearance c3 % | 19.2 | [15.8, 22.8] | 58.9 |
| L2 false-block % | 18.7 | [15.4, 22.1] | 15.4 |
| L3 false-block % | 3.8 | [2.3, 5.6] | 22.8 |
| judge failure rate % | 25.8 | | 25-30 |
| phi(L2, L3 catch) | 0.18 | [0.16, 0.21] | 0.11-0.15 |  (Fisher p = 0.000)
| passing both: observed (full) / independence % | 12.6 / 10.1 | | |
| ratio observed/independence (full) | 1.24 | [1.19, 1.29] | 1.3 |
| ratio observed/independence (routed) | 1.24 | [1.19, 1.29] | 2.3 |
| k* none / L2 / L2+L3 routed (200 q/day) | 112 / 18 / 18 | [105, 118] / [14, 22] / [14, 22] | 110 / 24 / 24 |
| capacity reduction by L2 % | 83.9 | [80.7, 87.3] | |
