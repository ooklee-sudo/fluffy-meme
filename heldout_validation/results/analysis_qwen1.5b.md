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
