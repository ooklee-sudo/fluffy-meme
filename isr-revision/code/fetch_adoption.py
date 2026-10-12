"""Weekly PyPI downloads and GitHub stars from ClickHouse's free public mirrors (no BigQuery needed).

    python fetch_adoption.py --repos sql/repo_map.csv --out .     # writes pypi.csv and stars.csv
    python build_adoption.py                                       # merges into data/adoption_weekly.csv

Sources (https://sql-clickhouse.clickhouse.com, user "demo", read-only)
  pypi.pypi_downloads_per_day   daily download counts per PyPI project (ClickPy, derived from the same
                                 PyPI BigQuery download logs as bigquery-public-data.pypi.file_downloads)
  github.repo_events_per_day    GH Archive events aggregated per repo and day; stars are WatchEvent
                                 (github.github_events is too large: the server truncates the scan silently)
Weeks start on Monday. The range is 2023-01-02 up to --end (exclusive, a Monday).
Former repository names are included because GH Archive logs events under the name at event time.
"""
import argparse
import io
import urllib.request

import pandas as pd

URL = "https://sql-clickhouse.clickhouse.com/?user=demo&default_format=CSVWithNames"
OLD_NAMES = ["ggerganov/whisper.cpp", "jmorganca/ollama", "jerryjliu/llama_index"]


def q(sql):
    req = urllib.request.Request(URL, data=sql.encode(), method="POST")
    with urllib.request.urlopen(req, timeout=600) as r:
        return pd.read_csv(io.BytesIO(r.read()))


def lit(xs):
    return ",".join("'" + x.replace("'", "''") + "'" for x in xs)


ap = argparse.ArgumentParser()
ap.add_argument("--repos", default="sql/repo_map.csv")
ap.add_argument("--out", default=".")
ap.add_argument("--start", default="2023-01-02")
ap.add_argument("--end", default="2026-10-12")
a = ap.parse_args()

m = pd.read_csv(a.repos).fillna("")
pk = sorted({p for ps in m.pypi_package for p in ps.split(";") if p} | {"llama-index"})  # llama-index: pre-split monolith, see build_adoption.py
d = q(f"""SELECT project AS package, toMonday(date) AS week, sum(count) AS downloads
          FROM pypi.pypi_downloads_per_day
          WHERE project IN ({lit(pk)}) AND date >= '{a.start}' AND date < '{a.end}'
          GROUP BY package, week ORDER BY package, week""")
d.to_csv(f"{a.out}/pypi.csv", index=False)
print("pypi.csv", d.shape, "packages:", sorted(d.package.unique()))
print("missing packages:", sorted(set(pk) - set(d.package)))

names = list(m.repo) + OLD_NAMES
s = q(f"""SELECT repo_name, toMonday(created_at) AS week, sum(count) AS stars_new
          FROM github.repo_events_per_day
          WHERE event_type = 'WatchEvent' AND lower(repo_name) IN ({lit([n.lower() for n in names])})
            AND created_at >= '{a.start}' AND created_at < '{a.end}'
          GROUP BY repo_name, week ORDER BY repo_name, week""")
s.to_csv(f"{a.out}/stars.csv", index=False)
print("stars.csv", s.shape, "repo names:", sorted(s.repo_name.unique()))
