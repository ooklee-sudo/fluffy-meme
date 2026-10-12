"""Diagnose the hot-fix rule against the figures in manuscript Section 5.2.
    python diag_hotfix.py data/releases.csv
Manuscript: 60% of 2,659 releases raise only the patch component of the previous release;
71% of those appear within 7 days (median 1 day); 43% of all releases are hot-fixes.
"""
import re, sys
import pandas as pd

R = pd.read_csv(sys.argv[1], parse_dates=["published_at"]).sort_values(["repo", "published_at"])
V = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?")

def ver(t):
    m = V.search(str(t))
    return tuple(int(g) if g else 0 for g in m.groups()) if m else None

R["v"] = R.tag.map(ver)
R["pv"] = R.groupby("repo").v.shift()
R["pt"] = R.groupby("repo").published_at.shift()
R["days"] = (R.published_at - R.pt).dt.days
ok = R.v.notna() & R.pv.notna()
same_mm = ok & R.apply(lambda r: r.v is not None and r.pv is not None and r.v[:2] == r.pv[:2], axis=1)
up = same_mm & R.apply(lambda r: r.v is not None and r.pv is not None and r.v[2] > r.pv[2], axis=1)
ne = same_mm & ~up & R.apply(lambda r: r.v is not None and r.pv is not None and r.v[2] != r.pv[2], axis=1)
print("releases", len(R), "| tag not parseable:", int(R.v.isna().sum()), "| first release of repo:", int(R.pv.isna().sum()))
print("patch raised only      ", round(up.mean(), 3), "(manuscript 0.60)")
print("patch changed, not up  ", int(ne.sum()))
print("  of 'raised': within 7d", round((R.days[up] <= 7).mean(), 3), "(manuscript 0.71), median days", R.days[up].median())
print("hot-fix = raised & <=7d ", round((up & (R.days <= 7)).mean(), 3))
print("hot-fix as in releases.csv", round(R.is_hotfix.mean(), 3), "(manuscript 0.43)")
print("tags not parseable, examples:", list(R.tag[R.v.isna()].head(8)))
