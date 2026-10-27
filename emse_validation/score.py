"""Score manual validation: inter-coder kappa, and precision/recall of the study classifier.

Usage: python score.py OUT_DIR [--adjudicated adjudicated.csv]

Reads sheet_coder1.csv, sheet_coder2.csv, key.csv from OUT_DIR. Optional adjudicated.csv
(id,label) gives the reference label when coders disagree; otherwise coder 1 and 2 must
agree or the row is dropped from precision/recall.

Precision = P(true | pred=1), estimated in the pred=1 stratum.
Recall    = TP / (TP + FN) with strata re-weighted by stratum size (the sample is 50/50).
Wilson 95% intervals; the recall interval is a delta-method-free bootstrap over the sample.
"""
import argparse, csv, math, os, random


def kappa(a, b):
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return (po - pe) / (1 - pe) if pe < 1 else float("nan")


def wilson(k, n, z=1.96):
    if n == 0:
        return (float("nan"),) * 2
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def load(path):
    with open(path, newline="", encoding="utf-8") as f:
        return {r["id"]: r for r in csv.DictReader(f)}


def recall(items):
    # items: list of (pred, truth, stratum_size)
    tp = sum(s * (t == 1) for p, t, s in items if p == 1) / max(1, sum(1 for p, _, _ in items if p == 1))
    fn = sum(s * (t == 1) for p, t, s in items if p == 0) / max(1, sum(1 for p, _, _ in items if p == 0))
    return tp / (tp + fn) if tp + fn else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--adjudicated")
    a = ap.parse_args()

    s1 = load(os.path.join(a.dir, "sheet_coder1.csv"))
    s2 = load(os.path.join(a.dir, "sheet_coder2.csv"))
    key = load(os.path.join(a.dir, "key.csv"))
    adj = {k: int(v["label"]) for k, v in load(a.adjudicated).items()} if a.adjudicated else {}

    ids = sorted(key)
    l1 = [int(s1[i]["label"]) for i in ids]
    l2 = [int(s2[i]["label"]) for i in ids]
    print(f"n = {len(ids)}  raw agreement = {sum(x == y for x, y in zip(l1, l2)) / len(ids):.3f}  Cohen's kappa = {kappa(l1, l2):.3f}")

    items = []
    for i, x, y in zip(ids, l1, l2):
        t = adj.get(i, x if x == y else None)
        if t is not None:
            items.append((int(key[i]["pred"]), t, int(key[i]["stratum_size"])))
    dropped = len(ids) - len(items)
    if dropped:
        print(f"{dropped} disagreements without adjudication dropped")

    pos = [t for p, t, _ in items if p == 1]
    k, n = sum(pos), len(pos)
    lo, hi = wilson(k, n)
    print(f"precision = {k}/{n} = {k / n:.3f}  (Wilson 95% {lo:.3f}-{hi:.3f})")

    r = recall(items)
    rng = random.Random(0)
    bs = sorted(recall([rng.choice(items) for _ in items]) for _ in range(2000))
    bs = [x for x in bs if x == x]
    print(f"recall (stratum-weighted) = {r:.3f}  (bootstrap 95% {bs[int(.025 * len(bs))]:.3f}-{bs[int(.975 * len(bs))]:.3f})")


if __name__ == "__main__":
    main()
