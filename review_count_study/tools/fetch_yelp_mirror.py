"""Fetch a random sample of Yelp reviews + user review counts from an UNOFFICIAL Hugging Face mirror
(yashraizad/yelp-open-dataset-*). For pipeline testing only: Yelp's dataset terms forbid redistribution and
restrict use; get the official files from https://www.yelp.com/dataset for real research.
Mirror caveat: the outcome column is `total_interaction` (assumed useful+funny+cool), not `useful`.
Data is written OUTSIDE the repo (pass --out-dir) and must not be committed."""
import argparse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROWS = "https://datasets-server.huggingface.co/rows"
DS = "yashraizad/yelp-open-dataset-reviews"
USERS_URL = "https://huggingface.co/datasets/yashraizad/yelp-open-dataset-users/resolve/main/users.parquet"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--total-rows", type=int, default=6_990_280)
    a = ap.parse_args()
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(a.seed)
    pages = int(np.ceil(a.n * 1.3 / 100))  # oversample, then drop empty texts
    offsets = rng.choice(a.total_rows // 100, pages, replace=False) * 100
    rows = []
    for off in offsets:
        r = requests.get(ROWS, params=dict(dataset=DS, config="default", split="train", offset=int(off), length=100), timeout=60)
        r.raise_for_status()
        rows += [x["row"] for x in r.json()["rows"]]
    rv = pd.DataFrame(rows)
    rv = rv[rv["text"].fillna("").str.strip().ne("")].drop_duplicates("review_id").head(a.n)
    rv.to_parquet(out / "reviews_sample.parquet")
    users_path = out / "users.parquet"
    if not users_path.exists():
        urllib.request.urlretrieve(USERS_URL, users_path)
    us = pd.read_parquet(users_path)
    print("users columns:", list(us.columns)[:12], "rows:", len(us))
    print("reviews:", len(rv), "mean total_interaction:", rv["total_interaction"].mean())


if __name__ == "__main__":
    main()
