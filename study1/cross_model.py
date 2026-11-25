"""Cross-model agreement of Bradley-Terry photo scores on the 2,000-listing subset.
Usage: python cross_model.py WORKDIR PAIRS_PRIMARY PAIRS_SECOND SUBSET_CSV"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, ".")
from reliability import load_pairs, scores
from analyze_study1 import ATT

def main(work, p1, p2, sub_csv):
    s = pd.read_csv(f"{work}/sample.csv"); grp = (s.city + "|" + s.room_type).set_axis(s.id).to_dict()
    sub = set(pd.read_csv(sub_csv).id)
    r1, r2 = load_pairs(p1), load_pairs(p2)
    # primary-model scores for the subset: use primary pairs among subset listings only (same sparse design) and all primary pairs
    k1 = [k for k in r1 if k[0] in sub and k[1] in sub]
    print("subset pairs: primary-within-subset", len(k1), " second model", len(r2))
    for att in ATT:
        full = scores(r1, att, grp, list(r1))             # primary model, full graph
        sec = scores(r2, att, grp, list(r2))               # second model, subset graph
        ids = sorted(set(full) & set(sec) & sub)
        r = np.corrcoef([full[i] for i in ids], [sec[i] for i in ids])[0, 1]
        # attenuation ceiling: second-model split-half reliability
        keys = list(r2); rng = np.random.default_rng(5); p = rng.permutation(len(keys))
        a = scores(r2, att, grp, [keys[i] for i in p[: len(p)//2]]); b = scores(r2, att, grp, [keys[i] for i in p[len(p)//2:]])
        j = sorted(set(a) & set(b)); rh = np.corrcoef([a[i] for i in j], [b[i] for i in j])[0, 1]
        print(f"  {att:22s} n={len(ids):5d}  r(primary, second)={r:.3f}   second-model split-half reliability={2*rh/(1+rh):.3f}")
    # raw choice agreement at pair level
    for att in ATT:
        agree = n = 0
        for k, v in r2.items():
            if k in r1:
                f = lambda x: 1.0 if (x["AB"].get(att) == "A" and x["BA"].get(att) == "B") else (0.0 if (x["AB"].get(att) == "B" and x["BA"].get(att) == "A") else 0.5)
                a, b = f(v), f(r1[k])
                if a != 0.5 and b != 0.5: n += 1; agree += (a == b)
        if n: print(f"  pair-level agreement (both decisive) {att:22s} {agree}/{n} = {agree/n:.3f}")

if __name__ == "__main__":
    main(*sys.argv[1:5])
