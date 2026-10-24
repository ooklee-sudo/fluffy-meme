"""Feasibility pilot on AIDev v5 (AIDev-pop): per-agent PR outcomes and review effort.

Downloads pull_request, pr_reviews, pr_review_comments, pr_commits (~1.2 GB) into data/aidev/.
"""
import pathlib

import pandas as pd
from huggingface_hub import hf_hub_download

D = pathlib.Path(__file__).parent / "data" / "aidev"
REPO = "hao-li/AIDev"
REV = "v5"


def get(name, columns=None):
    p = hf_hub_download(REPO, f"{name}.parquet", repo_type="dataset", revision=REV, local_dir=D)
    return pd.read_parquet(p, columns=columns)


def main():
    pr = get("pull_request", ["id", "agent", "state", "created_at", "closed_at", "merged_at", "repo_id"])
    rv = get("pr_reviews", ["id", "pr_id", "pull_request_review_id", "user_type", "state", "submitted_at"])
    rc = get("pr_review_comments", ["id", "pull_request_review_id", "user_type", "in_reply_to_id"])
    cm = get("pr_commits", ["sha", "pr_id"])
    print("user_type values (reviews):", rv.user_type.value_counts(dropna=False).to_dict())
    print("review states:", rv.state.value_counts(dropna=False).to_dict())

    pr["merged"] = pr.merged_at.notna()
    pr["t_close_h"] = (pd.to_datetime(pr.closed_at, utc=True, errors="coerce")
                       - pd.to_datetime(pr.created_at, utc=True, errors="coerce")).dt.total_seconds() / 3600
    human = rv[rv.user_type.fillna("").str.lower() != "bot"]
    g = pr.set_index("id")
    g["n_reviews"] = rv.groupby("pr_id").size().reindex(g.index).fillna(0)
    g["n_human_reviews"] = human.groupby("pr_id").size().reindex(g.index).fillna(0)
    g["changes_req"] = (rv[rv.state == "CHANGES_REQUESTED"].groupby("pr_id").size().reindex(g.index).fillna(0) > 0)
    rid2pr = rv.drop_duplicates("pull_request_review_id").set_index("pull_request_review_id").pr_id
    rc["pr_id"] = rc.pull_request_review_id.map(rid2pr)
    hc = rc[rc.user_type.fillna("").str.lower() != "bot"]
    g["n_inline_human"] = hc.groupby("pr_id").size().reindex(g.index).fillna(0)
    g["n_commits"] = cm.groupby("pr_id").size().reindex(g.index).fillna(0)

    agg = g.groupby("agent").agg(
        n_pr=("merged", "size"), n_repo=("repo_id", "nunique"), merge_rate=("merged", "mean"),
        any_human_review=("n_human_reviews", lambda s: (s > 0).mean()),
        mean_human_reviews=("n_human_reviews", "mean"), mean_inline_human=("n_inline_human", "mean"),
        changes_requested=("changes_req", "mean"), mean_commits=("n_commits", "mean"),
        med_close_h=("t_close_h", "median"))
    pd.set_option("display.width", 200)
    print("\nPer-agent (AIDev-pop, v5):\n", agg.round(3).to_string())

    ra = g.groupby("repo_id").agent.nunique()
    print(f"\nrepos: {len(ra):,}; with >=2 agents: {(ra >= 2).sum():,} ({(ra >= 2).mean():.1%}); >=3: {(ra >= 3).sum():,}")
    multi = g[g.repo_id.isin(ra[ra >= 2].index)]
    print("PRs in multi-agent repos:", len(multi), "| per agent:", multi.agent.value_counts().to_dict())
    agg.round(4).to_csv(pathlib.Path(__file__).parent / "results_aidev_pilot_by_agent.csv")
    g.reset_index().to_parquet(D / "pr_features.parquet")


if __name__ == "__main__":
    main()
