# Revision analyses

Python 3.10+, numpy, pandas, matplotlib. No statsmodels needed.

| Script | Purpose | Needs |
|---|---|---|
| `fig_from_reported.py` | Figures 1-3 from estimates already in the manuscript | nothing |
| `launch_daily.py` | Daily-resolution launch analysis with placebo-date randomization inference; Figure 4 | `releases.csv`, `launches.csv`, `exposure.csv` |
| `receiver_side.py` | Does adoption respond to cadence and to bug-preceded releases? | `weekly_panel.csv`, `releases.csv`, `adoption_weekly.csv` |
| `stats_utils.py` | Two-way FE OLS, CR1 cluster SEs, wild cluster restricted bootstrap (Webb) | |
| `make_synthetic.py` | Writes test data and documents every input schema | |
| `sql/` | BigQuery queries for PyPI downloads and GH Archive stars; `repo_map.csv` | |

Quick test:
    python make_synthetic.py
    python launch_daily.py  --data data_synthetic --out out_test --R 99
    python receiver_side.py --data data_synthetic --out out_test --B 199

Real run: put the five CSVs in ./data with the column names in make_synthetic.py, then
    python launch_daily.py --data data --out output --R 999
    python launch_daily.py --data data --out output_regular --R 999 --hotfix regular
    python launch_daily.py --data data --out output_clean  --R 999 --clean
    python receiver_side.py --data data --out output --B 999

Notes
- launches.csv `keywords`: case-insensitive regular expression for the model as it appears in release notes
  (e.g. "gpt-4o|gpt4o"); same patterns as events.csv of the first analysis kit.
- `age` / `regular_age` in weekly_panel.csv follow the manuscript's definitions (1 = first week
  after a release).
- The scripts were tested on synthetic data only; check the column mapping against your files.
- Verify the PyPI package names in sql/repo_map.csv before running the BigQuery query and do a
  dry run first: the PyPI table is large and billed by bytes scanned.
