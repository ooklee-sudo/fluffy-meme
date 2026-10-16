"""Profile purchase-count distributions in public datasets (UCI Online Retail II, CDNOW sample).

Usage: python real_data_profile.py --retail2 PATH/online_retail_II.xlsx --cdnow PATH/CDNOW_sample.txt
Counts = number of distinct purchase occasions (invoices / transaction dates) per customer within a
4-week window, for a cohort observed before the window (zeros kept). Cancellations are excluded.
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import count_metrics as cm  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")


def profile(y, label):
    y = np.asarray(y, dtype=int)
    s = cm.summary(y)
    a, t, p = cm.cameron_trivedi(y)
    m = cm.fit_count_models(y)
    s.update(label=label, n=len(y), max=int(y.max()), ct_alpha=a, ct_p=p,
             aic_poisson=m["poisson"], aic_nb=m["nb"], aic_zip=m["zip"], best=m["best"],
             disp_ci_lo=cm.bootstrap_ci(y, lambda v: v.var(ddof=1) / v.mean(), n_boot=300)[0],
             disp_ci_hi=cm.bootstrap_ci(y, lambda v: v.var(ddof=1) / v.mean(), n_boot=300)[1])
    return s


def window_counts(df, cohort_ids, start, weeks=4):
    end = start + pd.Timedelta(weeks=weeks)
    w = df[(df.date >= start) & (df.date < end)].groupby("cid").event.nunique()
    return w.reindex(cohort_ids, fill_value=0).to_numpy()


def retail2(path):
    cache = path + ".parquet.csv"
    if os.path.exists(cache):
        df = pd.read_csv(cache, parse_dates=["date"], dtype={"cid": str, "event": str})
    else:
        sheets = pd.read_excel(path, sheet_name=None, dtype={"Invoice": str})
        df = pd.concat(sheets.values())
        df = df.rename(columns={"Invoice": "event", "InvoiceDate": "date", "Customer ID": "cid"})
        df = df[["event", "date", "cid", "Quantity", "Price"]]
        df.to_csv(cache, index=False)
        df["date"] = pd.to_datetime(df["date"])
    df = df.dropna(subset=["cid"])
    df = df[~df.event.astype(str).str.startswith("C")]  # drop cancellations
    t0 = df.date.min().normalize()
    first = df.groupby("cid").date.min()
    cohort = first[first < t0 + pd.Timedelta(days=90)].index  # customers active in first 3 months
    rows = []
    for k, off in enumerate([100, 128, 156, 184, 212, 240, 268]):
        y = window_counts(df, cohort, t0 + pd.Timedelta(days=off))
        rows.append(profile(y, f"retail2_win{k}_day{off}"))
    return rows, cohort


def cdnow(path):
    df = pd.read_csv(path, sep=r"\s+", header=None, names=["master", "cid", "date", "cds", "spend"])
    df["date"] = pd.to_datetime(df["date"].astype(str), format="%Y%m%d")
    df["event"] = df.date.astype(str)  # distinct purchase days
    cohort = df.cid.unique()
    t0 = pd.Timestamp("1997-04-01")  # after the Q1-1997 cohort entry quarter
    rows = []
    for k, off in enumerate([0, 28, 56, 84, 112, 140, 168]):
        y = window_counts(df, cohort, t0 + pd.Timedelta(days=off))
        rows.append(profile(y, f"cdnow_win{k}_day{off}"))
    y39 = window_counts(df, cohort, t0, weeks=39)
    rows.append(profile(y39, "cdnow_39weeks"))
    return rows, cohort


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--retail2", required=True)
    ap.add_argument("--cdnow", required=True)
    a = ap.parse_args()
    r1, c1 = retail2(a.retail2)
    r2, c2 = cdnow(a.cdnow)
    df = pd.DataFrame(r1 + r2).round(3)
    df.to_csv(f"{OUT}/real_profile.csv", index=False)
    json.dump({"retail2_cohort": len(c1), "cdnow_cohort": len(c2)}, open(f"{OUT}/real_profile_meta.json", "w"))
    pd.set_option("display.width", 250)
    print(df[["label", "n", "mean", "var", "disp_ratio", "disp_ci_lo", "disp_ci_hi", "zero_frac", "top10_share",
              "ct_p", "best"]].to_string(index=False))
