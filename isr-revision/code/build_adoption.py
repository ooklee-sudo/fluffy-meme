"""Merge pypi.csv and stars.csv (from fetch_adoption.py or the BigQuery queries in sql/) into data/adoption_weekly.csv.

pypi.csv:  package, week, downloads[, downloads_pip]
stars.csv: repo_name, week, stars_new
Repository names must match weekly_panel.csv; add entries to OLD2NEW if they differ.

Choices that affect the series (check them before the final run)
  - Renamed repositories: events under former names are mapped to the current name.
  - llama_index: llama-index-core only exists from early 2024, and its first weeks are small. The
    monolithic llama-index package is used until the first week in which llama-index-core has at least as
    many downloads, and llama-index-core afterwards. They are not summed, because llama-index depends
    on llama-index-core.
  - autogen: pyautogen and autogen-agentchat are summed (repo_map.csv). pyautogen is now maintained
    by the AG2 fork, so later pyautogen downloads may not reflect microsoft/autogen.
  - Weeks with no star events count as 0 stars. Weeks with no PyPI rows stay missing.
"""
import argparse
import os

import pandas as pd

OLD2NEW = {"ggerganov/whisper.cpp": "ggml-org/whisper.cpp", "jmorganca/ollama": "ollama/ollama",
           "jerryjliu/llama_index": "run-llama/llama_index"}
PRE_SPLIT = {"llama-index-core": "llama-index"}   # package -> predecessor used before its first week

ap = argparse.ArgumentParser()
ap.add_argument("--repos", default="sql/repo_map.csv")
ap.add_argument("--pypi", default="pypi.csv")
ap.add_argument("--stars", default="stars.csv")
ap.add_argument("--data", default="data")
a = ap.parse_args()

m = pd.read_csv(a.repos).fillna("")
pkg2repo = {p: r for r, ps in zip(m.repo, m.pypi_package) for p in ps.split(";") if p}
d = pd.read_csv(a.pypi)
for pkg, pre in PRE_SPLIT.items():
    if pkg in d.package.values and pre in d.package.values:
        w = d[d.package.isin([pkg, pre])].pivot(index="week", columns="package", values="downloads")
        caught_up = w[(w[pkg] >= w[pre])].index
        first = caught_up.min() if len(caught_up) else w.index.max()
        print(f"{pre} -> {pkg}: switch in week {first}")
        d = d[~((d.package == pre) & (d.week >= first)) & ~((d.package == pkg) & (d.week < first))]
        pkg2repo[pre] = pkg2repo[pkg]
d["repo"] = d.package.map(pkg2repo)
d = d.dropna(subset=["repo"]).groupby(["repo", "week"], as_index=False).downloads.sum()
s = pd.read_csv(a.stars)
s["repo"] = s.repo_name.replace(OLD2NEW)
s = s.groupby(["repo", "week"], as_index=False).stars_new.sum()
panel = pd.read_csv(os.path.join(a.data, "weekly_panel.csv"))[["repo", "week"]]
x = panel.merge(d, on=["repo", "week"], how="left").merge(s, on=["repo", "week"], how="left")
x["stars_new"] = x.stars_new.fillna(0)
missing = sorted(set(panel.repo) - set(d.repo) - set(s.repo))
if missing:
    print("WARNING: no adoption data matched for", missing)
print("repos without PyPI downloads (stars only):", sorted(set(panel.repo) - set(d.repo)))
x.to_csv(os.path.join(a.data, "adoption_weekly.csv"), index=False)
print("wrote", os.path.join(a.data, "adoption_weekly.csv"), x.shape)
