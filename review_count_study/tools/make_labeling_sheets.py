"""Draw a simple random sample of the analysis rows and write BLIND coding sheets for two human coders.

Sampling must be a simple random sample of the rows used in the regression (needed for the DSL correction,
which assumes a known, constant labelling probability pi = n_label / N). Coders never see LLM codes, stars,
counts or author info. Overlap rows are coded by BOTH coders (inter-coder reliability); the rest are split.

Usage:
  python tools/make_labeling_sheets.py --coded out/reviews_coded.parquet --out-dir labeling --n 400 --overlap 100
Outputs (in --out-dir): coder_A.csv, coder_B.csv (give to coders), sample_key.csv (keep private: sampling record).
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd

FIELDS = ["valid", "sentiment", "emotional_intensity", "specificity", "informativeness", "argument_balance",
          "narrative", "explicit_recommendation", "comparison", "dominant_emotion", "notes"]
HINT = {"valid": "1/0 (0=unreadable/empty)", "sentiment": "1-5", "emotional_intensity": "1-5", "specificity": "1-5",
        "informativeness": "1-5", "argument_balance": "1-3", "narrative": "0/1", "explicit_recommendation": "0/1",
        "comparison": "0/1", "dominant_emotion": "joy|anger|anxiety|sadness|surprise|none"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--coded", required=True, help="reviews_coded.parquet/.csv from run_pipeline (rows actually analysed)")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--overlap", type=int, default=100, help="rows coded by both coders")
    ap.add_argument("--seed", type=int, default=2024)
    a = ap.parse_args()
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(a.coded) if a.coded.endswith(".parquet") else pd.read_csv(a.coded)
    if "error" in df:
        df = df[df["error"].isna()]
    df = df[df.get("valid", True) == True]  # noqa: E712  rows the regression actually uses
    assert a.overlap <= a.n <= len(df), "need overlap <= n <= number of analysed rows"
    rng = np.random.default_rng(a.seed)
    sample = df.iloc[rng.permutation(len(df))[:a.n]]                       # simple random sample
    ids = sample["review_id"].tolist()
    both, rest = ids[:a.overlap], ids[a.overlap:]
    half = len(rest) // 2
    assign = {"A": both + rest[:half], "B": both + rest[half:]}
    text = sample.set_index("review_id")["text"]

    for coder, rids in assign.items():
        order = list(rng.permutation(rids))  # shuffle so overlap rows are not recognisable / ordered
        sheet = pd.DataFrame({"review_id": order, "text": [text[r] for r in order]})
        for f in FIELDS:
            sheet[f] = ""
        hint = pd.DataFrame([{"review_id": "#ALLOWED_VALUES", "text": "(delete this row after reading; see codebook.md)",
                              **HINT, "notes": "free text"}])
        pd.concat([hint, sheet]).to_csv(out / f"coder_{coder}.csv", index=False, encoding="utf-8-sig")

    key = pd.DataFrame({"review_id": ids, "in_overlap": [r in set(both) for r in ids]})
    key["pi"] = a.n / len(df)
    key["N_analysed"] = len(df)
    key.to_csv(out / "sample_key.csv", index=False)
    print(f"N={len(df)} sample={a.n} overlap={a.overlap} pi={a.n/len(df):.4f}; "
          f"coder A rows={len(assign['A'])}, coder B rows={len(assign['B'])}")


if __name__ == "__main__":
    main()
