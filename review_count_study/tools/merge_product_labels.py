"""Merge two coders' product labels; report inter-coder agreement and LLM accuracy against human consensus.

Steps: (1) validate both sheets; (2) inter-coder kappa/agreement per dimension; (3) write disagreements to
product_adjudication.csv for discussion; (4) once a resolved file (item_id, good_type, motive) is supplied with
--consensus, compare the LLM labels in the private key with the human consensus (accuracy, kappa, confusion).
Usage: python tools/merge_product_labels.py --a product_coder_A.csv --b product_coder_B.csv --key product_sample_key.csv --out-dir product_labeling [--consensus resolved.csv]
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

G, M = {"search", "experience"}, {"hedonic", "utilitarian"}


def load(path):
    d = pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")
    d = d[~d["item_id"].str.startswith("#")].copy()
    for c, ok in (("good_type", G), ("motive", M)):
        d[c] = d[c].str.strip().str.lower()
        bad = d.loc[~d[c].isin(ok), "item_id"].tolist()
        if bad:
            raise SystemExit(f"[{path}] missing/invalid '{c}' for {len(bad)} items, e.g. {bad[:5]}")
    return d.set_index("item_id")


def boot_ci(y1, y2, B=2000, seed=0):
    rng = np.random.default_rng(seed); n = len(y1); ks = []
    for _ in range(B):
        i = rng.integers(0, n, n)
        ks.append(cohen_kappa_score(y1[i], y2[i]))
    return np.nanpercentile(ks, [2.5, 97.5])


def report(name, x, y):
    x, y = np.asarray(x), np.asarray(y)
    lo, hi = boot_ci(x, y)
    print(f"  {name}: agreement {np.mean(x == y):.1%}, kappa {cohen_kappa_score(x, y):.3f} (95% CI {lo:.3f}-{hi:.3f})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True); ap.add_argument("--b", required=True); ap.add_argument("--key", required=True)
    ap.add_argument("--out-dir", required=True); ap.add_argument("--consensus")
    a = ap.parse_args()
    out = Path(a.out_dir)
    A, B, key = load(a.a), load(a.b), pd.read_csv(a.key).set_index("item_id")
    ids = sorted(set(A.index) & set(B.index))
    assert len(ids) == len(key), f"coders cover {len(ids)} of {len(key)} items"
    print(f"[inter-coder agreement, n={len(ids)}]")
    for c in ("good_type", "motive"):
        report(c, A.loc[ids, c], B.loc[ids, c])
    dis = A.loc[ids, ["good_type", "motive"]].join(B.loc[ids, ["good_type", "motive"]], lsuffix="_A", rsuffix="_B")
    dis = dis[(dis.good_type_A != dis.good_type_B) | (dis.motive_A != dis.motive_B)]
    dis.to_csv(out / "product_adjudication.csv")
    print(f"disagreements to resolve: {len(dis)} (product_adjudication.csv; resolved file needs item_id,good_type,motive)")
    if a.consensus:
        cons = pd.read_csv(a.consensus).set_index("item_id")
        agree = A.loc[ids, ["good_type", "motive"]].where((A.loc[ids, ["good_type", "motive"]] == B.loc[ids, ["good_type", "motive"]]))
        gold = agree.copy()
        for c in ("good_type", "motive"):
            gold[c] = gold[c].fillna(cons[c])
        assert gold.notna().all().all(), "consensus file does not cover all disagreements"
        print("[LLM labels versus human consensus]")
        for c, l in (("good_type", "llm_good_type"), ("motive", "llm_motive")):
            report(c, key.loc[ids, l], gold[c])
            print(pd.crosstab(gold[c], key.loc[ids, l], rownames=["human"], colnames=["LLM"]).to_string())
        gold.join(key[["parent_asin"]]).to_csv(out / "product_human_consensus.csv")


if __name__ == "__main__":
    main()
