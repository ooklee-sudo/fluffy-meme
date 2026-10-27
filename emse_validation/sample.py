"""Draw blinded, stratified coding sheets for manual validation.

Usage: python sample.py {issues|notes} INPUT.csv OUT_DIR [--n 100] [--seed 1] [--coders 2]

issues: INPUT needs columns id,repo,title,labels,body,pred  (pred = 1 if the study classified it as a bug)
notes : INPUT needs columns id,repo,text,pred               (pred = 1 if keyword matched / entry flagged as fix)

Half of the sample comes from pred=1 and half from pred=0, so that both precision
and recall can be estimated. The strata are written to key.csv (do NOT give it to coders).
Coders receive one sheet each with the same rows in independent random order and a
blank `label` column (1/0).
"""
import argparse, csv, os, random


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["issues", "notes"])
    ap.add_argument("inp")
    ap.add_argument("out")
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--coders", type=int, default=2)
    a = ap.parse_args()

    rng = random.Random(a.seed)
    with open(a.inp, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    pos = [r for r in rows if r["pred"] == "1"]
    neg = [r for r in rows if r["pred"] == "0"]
    half = a.n // 2
    if len(pos) < half or len(neg) < half:
        raise SystemExit(f"need >= {half} rows in each stratum (pos={len(pos)}, neg={len(neg)})")
    pick = rng.sample(pos, half) + rng.sample(neg, half)

    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "key.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "pred", "stratum_size"])
        for r in pick:
            w.writerow([r["id"], r["pred"], len(pos) if r["pred"] == "1" else len(neg)])

    show = [c for c in rows[0] if c not in ("pred",)]
    for k in range(1, a.coders + 1):
        order = pick[:]
        random.Random(a.seed * 1000 + k).shuffle(order)
        with open(os.path.join(a.out, f"sheet_coder{k}.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(show + ["label"])
            for r in order:
                w.writerow([r[c] for c in show] + [""])
    print(f"wrote {a.coders} sheets + key.csv to {a.out} ({len(pick)} rows each)")


if __name__ == "__main__":
    main()
