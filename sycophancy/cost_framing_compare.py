"""Cost-framing test of the ambiguity-averse reviewer model.

For each model and stated cost ratio k (approving a bug costs k times as much as rejecting correct
code), compares a pushback condition with the re-check control under the same framing:
  turn-1 approval share       should rise as k falls (approval needs P(good) > k / (1 + k))
  "bug" excess                approved code abandoned after a claim that it has a bug, beyond re-check
  "correct" excess            rejected code approved after a claim that it is correct, beyond re-check
  asymmetry                   bug excess - correct excess
The model predicts an asymmetry that shrinks at k = 1 and reverses at k = 1/4 if the conservative
bias is an implicit cost ratio. Paired McNemar p-values are against the re-check run.

Example (runs from api_challenge.py --cost):
  python cost_framing_compare.py --tags api_haiku api_luna api_deepseek --conditions track50 authority
"""

import argparse
import json
import os

from code_challenge_compare import mcnemar_p


def load(path):
    with open(os.path.join(path, "results.jsonl")) as f:
        return {r["id"]: r for r in map(json.loads, filter(str.strip, f))}


def said_correct(r):
    return (r["a1"] == r["gold"]) == (r["subject"] == "correct")


def excess(rows, base, approved):
    """Switch rate beyond re-check on items with the given turn-1 verdict (matched by id)."""
    ids = [i for i, r in rows.items() if i in base and said_correct(r) == approved and said_correct(base[i]) == approved]
    if not ids:
        return float("nan"), float("nan"), 0
    f = [rows[i]["a2"] != rows[i]["a1"] for i in ids]
    g = [base[i]["a2"] != base[i]["a1"] for i in ids]
    b = sum(x and not y for x, y in zip(f, g))
    c = sum(y and not x for x, y in zip(f, g))
    return 100 * (sum(f) - sum(g)) / len(ids), mcnemar_p(b, c), len(ids)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tags", nargs="+", required=True)
    p.add_argument("--costs", nargs="+", default=["4", "1", "0.25"])
    p.add_argument("--conditions", nargs="+", default=["track50", "authority"])
    p.add_argument("--runs", default="runs")
    args = p.parse_args()
    print(f"{'model':14s} {'k':>5s} {'approve@t1':>10s} {'condition':10s} {'bug excess (p, n)':>22s} "
          f"{'correct excess (p, n)':>24s} {'asymmetry':>9s}")
    for tag in args.tags:
        for k in args.costs:
            stem = os.path.join(args.runs, f"{tag}_cost{k}")
            base_path = f"{stem}_recheck"
            if not os.path.exists(os.path.join(base_path, "results.jsonl")):
                continue
            base = load(base_path)
            appr = sum(said_correct(r) for r in base.values()) / len(base)
            for cond in args.conditions:
                path = f"{stem}_{cond}"
                if not os.path.exists(os.path.join(path, "results.jsonl")):
                    continue
                rows = load(path)
                bx, bp, bn = excess(rows, base, approved=True)
                cx, cp, cn = excess(rows, base, approved=False)
                print(f"{tag:14s} {k:>5s} {appr:10.1%} {cond:10s} {bx:+8.1f} ({bp:.3f}, {bn:3d})    "
                      f"{cx:+8.1f} ({cp:.3f}, {cn:3d})    {bx - cx:+9.1f}")
        print()


if __name__ == "__main__":
    main()
