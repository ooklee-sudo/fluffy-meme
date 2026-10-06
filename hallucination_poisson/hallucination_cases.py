"""Dispersion of dated public AI-hallucination court cases (Charlotin, AI Hallucination Cases database; CC BY 4.0).
The date is the court decision date (day resolution), the log is curated and subject to detection and reporting bias, and counts grew fast
until mid-2025, so only the later, flatter period is analysed.

  python -I hallucination_cases.py download.csv --out runs/hallucination_cases.json"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from triage_data import arrival_block  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("csv"); ap.add_argument("--out", default="runs/hallucination_cases.json")
a = ap.parse_args()
d = pd.read_csv(a.csv)
d["Date"] = pd.to_datetime(d["Date"], errors="coerce")
d = d.dropna(subset=["Date"])
out = {"n_cases_with_date": int(len(d)), "span": [str(d.Date.min().date()), str(d.Date.max().date())]}
monthly = d.groupby(d.Date.dt.to_period("M")).size()
out["monthly_counts_last_12"] = {str(k): int(v) for k, v in monthly.tail(12).items()}
seg = d[(d.Date >= "2025-10-01") & (d.Date < "2026-09-01")]   # the latest month is incomplete (reporting lag)
ts = seg.Date + pd.Timedelta(hours=12)            # date only: all cases at noon (hour-of-day fields are not meaningful)
blk = arrival_block(ts, "court decisions Oct 2025 - Aug 2026", workdays=[0, 1, 2, 3, 4])
keep = ["label", "n", "span", "days", "workdays", "mean_weekday_tickets", "weekend_to_weekday_daily_ratio", "weekday_dispersion_index_stratified", "weekday_dispersion_p",
        "implied_daily_rate_cv", "poisson_plan_exceeded_share", "negbin_plan_exceeded_share", "detrended", "causal"]
out["segment"] = {k: blk[k] for k in keep}
json.dump(out, open(a.out, "w"), indent=1, default=float)
print(json.dumps(out, indent=1, default=float)[:3000])
