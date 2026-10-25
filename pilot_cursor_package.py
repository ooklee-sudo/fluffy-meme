"""Pilot: adoption timing and filter pass rates from the public Cursor replication package.

Data: He et al. (MSR 2026) replication package, Zenodo 10.5281/zenodo.18368662 (CC-BY-4.0).
Usage: python3 -I pilot_cursor_package.py <path to CursorStudy/data>
Reads only ts_repos_monthly.csv and matching.csv; never executes code from the package.
"""
import sys
import pandas as pd

data = sys.argv[1]
ts = pd.read_csv(f"{data}/ts_repos_monthly.csv", low_memory=False)
ts["cursor"] = ts.cursor.astype(str).str.lower().eq("true")
first = ts[ts.cursor].groupby("repo_name").month.min().rename("adopt")
tr = ts.join(first, on="repo_name")
tr = tr[tr.adopt.notna()].copy()
tr["pre"] = tr.month < tr.adopt

print("first-adoption month distribution (treated repos):")
print(first.value_counts().sort_index().to_string())

agg = tr.groupby("repo_name").apply(lambda d: pd.Series({
    "pre_m": d[d.pre].month.nunique(), "post_m": d[~d.pre].month.nunique(),
    "pre_issues": d[d.pre].issues.sum()}), include_groups=False)
print(f"\ntreated repos: {len(agg)}")
print("pass rate = share of treated repos with >=k pre and post months and >=n pre-adoption issues")
for k in (3, 6, 12):
    for n in (0, 5, 10, 20):
        ok = (agg.pre_m >= k) & (agg.post_m >= k) & (agg.pre_issues >= n)
        print(f"  k={k:2d} n={n:2d}: {ok.sum():4d} ({ok.mean():.0%})")

m = pd.read_csv(f"{data}/matching.csv", usecols=["repo_name", "group", "n_releases"])
t = m[m.group == "treatment"].drop_duplicates("repo_name")
print(f"\nreleases (matching snapshot), treated n={len(t)}: "
      f">=1 {(t.n_releases >= 1).mean():.0%}, >=3 {(t.n_releases >= 3).mean():.0%}, >=5 {(t.n_releases >= 5).mean():.0%}")

# Repos passing the main filter (k=6 months pre/post, >=10 pre-adoption issues) for label collection
ok = (agg.pre_m >= 6) & (agg.post_m >= 6) & (agg.pre_issues >= 10)
out = agg[ok].join(first).reset_index()[["repo_name", "adopt", "pre_m", "post_m", "pre_issues"]]
out.to_csv("pilot_pass_repos.csv", index=False)
print(f"\nwrote pilot_pass_repos.csv ({len(out)} repos)")
