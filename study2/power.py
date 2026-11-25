"""Simulation-based power for the planned Study 2 (within-subject, 6 of 24 rooms per participant, 3 per condition).
Outcome in SD units; crossed participant and room random intercepts; effect = standardized condition effect d.
Analysis = participant-level paired difference with room-level variance included in the data-generating process."""
import numpy as np
from math import sqrt
rng = np.random.default_rng(1)
def power(n, d, icc_p=0.25, icc_r=0.25, reps=2000):
    hits = 0
    for _ in range(reps):
        u = rng.normal(0, sqrt(icc_p), n); v = rng.normal(0, sqrt(icc_r), 24)
        diffs = []
        for i in range(n):
            rooms = rng.permutation(24)[:6]; cond = np.array([0, 0, 0, 1, 1, 1]); rng.shuffle(cond)
            y = u[i] + v[rooms] + d * cond + rng.normal(0, sqrt(1 - icc_p - icc_r), 6)
            diffs.append(y[cond == 1].mean() - y[cond == 0].mean())
        t = np.mean(diffs) / (np.std(diffs, ddof=1) / sqrt(n)); hits += abs(t) > 1.98
    return hits / reps
for n in (60, 90, 120, 160):
    print(n, {d: round(power(n, d, reps=1000), 2) for d in (0.15, 0.2, 0.3, 0.4)})
