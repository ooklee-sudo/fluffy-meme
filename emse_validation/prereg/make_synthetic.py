"""Synthetic data to test confirmatory_analysis.py (planted effect: exposed repos release sooner after launches)."""
import csv, datetime as dt, random, sys

out, effect = sys.argv[1], float(sys.argv[2])
rng = random.Random(3)
start = dt.date(2025, 1, 1)
repos = [f"r{i}" for i in range(12)]
types = ["open_weights", "openai", "anthropic", "google"]
exposed = {(r, t): int(rng.random() < 0.45) for r in repos for t in types}
launches = [(f"L{i}", start + dt.timedelta(days=60 + 25 * i), types[i % 4]) for i in range(16)]
rel = []
for r in repos:
    d = start
    while d < start + dt.timedelta(days=520):
        d += dt.timedelta(days=max(1, int(rng.expovariate(1 / 9))))
        rel.append((r, d))
    for _, ld, lt in launches:
        if exposed[(r, lt)] and rng.random() < effect:
            rel.append((r, ld + dt.timedelta(days=rng.randint(0, 2))))
with open(f"{out}/releases.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["repo", "published_at"]); w.writerows(sorted(rel))
with open(f"{out}/launches.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["launch_id", "announce_date", "launch_type"]); w.writerows(launches)
with open(f"{out}/exposure.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["repo", "launch_type", "exposed"])
    for (r, t), e in exposed.items(): w.writerow([r, t, e])
