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
from stats_model import capacity, capacity_nb  # noqa: E402
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
from pandas.tseries.holiday import USFederalHolidayCalendar  # noqa: E402
hol = USFederalHolidayCalendar().holidays(start="2025-10-01", end="2026-09-01")
blk_x = arrival_block(ts, "court decisions Oct 2025 - Aug 2026, US federal holidays excluded", workdays=[0, 1, 2, 3, 4], exclude=hol)
keep = ["label", "n", "span", "days", "workdays", "mean_weekday_tickets", "weekend_to_weekday_daily_ratio", "weekday_dispersion_index_stratified", "weekday_dispersion_p",
        "implied_daily_rate_cv", "poisson_plan_exceeded_share", "negbin_plan_exceeded_share", "detrended", "causal"]
out["segment"] = {k: blk[k] for k in keep}
out["segment_excl_holidays"] = {k: blk_x[k] for k in keep + ["excluded_work_days"]}
sep = d[(d.Date >= "2026-09-01") & (d.Date < "2026-10-01")]
out["excluded_months"] = {"2026-09": int(len(sep)), "2026-10 (data end 2026-10-01)": int((d.Date >= "2026-10-01").sum()), "reason": "recent months are incomplete because of reporting lag"}
for key in ("segment", "segment_excl_holidays"):
    blk_k = out[key]; lam = blk_k["mean_weekday_tickets"]; phi = max(1.0, blk_k["weekday_dispersion_index_stratified"])
    r_ = lam / (phi - 1.0) if phi > 1.0 else float("inf")
    blk_k["k95_poisson"] = int(capacity(lam, 0.95)); blk_k["k95_negbin_stratified_index"] = int(capacity_nb(lam, r_, 0.95))
json.dump(out, open(a.out, "w"), indent=1, default=float)
print(json.dumps(out, indent=1, default=float)[:3000])
