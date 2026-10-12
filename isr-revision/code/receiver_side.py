"""Receiver-side test of the signaling argument (Section 2.4).

Question: do users reward release cadence (adoption rises after periods of frequent
releases), and do they reward releases that follow bug surges any more than other releases?
If adoption responds to cadence but not to its bug-responsive component, receivers treat
cadence as a signal without discriminating on the quality it is read as indicating; together
with Sections 5.1-5.3, both halves of the signaling argument are then tested.

Inputs (--data): weekly_panel.csv, releases.csv, adoption_weekly.csv (see make_synthetic.py;
SQL for downloads and stars is in sql/). Repositories with no PyPI artifact have missing
downloads and drop from the downloads models only.

Variables (repository-week t; W = --window weeks):
  y_dl     log mean weekly downloads in t+1..t+4 minus log mean in t-3..t
  y_st     log(1+stars in t+1..t+4) minus log(1+stars in t-3..t)
  rel      releases in t-W+1..t
  bugpre   releases in t-W+1..t that follow a week whose bug share exceeded the repository median
  hot      hot-fix releases in t-W+1..t
  iss      log(1 + issues in t-W+1..t)
  lag_y    outcome measured four weeks earlier
All regressors standardized over the pooled sample. Repository and week fixed effects;
CR1 standard errors clustered by repository; wild cluster restricted bootstrap p-values
(Webb weights). With rel in the model, the coefficient on bugpre (hot) is the extra
response to a bug-preceded (hot-fix) release over any other release.

Caveats: adoption and releases are jointly driven by project momentum; lag_y and the issue
control absorb part of it. Overlapping windows induce serial correlation, which repository
clustering allows for. Download counts include mirrors and CI.
"""
import argparse
import os
import numpy as np
import pandas as pd
from stats_utils import twfe_ols, wild_cluster_p

ap = argparse.ArgumentParser()
ap.add_argument("--data", default="data")
ap.add_argument("--out", default="output")
ap.add_argument("--window", type=int, default=8)
ap.add_argument("--B", type=int, default=999)
ap.add_argument("--no-downloads", default="", help="comma-separated repositories whose PyPI downloads are set to missing (they enter only the star models)")
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
W = a.window

P = pd.read_csv(os.path.join(a.data, "weekly_panel.csv"), parse_dates=["week"])
A = pd.read_csv(os.path.join(a.data, "adoption_weekly.csv"), parse_dates=["week"])
R = pd.read_csv(os.path.join(a.data, "releases.csv"))
R["week"] = (pd.to_datetime(R.published_at, utc=True).dt.tz_localize(None)
             .dt.to_period("W-SUN").dt.start_time)
hot_w = R[R.is_hotfix == 1].groupby(["repo", "week"]).size().rename("n_hot")
D = (P.merge(A, on=["repo", "week"], how="left")
       .merge(hot_w, on=["repo", "week"], how="left")
       .fillna({"n_hot": 0}).sort_values(["repo", "week"]))
for r in [x.strip() for x in a.no_downloads.split(",") if x.strip()]:
    if r not in set(D.repo):
        raise SystemExit(f"--no-downloads: unknown repository {r}")
    D.loc[D.repo == r, "downloads"] = np.nan


def build(g):
    g = g.copy()
    share = g.bugs / g.issues.replace(0, np.nan)
    hi_bug_prev = (share > share.median()).shift(1).fillna(False).astype(int)
    g["rel"] = g.release.rolling(W, min_periods=W).sum()
    g["bugpre"] = (g.release * hi_bug_prev).rolling(W, min_periods=W).sum()
    g["hot"] = g.n_hot.rolling(W, min_periods=W).sum()
    g["iss"] = np.log1p(g.issues.rolling(W, min_periods=W).sum())
    fwd = lambda s: s.shift(-1).rolling(4).mean().shift(-3)      # mean over t+1..t+4
    back = lambda s: s.rolling(4).mean()                          # mean over t-3..t
    g["y_dl"] = np.log(fwd(g.downloads)) - np.log(back(g.downloads))
    g["y_st"] = np.log1p(4 * fwd(g.stars_new)) - np.log1p(4 * back(g.stars_new))
    g["lag_y_dl"] = g.y_dl.shift(4)
    g["lag_y_st"] = g.y_st.shift(4)
    return g


D = pd.concat([build(g) for _, g in D.groupby("repo", sort=False)], ignore_index=True)
for c in ["rel", "bugpre", "hot", "iss"]:
    D[c] = (D[c] - D[c].mean()) / D[c].std()

models = {"M1 cadence": ["rel", "iss"],
          "M2 cadence + bug-preceded": ["rel", "bugpre", "iss"],
          "M3 cadence + hot-fix": ["rel", "hot", "iss"]}
rows = []
for y in ["y_dl", "y_st"]:
    for mname, xs in models.items():
        cols = xs + [f"lag_{y}"]
        d = D.dropna(subset=[y] + cols)
        d = d[np.isfinite(d[y])]
        if d.repo.nunique() < 5:
            continue
        X = d[cols].to_numpy(float)
        fit = twfe_ols(d[y].to_numpy(float), X, [d.repo.to_numpy(), d.week.to_numpy()],
                       d.repo.to_numpy(), names=cols)
        for j, nm in enumerate(cols):
            if nm.startswith("lag_"):
                continue
            p = wild_cluster_p(d[y].to_numpy(float), X, [d.repo.to_numpy(), d.week.to_numpy()],
                               d.repo.to_numpy(), j, B=a.B)
            rows.append(dict(outcome=y, model=mname, term=nm, coef=fit["coef"][j], se=fit["se"][j],
                             wcr_p=p, n=len(d), clusters=d.repo.nunique()))
out = pd.DataFrame(rows)
out.to_csv(f"{a.out}/receiver_side_results.csv", index=False)
print(out.round(4).to_string(index=False))
