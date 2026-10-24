"""Event study around the Claude Opus 4.5 -> 4.6 switch among Claude Code PRs (AIDev v5, AIDev-pop).

Idea: the default model changes for many users at once, so a before/after comparison within the same repos
is less exposed to users choosing a model per task. Reduced form (ITT): all Claude Code PRs, not only those whose
model is identified. First stage: share of identified PRs that name Opus 4.6.
"""
import pathlib

import numpy as np
import pandas as pd
import statsmodels.api as sm

from aidev_versions import pr_models

HERE = pathlib.Path(__file__).parent
D = HERE / "data" / "aidev"
W = 21  # days per window
OUTS = ["any_human_review", "n_human_reviews", "n_inline_human", "changes_req", "merged", "n_commits"]


def load():
    f = pd.read_parquet(D / "pr_features.parquet")
    f = f[f.agent == "Claude_Code"].merge(pr_models(), on="id", how="left")
    f["date"] = pd.to_datetime(f.created_at, utc=True, errors="coerce").dt.tz_localize(None).dt.normalize()
    f = f.dropna(subset=["date"])
    f["any_human_review"] = (f.n_human_reviews > 0).astype(float)
    for c in ("merged", "changes_req"):
        f[c] = f[c].astype(float)
    return f


def estimate(f, t0, label):
    pre = f[(f.date >= t0 - pd.Timedelta(days=W)) & (f.date < t0)]
    post = f[(f.date >= t0) & (f.date < t0 + pd.Timedelta(days=W))]
    both = set(pre.repo_id) & set(post.repo_id)
    w = pd.concat([pre.assign(post=0.0), post.assign(post=1.0)])
    w = w[w.repo_id.isin(both)]
    rows = []
    for y in OUTS:
        yw = w[y] - w.groupby("repo_id")[y].transform("mean")
        xw = w.post - w.groupby("repo_id").post.transform("mean")
        r = sm.OLS(yw.values, xw.values).fit(cov_type="cluster", cov_kwds={"groups": w.repo_id.values})
        rows.append({"window": label, "t0": t0.date(), "outcome": y, "coef": r.params[0], "se": r.bse[0],
                     "p": r.pvalues[0], "pre_mean": w.loc[w.post == 0, y].mean(), "n_pr": len(w), "n_repo": len(both)})
    return rows


def main():
    f = load()
    ident = f.dropna(subset=["model"])
    daily = pd.DataFrame({
        "n_pr": f.groupby("date").size(),
        "ident_share": f.groupby("date").model.apply(lambda s: s.notna().mean()),
        "opus46_of_ident": ident.groupby("date").model.apply(lambda s: (s == "Opus 4.6").mean()),
        "n_ident": ident.groupby("date").size()}).dropna(subset=["n_ident"])
    lo, hi = pd.Timestamp("2026-01-26"), pd.Timestamp("2026-02-20")
    print("Daily around the switch:\n", daily.loc[lo:hi].round(3).to_string())
    big = ident[(ident.model == "Opus 4.6")].groupby("date").size()
    t0 = big[big >= 50].index.min()
    print(f"\nt0 = first day with >=50 identified Opus 4.6 PRs: {t0.date()}")

    rows = estimate(f, t0, "TRUE")
    for shift in (-42, -21, 21):
        rows += estimate(f, t0 + pd.Timedelta(days=shift), f"placebo{shift:+d}d")
    out = pd.DataFrame(rows)
    pd.set_option("display.width", 220)
    print("\nRepo fixed effects, post vs pre (%d-day windows), cluster by repo:" % W)
    print(out.round(4).to_string(index=False))
    out.round(5).to_csv(HERE / "results_aidev_event_study.csv", index=False)

    pre = f[(f.date >= t0 - pd.Timedelta(days=W)) & (f.date < t0)]
    post = f[(f.date >= t0) & (f.date < t0 + pd.Timedelta(days=W))]
    print("\nFirst stage (identified PRs): Opus 4.6 share pre = %.3f, post = %.3f" % (
        (pre.model == "Opus 4.6").sum() / max(pre.model.notna().sum(), 1),
        (post.model == "Opus 4.6").sum() / max(post.model.notna().sum(), 1)))
    print("Identification rate pre = %.3f, post = %.3f" % (pre.model.notna().mean(), post.model.notna().mean()))


if __name__ == "__main__":
    main()
