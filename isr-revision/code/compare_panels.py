"""Compare the rebuilt panel with the first kit's panel (kit results/panel.csv), row by row.

    python compare_panels.py data\\weekly_panel.csv data\\releases.csv C:\\Users\\leeook\\isr_analysis_kit\\results\\panel.csv

kit panel.csv columns used: repo, week, any_rel, any_reg, n_hot, issues, bugs
Prints the number of rows, mismatches per column, and the hot-fix share (manuscript: 0.43).
"""
import sys
import pandas as pd

P = pd.read_csv(sys.argv[1], parse_dates=["week"])
R = pd.read_csv(sys.argv[2], parse_dates=["published_at"])
K = pd.read_csv(sys.argv[3], parse_dates=["week"])
R["week"] = R.published_at.dt.to_period("W-SUN").dt.start_time
hot = R[R.is_hotfix == 1].groupby(["repo", "week"]).size().rename("n_hot_mine")
M = P.merge(K, on=["repo", "week"], how="outer", suffixes=("", "_kit"), indicator=True)
M = M.merge(hot, on=["repo", "week"], how="left").fillna({"n_hot_mine": 0})
print("rows: mine", len(P), "| kit", len(K), "| in both", int((M._merge == "both").sum()))
B = M[M._merge == "both"]
for mine, kit in [("release", "any_rel"), ("regular_release", "any_reg"), ("issues", "issues_kit"), ("bugs", "bugs_kit"), ("n_hot_mine", "n_hot")]:
    if kit not in B.columns:
        kit = kit.replace("_kit", "")
    d = B[B[mine] != B[kit]]
    print(f"{mine:16s} vs {kit:10s} mismatches: {len(d)} of {len(B)}")
    if 0 < len(d) <= 5:
        print(d[["repo", "week", mine, kit]].to_string(index=False))
print("hot-fix share of releases:", round(R.is_hotfix.mean(), 4), "(manuscript 0.43)")
