"""Cohen's kappa for exposure coding.

Usage: python kappa_exposure.py coder1.csv coder2.csv
Each file: repo,launch_type,exposed   (launch_type in open_weights/openai/anthropic/google; exposed 0/1)
Rows are matched on (repo, launch_type). Disagreements are listed for adjudication.
"""
import csv, sys
from score import kappa


def read(p):
    with open(p, newline="", encoding="utf-8") as f:
        return {(r["repo"], r["launch_type"]): int(r["exposed"]) for r in csv.DictReader(f)}


a, b = read(sys.argv[1]), read(sys.argv[2])
keys = sorted(set(a) & set(b))
x, y = [a[k] for k in keys], [b[k] for k in keys]
print(f"cells = {len(keys)}  agreement = {sum(i == j for i, j in zip(x, y)) / len(keys):.3f}  kappa = {kappa(x, y):.3f}")
for k in keys:
    if a[k] != b[k]:
        print("disagree:", k, a[k], b[k])
