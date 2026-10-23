"""Merge the two filled coder sheets into one human label file for run_pipeline.py --human-labels.

- validates every value against the codebook ranges
- reports inter-coder agreement on the overlap rows (Krippendorff alpha / weighted kappa)
- overlap rows: if coders agree -> that value; ordinal disagreement -> rounded mean is NOT used silently:
  rows with any disagreement are written to adjudication.csv and EXCLUDED from human.csv until resolved
  (pass --adjudicated adjudication_resolved.csv with the resolved values to include them)
Usage: python tools/merge_human_labels.py --a coder_A.csv --b coder_B.csv --key sample_key.csv --out-dir labeling
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import prompts, reliability  # noqa: E402

RANGES = {"sentiment": (1, 5), "emotional_intensity": (1, 5), "specificity": (1, 5), "informativeness": (1, 5),
          "argument_balance": (1, 3), "narrative": (0, 1), "explicit_recommendation": (0, 1), "comparison": (0, 1)}
EMOTIONS = {"joy", "anger", "anxiety", "sadness", "surprise", "none"}


def load_sheet(path):
    d = pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")
    d = d[~d["review_id"].str.startswith("#")].copy()
    d["valid"] = d["valid"].str.strip().replace("", "1")
    bad = []
    for f, (lo, hi) in RANGES.items():
        v = pd.to_numeric(d[f].str.strip(), errors="coerce")
        miss = d["valid"].eq("1") & (v.isna() | (v < lo) | (v > hi) | (v % 1 != 0))
        bad += [(r, f) for r in d.loc[miss, "review_id"]]
        d[f] = v
    em = d["dominant_emotion"].str.strip().str.lower()
    bad += [(r, "dominant_emotion") for r in d.loc[d["valid"].eq("1") & ~em.isin(EMOTIONS), "review_id"]]
    d["dominant_emotion"] = em
    d["valid"] = d["valid"].astype(int)
    if bad:
        print(f"[{path}] {len(bad)} missing/invalid cells, e.g. {bad[:5]}")
        sys.exit(1)
    return d.set_index("review_id")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True); ap.add_argument("--b", required=True)
    ap.add_argument("--key", required=True); ap.add_argument("--out-dir", required=True)
    ap.add_argument("--adjudicated", help="CSV with the same columns as human.csv for resolved overlap rows")
    a = ap.parse_args()
    out = Path(a.out_dir)
    A, B, key = load_sheet(a.a), load_sheet(a.b), pd.read_csv(a.key)
    cols = prompts.CODED_FIELDS
    ov = key.loc[key["in_overlap"], "review_id"]
    missing = set(ov) - (set(A.index) & set(B.index))
    assert not missing, f"{len(missing)} overlap rows missing from a sheet"

    both_valid = ov[(A.loc[ov, "valid"] == 1).values & (B.loc[ov, "valid"] == 1).values]
    tab = reliability.agreement_table(A.loc[both_valid, cols], B.loc[both_valid, cols])
    tab.to_csv(out / "inter_coder_reliability.csv", index=False)
    print("[inter-coder agreement on overlap]\n", tab.round(3).to_string(index=False))

    single = pd.concat([A.drop(index=ov, errors="ignore"), B.drop(index=ov, errors="ignore")])[cols + ["valid"]]
    agree = (A.loc[ov, cols + ["valid"]] == B.loc[ov, cols + ["valid"]]).all(axis=1)
    resolved = A.loc[ov[agree.values], cols + ["valid"]]
    disagree = ov[~agree.values]
    adj = pd.concat({"coderA": A.loc[disagree, cols + ["valid"]], "coderB": B.loc[disagree, cols + ["valid"]]}, axis=1)
    adj.to_csv(out / "adjudication.csv", encoding="utf-8-sig")
    parts = [single, resolved]
    if a.adjudicated:
        parts.append(pd.read_csv(a.adjudicated).set_index("review_id")[cols + ["valid"]])
    human = pd.concat(parts)
    human = human[~human.index.duplicated(keep="last")]
    human.to_csv(out / "human.csv")
    print(f"[merge] human labels: {len(human)} | overlap agree on all fields: {int(agree.sum())}/{len(ov)} | "
          f"need adjudication: {len(disagree)} (see adjudication.csv)")
    print("NOTE: if unresolved overlap rows are dropped, the labelled set is no longer a pure simple random "
          "sample; resolve them (--adjudicated) before the DSL correction.")


if __name__ == "__main__":
    main()
