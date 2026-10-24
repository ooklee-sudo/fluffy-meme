"""Sample Amazon Reviews 2023 (McAuley Lab; cite Hou et al. 2024 per the dataset README) via HTTP range reads.

The raw category files are huge and sorted by user_id, so a random byte window holds all reviews of the users
fully inside it. For each category we read random windows, drop the first/last (possibly cut) user, compute
`author_reviews` = that user's number of reviews in the category file (exact for the kept users), then keep at
most --max-per-user random reviews per user so heavy reviewers do not dominate. Sampling is by byte window, i.e.
size-biased toward prolific reviewers and clustered by user: use cluster-robust SEs by user (group_id=user_id)
and treat it as a test sample, not a probability sample of Amazon.
Raw text must not be redistributed; write data outside the repo (--out-dir)."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests

URL = "https://huggingface.co/datasets/McAuley-Lab/Amazon-Reviews-2023/resolve/main/raw/review_categories/{}.jsonl"
SIZES_MB = {"Grocery_and_Gourmet_Food": 5974, "Electronics": 22616, "Video_Games": 2683, "Software": 1869,
            "Musical_Instruments": 1558, "Movies_and_TV": 8391, "Toys_and_Games": 7316, "Pet_Supplies": 8351}
GOODS = {"Grocery_and_Gourmet_Food": "experience", "Movies_and_TV": "experience", "Video_Games": "experience",
         "Electronics": "search", "Software": "search", "Musical_Instruments": "search", "Toys_and_Games": "search",
         "Pet_Supplies": "search"}


def window(cat, size_bytes, chunk, rng):
    off = int(rng.integers(0, size_bytes - chunk))
    r = requests.get(URL.format(cat), headers={"Range": f"bytes={off}-{off + chunk}"}, timeout=90)
    r.raise_for_status()
    lines = r.content.decode("utf8", "ignore").split("\n")[1:-1]  # drop cut first/last line
    rows = []
    for l in lines:
        try:
            rows.append(json.loads(l))
        except json.JSONDecodeError:
            pass
    if not rows:
        return []
    users = [x["user_id"] for x in rows]
    first, last = users[0], users[-1]
    return [x for x in rows if x["user_id"] not in (first, last)]  # edge users may be incomplete


def sample_category(cat, n, chunk, max_per_user, seed):
    rng = np.random.default_rng(seed)
    size = SIZES_MB[cat] * 1_000_000
    got, seen_users = [], set()
    while sum(min(c, max_per_user) for c in pd.Series([x["user_id"] for x in got]).value_counts()) < n * 1.1:
        for x in window(cat, size, chunk, rng):
            if x["user_id"] in seen_users:
                continue
            got.append(x)
        seen_users |= {x["user_id"] for x in got}
    df = pd.DataFrame(got)
    df["author_reviews"] = df.groupby("user_id")["user_id"].transform("size")
    df = df.sample(frac=1, random_state=seed).groupby("user_id").head(max_per_user)  # random cap per user
    df["text"] = (df["title"].fillna("") + ". " + df["text"].fillna("")).str.strip(". ").str.strip()
    df = df[df["text"].str.len() > 0]
    df["has_image"] = df["images"].map(lambda v: int(v is not None and len(v) > 0))
    df["parent_asin"] = df["parent_asin"].astype(str)
    df["category"] = GOODS[cat]
    df["product_category"] = cat
    return df.sample(min(n, len(df)), random_state=seed).drop(columns=["images"], errors="ignore")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--categories", nargs="+", default=["Grocery_and_Gourmet_Food", "Electronics"])
    ap.add_argument("--n-per-cat", type=int, default=1000)
    ap.add_argument("--chunk-bytes", type=int, default=200_000)
    ap.add_argument("--max-per-user", type=int, default=5)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    df = pd.concat([sample_category(c, a.n_per_cat, a.chunk_bytes, a.max_per_user, a.seed) for c in a.categories])
    df.to_parquet(out / "amazon_sample.parquet")
    print(df.groupby("category").agg(n=("text", "size"), users=("user_id", "nunique"),
                                     mean_helpful=("helpful_vote", "mean"), zero_share=("helpful_vote", lambda s: (s == 0).mean())))


if __name__ == "__main__":
    main()
