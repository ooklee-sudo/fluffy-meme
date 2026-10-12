"""Diagnose the hot-fix rule against the figures in manuscript Section 5.2.
    python diag_hotfix.py data/releases.csv
Manuscript: 60% of 2,659 releases raise only the patch component of the previous release;
71% of those appear within 7 days (median 1 day); 43% of all releases are hot-fixes.
"""
import re, sys
import pandas as pd

R = pd.read_csv(sys.argv[1], parse_dates=["published_at"]).sort_values(["repo", "published_at"], kind="stable")
V = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?")

n = unparsable = firsts = changed_not_up = 0
raised_days, examples = [], []
prev_repo = prev_v = prev_t = None
for repo, tag, ts in zip(R.repo, R.tag, R.published_at):
    n += 1
    m = V.search(str(tag))
    v = tuple(int(g) if g else 0 for g in m.groups()) if m else None
    if v is None:
        unparsable += 1
        if len(examples) < 8:
            examples.append(tag)
    if repo != prev_repo:
        firsts += 1
    elif v is not None and prev_v is not None and v[:2] == prev_v[:2]:
        if v[2] > prev_v[2]:
            raised_days.append((ts - prev_t).days)
        elif v[2] != prev_v[2]:
            changed_not_up += 1
    prev_repo, prev_v, prev_t = repo, v, ts

s = pd.Series(raised_days)
print("releases", n, "| tag not parseable:", unparsable, "| first release of a repo:", firsts)
print("patch raised only        ", round(len(s) / n, 3), "(manuscript 0.60)")
print("patch changed but lower  ", changed_not_up)
print("  of 'raised': within 7d ", round((s <= 7).mean(), 3), "(manuscript 0.71); median days", s.median())
print("hot-fix = raised & <=7d  ", round((s <= 7).sum() / n, 3))
print("hot-fix as in releases.csv", round(R.is_hotfix.mean(), 3), "(manuscript 0.43)")
print("unparseable tag examples:", examples)
