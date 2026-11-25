"""Measurement diagnostics for Study 1 (no outcome variables used).

Split-half reliability of Bradley-Terry photo scores, positional bias, and split-half
reliability of review-based experience scores.
Usage: python reliability.py WORKDIR PAIRS_JSONL REVIEWS_JSONL
"""
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, ".")
from analyze_study1 import bradley_terry, ATT

def load_pairs(path):
    raw = {}
    for l in open(path):
        x = json.loads(l); raw.setdefault((x["a"], x["b"]), {})[x["order"]] = x["res"]
    return {k: v for k, v in raw.items() if len(v) == 2}

def scores(raw, att, grp, keys):
    wins = {}
    for k in keys:
        v = raw[k]; a, b = k
        if v["AB"].get(att) not in ("A", "B") or v["BA"].get(att) not in ("A", "B"): continue
        if grp.get(a) != grp.get(b): continue
        w1 = v["AB"][att] == "A"; w2 = v["BA"][att] == "B"
        wa = 1.0 if (w1 and w2) else (0.0 if (not w1 and not w2) else 0.5)
        wins[(a, b)] = wa; wins[(b, a)] = 1 - wa
    out = {}
    byg = {}
    for (a, b), w in wins.items(): byg.setdefault(grp[a], {})[(a, b)] = w
    for g, wg in byg.items(): out.update(bradley_terry(wg))
    return out

def main(work, pairs, revs):
    s = pd.read_csv(f"{work}/sample.csv"); grp = (s.city + "|" + s.room_type).set_axis(s.id).to_dict()
    raw = load_pairs(pairs); keys = sorted(raw); rng = np.random.default_rng(3)
    print("pairs with both orders:", len(keys))
    print("\nPositional bias (share choosing the FIRST photo) and order-reversal rate")
    for att in ATT:
        first = np.mean([(v["AB"].get(att) == "A") for v in raw.values() if v["AB"].get(att) in "AB"] + [(v["BA"].get(att) == "A") for v in raw.values() if v["BA"].get(att) in "AB"])
        rev = np.mean([(v["AB"].get(att) == "A") != (v["BA"].get(att) == "B") for v in raw.values() if v["AB"].get(att) in "AB" and v["BA"].get(att) in "AB"])
        print(f"  {att:22s} first-position share {first:.3f}   reversal {rev:.3f}")
    print("\nSplit-half reliability of BT scores (random halves of pairs; Spearman-Brown corrected)")
    perm = rng.permutation(len(keys)); h1 = [keys[i] for i in perm[: len(keys) // 2]]; h2 = [keys[i] for i in perm[len(keys) // 2:]]
    for att in ATT:
        a, b = scores(raw, att, grp, h1), scores(raw, att, grp, h2)
        ids = sorted(set(a) & set(b)); r = np.corrcoef([a[i] for i in ids], [b[i] for i in ids])[0, 1]
        print(f"  {att:22s} n={len(ids):5d}  r_half={r:.3f}  reliability={2*r/(1+r):.3f}")
    print("\nSplit-half reliability of review-based experience scores (>=3 mentions per half not required; >=2)")
    rows = []
    for l in open(revs):
        x = json.loads(l)
        for att in ["cleanliness", "spaciousness", "brightness", "furnishing_condition"]:
            v = x["res"].get(att)
            if v in (-1, 0, 1): rows.append((x["listing_id"], att, v, rng.integers(2)))
    e = pd.DataFrame(rows, columns=["id", "att", "v", "h"])
    for att in ["cleanliness", "spaciousness", "brightness", "furnishing_condition"]:
        g = e[e.att == att].groupby(["id", "h"]).v.agg(["mean", "count"]).unstack("h")
        ok = g[(g[("count", 0)] >= 2) & (g[("count", 1)] >= 2)]
        if len(ok) > 20:
            r = np.corrcoef(ok[("mean", 0)], ok[("mean", 1)])[0, 1]; print(f"  {att:22s} n={len(ok):5d}  r_half={r:.3f}  reliability={2*r/(1+r):.3f}")
        else: print(f"  {att:22s} n={len(ok)} (too few)")

if __name__ == "__main__":
    main(*sys.argv[1:4])
