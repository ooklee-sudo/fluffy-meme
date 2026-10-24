"""Blind human-coding sheets for the product-level goods classification (search/experience, hedonic/utilitarian).

Draws a simple random sample of the products that were classified by the LLM and writes two sheets with the SAME
products in different random order (both coders code all of them -> inter-coder agreement, then consensus labels
as the gold standard for the LLM labels). Coders see the same listing information the LLM saw (title, main
category, category path, features, description) but no LLM labels and no review information.
Usage: python tools/make_product_sheets.py --labels product_labels_*.csv --meta-dir meta --out-dir product_labeling --n 200
"""
import argparse
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd

COLS = ["good_type", "motive", "confidence", "notes"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", required=True, help="LLM product labels CSV (defines the sampling frame)")
    ap.add_argument("--meta-dir", required=True); ap.add_argument("--out-dir", required=True)
    ap.add_argument("--n", type=int, default=200); ap.add_argument("--seed", type=int, default=2024)
    a = ap.parse_args()
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    lab = pd.read_csv(a.labels).dropna(subset=["good_type", "motive"]).drop_duplicates("parent_asin")
    rows = []
    for f in glob.glob(f"{a.meta_dir}/meta_*.jsonl"):
        rows += [json.loads(l) for l in open(f)]
    meta = pd.DataFrame(rows).drop_duplicates("parent_asin")
    frame = lab.merge(meta, on="parent_asin", how="inner")
    assert a.n <= len(frame)
    rng = np.random.default_rng(a.seed)
    sample = frame.iloc[rng.permutation(len(frame))[:a.n]].reset_index(drop=True)
    sample["item_id"] = [f"P{i+1:03d}" for i in range(len(sample))]
    view = pd.DataFrame({
        "item_id": sample["item_id"], "title": sample["title"].fillna("").str.slice(0, 300),
        "main_category": sample["main_category"].fillna(""),
        "category_path": sample["categories"].map(lambda c: " > ".join([x for x in (c or []) if x][-4:])),
        "features": sample["features"].map(lambda c: " | ".join((c or [])[:3])).str.slice(0, 400),
        "description": sample["description"].fillna("").str.slice(0, 400)})
    hint = {"item_id": "#ALLOWED_VALUES", "title": "(delete this row after reading; see the coder guide)",
            "good_type": "search|experience", "motive": "hedonic|utilitarian", "confidence": "1-3 (1=guess, 3=sure)",
            "notes": "free text"}
    for coder in ("A", "B"):
        sheet = view.sample(frac=1, random_state=int(rng.integers(1e9))).reset_index(drop=True)
        for c in COLS:
            sheet[c] = ""
        order = ["item_id", "title", "main_category", "category_path", "features", "description"] + COLS
        pd.concat([pd.DataFrame([hint]), sheet]).fillna("")[order].to_csv(out / f"product_coder_{coder}.csv", index=False, encoding="utf-8-sig")
    sample[["item_id", "parent_asin", "good_type", "motive"]].rename(
        columns={"good_type": "llm_good_type", "motive": "llm_motive"}).to_csv(out / "product_sample_key.csv", index=False)
    print(f"sampled {len(sample)} of {len(frame)} products -> coder_A/B sheets (same items, different order) + private key")


if __name__ == "__main__":
    main()
