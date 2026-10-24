"""Within-Claude-Code comparison across model versions (same workflow, different model).

Model is read from commit trailers ("Co-Authored-By: Claude Opus 4.6"); PR model = most frequent among its commits.
Outcomes come from aidev_pilot.py (data/aidev/pr_features.parquet). Repo fixed effects via within-transformation.
"""
import pathlib
import re

import numpy as np
import pandas as pd
import statsmodels.api as sm

HERE = pathlib.Path(__file__).parent
D = HERE / "data" / "aidev"
TRAILER = re.compile(r"co-authored-by:\s*claude\s+(opus|sonnet|haiku)\s+(\d(?:\.\d)?)", re.I)


def pr_models():
    cm = pd.read_parquet(D / "pr_commits.parquet", columns=["pr_id", "message"])
    cm["model"] = [("%s %s" % (m.group(1).title(), m.group(2)) if (m := TRAILER.search(s if isinstance(s, str) else "")) else None)
                   for s in cm.message]
    cm = cm.dropna(subset=["model"])
    cnt = cm.groupby(["pr_id", "model"]).size().rename("k").reset_index()
    tot = cnt.groupby("pr_id").k.transform("sum")
    top = cnt.loc[cnt.groupby("pr_id").k.idxmax()].copy()
    top["share"] = top.k / tot[top.index]
    top["n_models"] = cnt.groupby("pr_id").model.nunique().reindex(top.pr_id).values
    return top.rename(columns={"pr_id": "id"})[["id", "model", "share", "n_models"]]


def within(df, cols, by):
    return df[cols] - df.groupby(by)[cols].transform("mean")


def main():
    f = pd.read_parquet(D / "pr_features.parquet")
    f = f[f.agent == "Claude_Code"].merge(pr_models(), on="id")
    f = f[f.n_models == 1]  # PRs whose commits all name one model
    f["month"] = pd.to_datetime(f.created_at, utc=True, errors="coerce").dt.strftime("%Y-%m")
    f["any_human_review"] = (f.n_human_reviews > 0).astype(float)
    f["merged"] = f.merged.astype(float)
    f["changes_req"] = f.changes_req.astype(float)
    keep = f.model.value_counts()
    keep = keep[keep >= 500].index
    f = f[f.model.isin(keep)]
    print("Claude Code PRs with identified single model:", len(f))
    print(f.model.value_counts().to_string())
    print("\nmodel x month (PR counts):")
    print(pd.crosstab(f.model, f.month).to_string())
    outs = ["any_human_review", "n_human_reviews", "n_inline_human", "changes_req", "merged", "n_commits"]
    print("\nRaw means by model:")
    print(f.groupby("model")[outs].mean().round(3).to_string())

    ref = "Sonnet 4.5"
    models = [m for m in keep if m != ref]
    f = f.merge(f.groupby("repo_id").model.nunique().rename("nm"), on="repo_id")
    w = f[f.nm >= 2].copy()
    print(f"\nrepos with >=2 models: {w.repo_id.nunique():,}; PRs: {len(w):,}")
    X = pd.get_dummies(w.model)[models].astype(float)
    M = pd.get_dummies(w.month, drop_first=True).astype(float)
    Z = pd.concat([X, M], axis=1)
    Zw = Z - Z.groupby(w.repo_id.values).transform("mean")
    rows = []
    for y in outs:
        yw = w[y] - w.groupby("repo_id")[y].transform("mean")
        r = sm.OLS(yw.values, Zw.values).fit(cov_type="cluster", cov_kwds={"groups": w.repo_id.values})
        for i, m in enumerate(models):
            rows.append({"outcome": y, "model": m, "vs": ref, "coef": r.params[i], "se": r.bse[i],
                         "p": r.pvalues[i], "mean_ref": w.loc[w.model == ref, y].mean()})
    out = pd.DataFrame(rows)
    pd.set_option("display.width", 200)
    print("\nRepo + month fixed effects (LPM/OLS, cluster by repo):")
    print(out.round(4).to_string(index=False))
    out.round(5).to_csv(HERE / "results_aidev_versions_fe.csv", index=False)


if __name__ == "__main__":
    main()
