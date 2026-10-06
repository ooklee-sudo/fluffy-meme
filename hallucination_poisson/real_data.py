"""Tests on public production data (see README): BurstGPT request traces (Azure OpenAI) and the LLM-provider
incident history of Chu et al. (OpenAI / Anthropic / Character.AI status pages).

  python -I real_data.py --burstgpt DIR --incidents CSV --out runs/real_data.json

BurstGPT: seconds since an unknown day-0 origin, three files: days 0-60, 61-120 and 225-334 (shared origin).
Incidents: provider-declared outages/degradations, minute resolution, UTC. Neither is a hallucination log."""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stats_model import capacity, capacity_nb, dispersion_test, fit_negbin  # noqa: E402

DAY = 86400


def load_burstgpt(d):
    parts = []
    for i in (1, 2, 3):
        df = pd.read_csv(os.path.join(d, f"BurstGPT_{i}.csv"), usecols=["Timestamp", "Response tokens", "Model", "Log Type"])
        df["file"] = i
        parts.append(df)
    df = pd.concat(parts, ignore_index=True)
    df["t"] = df["Timestamp"].astype(float)
    df["failed"] = df["Response tokens"] == 0
    return df.sort_values("t").reset_index(drop=True)


def detrended_daily_cv(counts, window):
    """CV of count_d / local_mean_d where local mean = centred moving average of the other days in the window.
    With ~1e5 requests/day, Poisson sampling noise is negligible, so this is the CV of the daily rate itself."""
    c = np.asarray(counts, float)
    n, h = len(c), window // 2
    ratio = []
    for i in range(h, n - h):
        nb = np.concatenate([c[i - h:i], c[i + 1:i + h + 1]])
        ratio.append(c[i] / nb.mean())
    ratio = np.array(ratio)
    return float(ratio.std(ddof=1)), ratio


def burst_analysis(df):
    out = {"rows": int(len(df)), "failed_share": float(df["failed"].mean())}
    day = (df["t"] // DAY).astype(int)
    cnt = day.value_counts().sort_index()
    full = cnt.reindex(range(int(cnt.index.min()), int(cnt.index.max()) + 1))
    out["days_covered"] = int(full.notna().sum())
    out["gap_days"] = int(full.isna().sum())
    daily = cnt.copy()
    out["daily_requests"] = {"min": int(daily.min()), "median": float(daily.median()), "max": int(daily.max())}

    # ---- hour-of-day profile (second-resolution timestamps are on the local clock)
    hod = ((df["t"] % DAY) // 3600).astype(int)
    prof = np.bincount(hod, minlength=24).astype(float)
    prof = prof / prof.mean()
    out["hourly_profile"] = prof.tolist()
    out["peak_to_trough"] = float(prof.max() / prof.min())

    # ---- day-to-day variability around the local level, per contiguous segment (files 1+2 | file 3)
    segs = {"days 0-120 (files 1-2)": (0, 120), "days 225-334 (file 3)": (225, 334)}
    out["daily_cv"] = {}
    for name, (a, b) in segs.items():
        s = daily[(daily.index >= a) & (daily.index <= b)].reindex(range(a, b + 1)).fillna(0)
        res = {}
        for w in (7, 14):
            cv, _ = detrended_daily_cv(s.values, w)
            res[f"window{w}"] = cv
        # weekly cycle: mean ratio by position mod 7, then residual CV after removing it
        cv7, ratio = detrended_daily_cv(s.values, 14)
        pos = (np.arange(a + 7, b + 1 - 7)) % 7
        wk = np.array([ratio[pos == k].mean() for k in range(7)])
        res["weekly_cycle_amplitude(max/min)"] = float(wk.max() / wk.min())
        resid = ratio / wk[pos]
        res["cv_after_weekly_cycle_removed"] = float(resid.std(ddof=1))
        out["daily_cv"][name] = res

    # ---- robust day-to-day variability and the calmest 14-day window (guards against regime shifts / artefacts)
    sv = daily.reindex(range(int(daily.index.min()), int(daily.index.max()) + 1))
    lg = np.log(sv.where(sv >= 1000))                      # ignore near-empty (logging-gap) days
    med = lg.rolling(15, center=True, min_periods=8).median()
    resid = (lg - med).dropna()
    d1 = np.diff(lg.dropna().values)
    out["robust_daily_variability"] = {"log_sd_vs_rolling_median(MAD)": float(1.4826 * np.median(np.abs(resid - np.median(resid)))),
                                       "median_abs_day_to_day_log_change": float(np.median(np.abs(d1))),
                                       "share_of_days_changing_by_over_30pct": float(np.mean(np.abs(d1) > np.log(1.3)))}
    best = None
    for st in range(int(sv.index.min()), int(sv.index.max()) - 13):
        w = sv.loc[st:st + 13]
        if w.isna().any() or (w < 1000).any():
            continue
        cv = float(w.std(ddof=1) / w.mean())
        if best is None or cv < best[0]:
            best = (cv, st, float(w.mean()))
    out["calmest_14day_window"] = {"cv": best[0], "start_day": best[1], "mean_per_day": best[2]} if best else None
    # near-duplicate days (identical or <1% different counts exactly 6 days apart) - a data artefact to disclose
    c = sv.values
    dup = [(i, i + 6) for i in range(len(c) - 6) if not np.isnan(c[i]) and not np.isnan(c[i + 6]) and c[i] > 1000 and abs(c[i] - c[i + 6]) / c[i] < 0.01]
    out["near_duplicate_days_6_apart"] = len(dup)

    # ---- short-scale burstiness: Fano factor of counts per bin, relative to the mean of the enclosing hour
    sec = df["t"].astype(np.int64).values
    out["fano"] = {}
    for width in (1, 10, 60, 600):
        # use busiest-stable subset: all hours with >= 200 requests, normalise to hourly mean rate
        nbins = int(sec.max() // width) + 1
        counts = np.bincount(sec // width, minlength=nbins).astype(float)
        per_hour = max(1, 3600 // width)
        k = (len(counts) // per_hour) * per_hour
        m = counts[:k].reshape(-1, per_hour)
        mean_h, var_h = m.mean(1), m.var(1, ddof=1)
        ok = mean_h >= 1.0
        out["fano"][str(width)] = {"median_var_over_mean": float(np.median(var_h[ok] / mean_h[ok])), "hours_used": int(ok.sum())}

    # ---- failures (response tokens == 0): daily counts, heavy tail
    fd = df[df["failed"]]["t"].floordiv(DAY).astype(int).value_counts().sort_index()
    fd = fd.reindex(range(int(fd.index.min()), int(fd.index.max()) + 1)).fillna(0)
    fd = fd[fd.index.isin(daily.index)]
    out["failures"] = {"median_per_day": float(fd.median()), "max_per_day": int(fd.max()),
                       "p95_over_median": float(np.percentile(fd, 95) / max(1.0, fd.median())),
                       "failure_rate_by_day_median": float((fd / daily.reindex(fd.index)).median()),
                       "days_over_100x_median": int((fd > 100 * max(1.0, fd.median())).sum())}
    return out, daily


def capacity_replay(daily, alpha=0.95):
    """Capacity implications of the *measured* daily variability: take the daily request counts of a
    stable window, scale to the unprotected 120 hallucinations/day scenario, compare Poisson vs NB k*."""
    res = {}
    for name, (a, b) in {"files 1-2": (0, 120), "file 3": (225, 334)}.items():
        s = daily[(daily.index >= a) & (daily.index <= b)].values.astype(float)
        cv, ratio = detrended_daily_cv(s, 14)
        for lam in (10.0, 120.0):
            r = lam * ratio                      # daily intensity = lam x measured multiplier
            rng = np.random.default_rng(0)
            draws = rng.poisson(np.tile(r, 200))  # Poisson given the day's intensity
            kp = capacity(lam, alpha)
            m, rr = fit_negbin(draws)
            res[f"{name}, lambda={lam:g}"] = {"cv": cv, "k_poisson": kp, "k_negbin": capacity_nb(m, rr, alpha),
                                              "poisson_plan_exceeded_share": float(np.mean(draws > kp)), "target": 1 - alpha}
    return res


def incident_analysis(path):
    d = pd.read_csv(path, parse_dates=["start_timestamp", "close_timestamp"])
    d = d[d["start_timestamp"] >= "2023-03-01"].copy()      # status pages of all three providers populated
    d["day"] = d["start_timestamp"].dt.floor("D").dt.tz_localize(None)
    out = {"n": int(len(d)), "span": [str(d["start_timestamp"].min()), str(d["start_timestamp"].max())]}
    days = pd.date_range(d["day"].min(), d["day"].max(), freq="D")
    groups = {"all providers": d, "OpenAI": d[d.provider == "openai"], "Anthropic": d[d.provider == "anthropic"],
              "impact>=2 (major/critical)": d[d.incident_impact_level >= 2]}
    out["counts"] = {}
    for g, x in groups.items():
        dc = x.groupby("day").size().reindex(days, fill_value=0).values
        wk = pd.Series(dc).groupby(np.arange(len(dc)) // 7).sum().values[:-1]
        m, r = fit_negbin(dc)
        D, p = dispersion_test(dc)
        Dw, pw = dispersion_test(wk)
        # dispersion test stratified by day-of-week (removes the weekly cycle) and time-rescaling by hour-of-week
        dser = pd.Series(dc, index=days); chi = 0.0; df_ = 0
        for k in range(7):
            v = dser[dser.index.dayofweek == k].values
            if v.mean() > 0:
                chi += (len(v) - 1) * v.var(ddof=1) / v.mean(); df_ += len(v) - 1
        strat_p = float(2 * min(stats.chi2.cdf(chi, df_), stats.chi2.sf(chi, df_)))
        how = (x["start_timestamp"].dt.dayofweek * 24 + x["start_timestamp"].dt.hour).values
        n_weeks = len(days) / 7.0
        rate_how = np.bincount(how, minlength=168) / n_weeks                       # events per hour-of-week slot
        t0 = x["start_timestamp"].min().floor("D")
        th = ((x["start_timestamp"].sort_values() - t0).dt.total_seconds() / 3600).values
        grid = np.arange(0, int(th.max()) + 2)
        slot = ((t0.dayofweek * 24 + t0.hour + grid) % 168).astype(int)
        cum = np.concatenate([[0.0], np.cumsum(rate_how[slot])])
        Lam = np.interp(th, np.arange(len(cum)), cum)
        rg = np.diff(Lam); rg = rg[rg > 0]
        ks_resc = stats.kstest(rg, "expon", args=(0, rg.mean()))
        # day-of-week and hour-of-day homogeneity of arrivals
        dow = np.bincount(x["start_timestamp"].dt.dayofweek, minlength=7); hod = np.bincount(x["start_timestamp"].dt.hour, minlength=24)
        out["counts"][g] = {"n": int(len(x)), "lambda_per_day": float(m), "daily_dispersion_index": float(dc.var(ddof=1) / m), "dispersion_p_stratified_by_dow": strat_p,
                            "stratified_dispersion_index": float(chi / df_), "interarrival_ks_p_time_rescaled_hour_of_week": float(ks_resc.pvalue),
                            "dispersion_p": p, "weekly_dispersion_p": pw, "nb_r_daily": None if not np.isfinite(r) else float(r),
                            "dow_chi2_p": float(stats.chisquare(dow).pvalue), "hod_chi2_p": float(stats.chisquare(hod).pvalue),
                            "k_star_poisson_daily": capacity(m, 0.95), "k_star_negbin_daily": capacity_nb(m, r, 0.95),
                            "observed_days_over_poisson_k": float(np.mean(dc > capacity(m, 0.95))), "max_per_day": int(dc.max()),
                            "dow_counts": dow.tolist()}
        # inter-arrival times
        t = np.sort(x["start_timestamp"].astype("int64").values) / 1e9 / DAY
        gaps = np.diff(t); gaps = gaps[gaps > 0]
        ks = stats.kstest(gaps, "expon", args=(0, gaps.mean()))
        out["counts"][g]["interarrival_cv"] = float(gaps.std() / gaps.mean()); out["counts"][g]["interarrival_ks_p"] = float(ks.pvalue)
    # ---- duration (human response) and concurrent open incidents (M/G/infinity check)
    dur = (d["close_timestamp"] - d["start_timestamp"]).dt.total_seconds() / 3600
    out["duration_hours"] = {"median": float(dur.median()), "p90": float(dur.quantile(.9)), "p99": float(dur.quantile(.99)), "mean": float(dur.mean()),
                             "cv": float(dur.std() / dur.mean()), "zero_duration_share": float((dur == 0).mean())}
    ev = pd.concat([pd.Series(1, index=d["start_timestamp"]), pd.Series(-1, index=d["close_timestamp"])]).sort_index()
    ev = ev.groupby(level=0).sum()
    # time-weighted distribution of concurrently open incidents
    lvl = ev.cumsum(); dt = np.diff(lvl.index.values).astype("timedelta64[s]").astype(float)
    levels = lvl.values[:-1]
    w = {int(k): float(dt[levels == k].sum()) for k in np.unique(levels)}
    tot = sum(w.values()); pmf = {k: v / tot for k, v in w.items()}
    lam_day = len(d) / ((d["start_timestamp"].max() - d["start_timestamp"].min()).total_seconds() / DAY)
    mean_open = lam_day * dur.mean() / 24.0
    cum = 0.0; q95 = None
    for k in sorted(pmf):
        cum += pmf[k]
        if q95 is None and cum >= 0.95: q95 = k
    out["concurrent_open"] = {"time_avg_observed": float(sum(k * v for k, v in pmf.items())), "mginf_poisson_mean": float(mean_open),
                              "q95_observed": q95, "q95_mginf_poisson": int(stats.poisson.ppf(0.95, mean_open)),
                              "pmf": {str(k): v for k, v in pmf.items() if k <= 8}}
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--burstgpt", required=True); ap.add_argument("--incidents", required=True); ap.add_argument("--out", default="runs/real_data.json")
    a = ap.parse_args()
    df = load_burstgpt(a.burstgpt)
    b, daily = burst_analysis(df)
    b["capacity_replay"] = capacity_replay(daily)
    res = {"burstgpt": b, "incidents": incident_analysis(a.incidents)}
    json.dump(res, open(a.out, "w"), indent=1, default=float)
    print(json.dumps(res, indent=1, default=float)[:9000])
