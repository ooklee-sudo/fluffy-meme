"""Export the weekly panel that analyze.py builds, in the format spec_c.py expects.

Usage (inside the kit folder, after collect.py):
    python export_panel.py --end-week 2026-10-05          # writes panel.csv
    python spec_c.py panel.csv --boot 999
Columns: repo, week, issues, bugs, release (any release that week), age (weeks since the last release).
"""
import argparse, glob
import pandas as pd
from analyze import build_panel

ap = argparse.ArgumentParser()
ap.add_argument("--end-week", default=None)
ap.add_argument("--data", default="data")
ap.add_argument("--out", default="panel.csv")
a = ap.parse_args()
frames = [build_panel(d, a.end_week)[0] for d in sorted(glob.glob(f"{a.data}/*__*"))]
P = pd.concat(frames, ignore_index=True)
out = P[["repo", "week", "issues", "bugs", "any_rel", "age_any"]].rename(columns={"any_rel": "release", "age_any": "age"})
out.to_csv(a.out, index=False)
print(f"wrote {a.out}: {out['repo'].nunique()} repos, {len(out)} repository-weeks, {int(out['release'].sum())} release-weeks")
