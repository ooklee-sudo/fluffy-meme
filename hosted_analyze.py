"""Merge the monitor's accuracy series with vendor refresh dates and ask the paper's question for hosted models.

Inputs
  results/hosted_runs.csv   from hosted_monitor.py
  events_hosted.csv         one row per vendor refresh you can document: date,model,type,source
                            e.g. 2026-03-12,gpt-4o,snapshot_update,https://... (type is free text)
                            Only dates taken from the vendor's own pages or API (the `model_returned` string
                            changing is also logged below as a measured refresh).

Outputs (printed, and written to results/hosted_analysis.json)
  1. weekly accuracy per model with Wilson 95% intervals
  2. measured refreshes: weeks in which the returned model string changed
  3. H1 analogue: within each model, does accuracy fall with weeks since the last refresh?
     (binomial GLM of correct on weeks-since-refresh, run-clustered SE) and a pooled estimate
  4. H4 analogue: does the chance of a refresh in week t rise after a drop in accuracy in week t-1?

With a handful of models and a handful of refreshes (3 and 4 will be thin), report intervals, not significance.

Usage: python hosted_analyze.py [--events events_hosted.csv]
"""
import argparse
import json

import numpy as np
import pandas as pd
import statsmodels.api as sm


def wilson(k, n, z=1.96):
    if n == 0:
        return np.nan, np.nan
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def load(runs_path, events_path):
    d = pd.read_csv(runs_path, parse_dates=["ts"])
    d = d[d["error"].isna() | (d["error"] == "")].copy()
    d["correct"] = d["correct"].astype(float)
    d["week"] = d["ts"].dt.to_period("W-SUN").dt.start_time
    d["run"] = d["ts"].dt.floor("min")
    try:
        ev = pd.read_csv(events_path, parse_dates=["date"])
        ev["week"] = ev["date"].dt.to_period("W-SUN").dt.start_time
    except FileNotFoundError:
        ev = pd.DataFrame(columns=["date", "model", "type", "source", "week"])
    return d, ev


def measured_refreshes(d):
    out = []
    for m, g in d.sort_values("ts").groupby("model_requested"):
        s = g.groupby("run")["model_returned"].agg(lambda x: x.mode().iat[0])
        changed = s != s.shift()
        for t in s.index[changed][1:]:
            out.append(dict(model=m, date=t, type="returned_model_changed", source="api"))
    r = pd.DataFrame(out)
    if len(r):
        r["week"] = pd.to_datetime(r["date"]).dt.to_period("W-SUN").dt.start_time
    return r


def weekly(d):
    g = d.groupby(["model_requested", "week"])["correct"].agg(["sum", "count"]).reset_index()
    ci = g.apply(lambda r: wilson(r["sum"], r["count"]), axis=1, result_type="expand")
    g["acc"], g["lo"], g["hi"] = g["sum"] / g["count"], ci[0], ci[1]
    return g


def age_slope(d, refresh_weeks, model):
    """Binomial GLM of correct on weeks since last refresh (refresh = documented or measured), run-clustered SE."""
    g = d[d["model_requested"] == model].copy()
    if g.empty:
        return None
    starts = sorted(set(refresh_weeks) | {g["week"].min()})
    g["age"] = g["week"].map(lambda w: (w - max(s for s in starts if s <= w)).days / 7)
    if g["age"].nunique() < 3 or g["correct"].nunique() < 2:
        return None
    X = sm.add_constant(g[["age"]])
    m = sm.GLM(g["correct"], X, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(g["run"])[0]})
    return dict(model=model, slope=float(m.params["age"]), se=float(m.bse["age"]), n=int(len(g)), n_refresh=len(starts) - 1)


def dl(est, se):
    est, se = np.asarray(est), np.asarray(se)
    w = 1 / se**2
    fe = (w * est).sum() / w.sum()
    q = (w * (est - fe) ** 2).sum()
    tau2 = max(0, (q - (len(est) - 1)) / (w.sum() - (w**2).sum() / w.sum()))
    ws = 1 / (se**2 + tau2)
    m = (ws * est).sum() / ws.sum()
    s = np.sqrt(1 / ws.sum())
    return m, m - 1.96 * s, m + 1.96 * s


def refresh_after_drop(wk, refreshes):
    """P(refresh in week t | accuracy fell by >= 1 SD of weekly changes in week t-1) versus otherwise."""
    rows = []
    for m, g in wk.groupby("model_requested"):
        g = g.sort_values("week").copy()
        g["chg"] = g["acc"].diff()
        sd = g["chg"].std()
        if not np.isfinite(sd) or sd == 0:
            continue
        g["drop_prev"] = (g["chg"].shift(1) <= -sd).astype(int)
        rw = set(refreshes.loc[refreshes["model"] == m, "week"])
        g["refresh"] = g["week"].isin(rw).astype(int)
        rows.append(g.dropna(subset=["drop_prev"]))
    if not rows:
        return None
    a = pd.concat(rows)
    after, other = a[a["drop_prev"] == 1], a[a["drop_prev"] == 0]
    return dict(p_refresh_after_drop=float(after["refresh"].mean()) if len(after) else None, n_after=int(len(after)),
                p_refresh_otherwise=float(other["refresh"].mean()) if len(other) else None, n_other=int(len(other)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="results/hosted_runs.csv")
    ap.add_argument("--events", default="events_hosted.csv")
    ap.add_argument("--out", default="results/hosted_analysis.json")
    a = ap.parse_args()
    d, ev = load(a.runs, a.events)
    meas = measured_refreshes(d)
    allref = pd.concat([ev.assign(model=ev["model"]), meas], ignore_index=True) if len(meas) else ev
    wk = weekly(d)
    print(f"{d['model_requested'].nunique()} models, {d['run'].nunique()} runs, {d['week'].nunique()} weeks, "
          f"{len(ev)} documented + {len(meas)} measured refreshes")
    res = {"weekly": wk.assign(week=wk["week"].astype(str)).round(4).to_dict("records")}
    sl = [s for s in (age_slope(d, allref.loc[allref["model"] == m, "week"], m) for m in d["model_requested"].unique()) if s]
    res["age_slopes"] = sl
    for s in sl:
        print(f"H1 analogue {s['model']}: accuracy log-odds per week since refresh {s['slope']:+.4f} (SE {s['se']:.4f}); {s['n_refresh']} refreshes")
    if len(sl) >= 2:
        m, lo, hi = dl([s["slope"] for s in sl], [s["se"] for s in sl])
        res["pooled_slope"] = dict(est=m, lo=lo, hi=hi)
        print(f"pooled slope {m:+.4f} [{lo:+.4f}, {hi:+.4f}]  (negative = accuracy falls with time since refresh)")
    res["refresh_after_drop"] = refresh_after_drop(wk, allref)
    print("H4 analogue:", res["refresh_after_drop"])
    with open(a.out, "w") as f:
        json.dump(res, f, indent=2, default=str)
    print("saved", a.out)


if __name__ == "__main__":
    main()
