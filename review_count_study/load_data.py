"""Data loading: Yelp Open Dataset, Amazon Reviews 2023 (McAuley Lab), and a synthetic demo.

All loaders return a DataFrame with the common columns:
  review_id, text, count (response count), stars, days_since_post, author_reviews, group_id, category
"""
import json
import numpy as np
import pandas as pd

COMMON = ["review_id", "text", "count", "stars", "days_since_post", "author_reviews", "group_id", "category"]


def _read_jsonl(path, n_max=None):
    rows = []
    with open(path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if n_max and i >= n_max:
                break
            rows.append(json.loads(line))
    return pd.DataFrame(rows)


def load_yelp(review_path, user_path, n_max=500_000):
    """yelp_academic_dataset_review.json + yelp_academic_dataset_user.json. count = `useful` votes.
    Snapshot date = max review date, so days_since_post measures exposure time."""
    rv = _read_jsonl(review_path, n_max)
    us = _read_jsonl(user_path)[["user_id", "review_count"]].rename(columns={"review_count": "author_reviews"})
    df = rv.merge(us, on="user_id", how="left")
    df["date"] = pd.to_datetime(df["date"])
    df["days_since_post"] = (df["date"].max() - df["date"]).dt.days
    df = df.rename(columns={"useful": "count", "business_id": "group_id"})
    df["category"] = "restaurant_or_service"  # join business.json categories if H3 is tested
    return df.assign(author_reviews=df["author_reviews"].fillna(1))[COMMON]


def load_yelp_mirror(review_path, user_path):
    """Output of tools/fetch_yelp_mirror.py (unofficial mirror). count = total_interaction (assumed
    useful+funny+cool, NOT `useful` alone). No business categories -> H3 heterogeneity is skipped."""
    rv = pd.read_parquet(review_path)
    us = pd.read_parquet(user_path, columns=["user_id", "review_count"]).rename(columns={"review_count": "author_reviews"})
    df = rv.merge(us, on="user_id", how="left")
    df["date"] = pd.to_datetime(df["date"])
    df["days_since_post"] = (df["date"].max() - df["date"]).dt.days
    df = df.rename(columns={"total_interaction": "count", "business_id": "group_id"})
    df["category"] = "restaurant_or_service"
    return df.assign(author_reviews=df["author_reviews"].fillna(1))[COMMON]


def load_amazon_sample(path, group="user_id"):
    """Output of tools/fetch_amazon_sample.py. count = helpful_vote; author_reviews = reviews by that user in
    the category file; group_id defaults to user_id (the sampling cluster)."""
    d = pd.read_parquet(path)
    d["date"] = pd.to_datetime(d["timestamp"], unit="ms")
    d["days_since_post"] = (d["date"].max() - d["date"]).dt.days
    d["review_id"] = d["user_id"] + "|" + d["asin"] + "|" + d["timestamp"].astype(str)
    d = d.rename(columns={"helpful_vote": "count", "rating": "stars"})
    d["group_id"] = d[group]
    return d[COMMON]


def load_amazon(review_path, category, n_max=500_000):
    """Amazon Reviews 2023 JSONL (per category). count = helpful_vote. Product = parent_asin.
    Author review counts are not provided; compute from the file if user_id repeats."""
    rv = _read_jsonl(review_path, n_max)
    rv["date"] = pd.to_datetime(rv["timestamp"], unit="ms")
    rv["days_since_post"] = (rv["date"].max() - rv["date"]).dt.days
    rv["text"] = (rv["title"].fillna("") + ". " + rv["text"].fillna("")).str.strip()
    rv["author_reviews"] = rv.groupby("user_id")["user_id"].transform("size")
    rv["review_id"] = rv.index.astype(str)
    rv = rv.rename(columns={"helpful_vote": "count", "rating": "stars", "parent_asin": "group_id"})
    rv["category"] = category
    return rv[COMMON]


def stratified_sample(df, n, by=("category",), seed=0):
    """Equal-allocation sample across strata (falls back to all rows of small strata)."""
    rng = np.random.default_rng(seed)
    groups = list(df.groupby(list(by)))
    per = max(1, n // len(groups))
    parts = [g.sample(min(per, len(g)), random_state=int(rng.integers(1e9))) for _, g in groups]
    return pd.concat(parts).reset_index(drop=True)


# ---------------------------------------------------------------- synthetic demo
_POS = ["Loved it, truly great.", "Everything was excellent.", "Really happy with this."]
_NEG = ["Awful experience, very disappointed.", "Everything was bad.", "Not happy at all."]
_SPEC = ["I ordered the truffle gnocchi for $24 at 7pm and it came in 10 minutes.",
         "The battery lasted 9 hours at 50% brightness according to my test.",
         "Room 304 had a 2-inch gap under the door and the wifi was 5 Mbps."]
_BOTH = ["On the plus side the staff was friendly, but on the downside it was noisy and overpriced."]
_EMO = ["ABSOLUTELY!!! I can't even describe it!!!"]
_REC = ["You should definitely go. I recommend it to everyone."]
_NARR = ["First we waited, then we ordered, and afterwards we left."]
_CMP = ["Compared to the other place we tried last year, this was different."]


def make_demo(n=3000, seed=0, n_groups=60):
    """Synthetic reviews with known data-generating process (true IRRs) for pipeline testing.
    True log-rate: +0.35*specific +0.25*both_sided +0.20*extreme_sentiment +0.4*emotional_intensity(0/1) ...
    Counts are Negative Binomial (overdispersed), exposure = days_since_post."""
    rng = np.random.default_rng(seed)
    pos = rng.random(n) < 0.6
    spec = rng.random(n) < 0.4
    both = rng.random(n) < 0.2
    emo = rng.random(n) < 0.25
    rec = rng.random(n) < 0.3
    narr = rng.random(n) < 0.3
    cmp_ = rng.random(n) < 0.15
    texts = []
    for i in range(n):
        parts = [rng.choice(_POS if pos[i] else _NEG)]
        for flag, pool in ((spec[i], _SPEC), (both[i], _BOTH), (emo[i], _EMO),
                           (rec[i], _REC), (narr[i], _NARR), (cmp_[i], _CMP)):
            if flag:
                parts.append(rng.choice(pool))
        texts.append(" ".join(parts))
    days = rng.integers(10, 2000, n)
    stars = np.where(pos, rng.integers(4, 6, n), rng.integers(1, 3, n))
    author = rng.integers(1, 300, n)
    grp = rng.integers(0, n_groups, n)
    grp_eff = rng.normal(0, 0.3, n_groups)[grp]
    eta = (-5.0 + 0.35 * spec + 0.25 * both + 0.40 * emo + 0.15 * rec - 0.10 * pos
           + 0.003 * 0 + 0.2 * np.log(author) + grp_eff + np.log(days))
    mu = np.exp(eta)
    theta = 2.0
    cnt = rng.poisson(rng.gamma(theta, mu / theta))
    return pd.DataFrame(dict(review_id=[f"d{i}" for i in range(n)], text=texts, count=cnt, stars=stars,
                             days_since_post=days, author_reviews=author, group_id=grp.astype(str),
                             category=np.where(grp % 2 == 0, "experience", "search")))
