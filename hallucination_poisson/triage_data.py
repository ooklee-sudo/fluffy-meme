"""Human-triage evidence from public company ticket data (see README):
  * Mendeley 'Help Desk Tickets' (international software company, 2016-2023; Abdellatif; CC BY 4.0)
  * UCI 'Incident management process enriched event log' (ServiceNow, 2016; Amaral et al.)
  * Mendeley 'Help desk log of an Italian software company' (2010-2012; Polato)
We estimate (i) arrival structure of tickets (non-homogeneity, over-dispersion at realistic daily rates) and a direct test
of Proposition 2, (ii) service/resolution-time distributions, (iii) concurrency of open tickets against M/G/inf.

  python -I triage_data.py --issues issues.csv --uci incident_event_log.csv --italian helpdesk_it.csv --out runs/triage_data.json"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stats_model import capacity, capacity_nb, exceed_prob_nb, fit_negbin  # noqa: E402

DAY = 86400.0


def detect_workdays(s):
    """The five days of the week with the most tickets (work week differs by country: e.g. Sunday-Thursday)."""
    cnt = np.bincount(pd.Series(s).dt.dayofweek, minlength=7)
    return sorted(np.argsort(cnt)[-5:].tolist())


def arrival_block(start, label, min_year=None, workdays=None, window=None):
    """start: tz-naive pandas datetime Series of ticket creation times. workdays: day-of-week numbers (0=Mon) of the work week;
    detected from the data if None. window: optional (start, end) restriction (stationary segment)."""
    s = pd.Series(pd.to_datetime(start)).dropna().sort_values()
    if min_year:
        s = s[s.dt.year >= min_year]
    if window:
        s = s[(s >= window[0]) & (s < window[1])]
    workdays = workdays if workdays is not None else detect_workdays(s)
    weekend = [k for k in range(7) if k not in workdays]
    days = pd.date_range(s.min().floor("D"), s.max().floor("D"), freq="D")
    dc = s.dt.floor("D").value_counts().reindex(days, fill_value=0)
    out = {"label": label, "n": int(len(s)), "span": [str(s.min()), str(s.max())], "days": int(len(days)), "lambda_per_day": float(len(s) / len(days))}
    # hour-of-week non-homogeneity
    how = (s.dt.dayofweek * 24 + s.dt.hour).values
    obs = np.bincount(how, minlength=168).astype(float)
    out["how_chi2_p"] = float(stats.chisquare(obs).pvalue)
    dow_counts = np.bincount(s.dt.dayofweek, minlength=7)
    out["workdays"] = [int(k) for k in workdays]
    out["weekday_share"] = float(dow_counts[workdays].sum() / dow_counts.sum())
    out["weekend_to_weekday_daily_ratio"] = float((dow_counts[weekend].sum() / 2) / (dow_counts[workdays].sum() / 5))
    # restrict the count analysis to weekdays with count>0 stream (weekends are a different regime); stratify by day of week
    wd = dc[dc.index.dayofweek.isin(workdays)]
    chi, df_ = 0.0, 0
    c2_num, c2_den = 0.0, 0.0
    exceed_p, exceed_nb_plan, n_days = 0.0, 0.0, 0
    per_dow = []
    for k in workdays:
        v = wd[wd.index.dayofweek == k].values.astype(float)
        m, var = v.mean(), v.var(ddof=1)
        chi += (len(v) - 1) * var / m; df_ += len(v) - 1
        c2_num += (var - m) * len(v) / m ** 2; c2_den += len(v)
        mm, r = fit_negbin(v)
        kp, kn = capacity(m, 0.95), capacity_nb(mm, r, 0.95)
        per_dow.append({"dow": k, "mean": float(m), "var_over_mean": float(var / m), "k_poisson": kp, "k_negbin": kn,
                        "poisson_plan_exceeded": float(np.mean(v > kp)), "negbin_plan_exceeded": float(np.mean(v > kn))})
        exceed_p += (v > kp).sum(); exceed_nb_plan += (v > kn).sum(); n_days += len(v)
    out["weekday_dispersion_index_stratified"] = float(chi / df_)
    out["weekday_dispersion_p"] = float(2 * min(stats.chi2.cdf(chi, df_), stats.chi2.sf(chi, df_)))
    out["implied_daily_rate_cv"] = float(np.sqrt(max(0.0, c2_num / c2_den)))
    out["mean_weekday_tickets"] = float(wd.mean())
    out["poisson_plan_exceeded_share"] = float(exceed_p / n_days)
    out["negbin_plan_exceeded_share"] = float(exceed_nb_plan / n_days)
    out["per_dow"] = per_dow
    # ---- net of slow trends: leave-one-out local mean over +-20 weekdays (about 8 weeks)
    v = wd.values.astype(float); n = len(v); w = 20
    mu = np.array([np.mean(np.concatenate([v[max(0, i - w):i], v[i + 1:i + w + 1]])) for i in range(n)])
    ok = mu > 0
    # day-of-week multiplicative effect removed first so the local mean is not biased by the weekly cycle
    dowv = wd.index.dayofweek.values
    eff7 = np.ones(7)
    for k in workdays:
        eff7[k] = v[dowv == k].mean()
    eff = eff7 / np.mean([eff7[k] for k in workdays]); eff = eff[dowv]
    vv = v / eff
    mu = np.array([np.mean(np.concatenate([vv[max(0, i - w):i], vv[i + 1:i + w + 1]])) for i in range(n)]) * eff
    pearson = float(np.mean((v[ok] - mu[ok]) ** 2 / mu[ok]))
    infl = 1 + 1.0 / (2 * w)            # inflation of Pearson dispersion from estimating mu with 2w neighbours
    phi = pearson / infl
    c2 = max(0.0, (phi - 1) / float(np.mean(mu[ok])))
    out["detrended"] = {"pearson_dispersion": float(phi), "implied_daily_rate_cv": float(np.sqrt(c2)),
                        "poisson_local_plan_exceeded": float(np.mean(v[ok] > stats.poisson.ppf(0.95, mu[ok]))),
                        "negbin_local_plan_exceeded": float(np.mean(v[ok] > np.array([capacity_nb(m_, (1 / c2) if c2 > 0 else np.inf, 0.95) for m_ in mu[ok]]))),
                        "mean_weekday_tickets": float(v.mean())}
    # ---- causal (feasible) plan: trailing 20-workday mean (weekday effect removed), c estimated on earlier days only, rolling origin
    start_i = 60 if n >= 120 else w + 20; ex_p = ex_nb = n_eval = 0
    for i in range(start_i, n):
        mu_i = np.mean(vv[i - w:i]) * eff[i]
        prev = np.array([np.mean(vv[j - w:j]) * eff[j] for j in range(w, i)])
        pv = (v[w:i] - prev) ** 2 / prev
        phi_i = max(1.0, float(np.mean(pv)) / (1 + 1.0 / w))
        c2_i = max(0.0, (phi_i - 1) / float(np.mean(prev)))
        kp = stats.poisson.ppf(0.95, mu_i)
        kn = capacity_nb(mu_i, (1 / c2_i) if c2_i > 0 else np.inf, 0.95)
        ex_p += v[i] > kp; ex_nb += v[i] > kn; n_eval += 1
    out["causal"] = {"poisson_plan_exceeded": float(ex_p / n_eval) if n_eval else None, "negbin_plan_exceeded": float(ex_nb / n_eval) if n_eval else None, "n_eval_days": int(n_eval)}
    # time-rescaled inter-arrival test with a fitted hour-of-week intensity (arrivals as events)
    t0 = s.iloc[0].floor("D")
    th = ((s - t0).dt.total_seconds() / 3600).values
    n_weeks = len(days) / 7.0
    rate = obs / n_weeks
    grid = np.arange(0, int(th.max()) + 2)
    slot = ((t0.dayofweek * 24 + grid) % 168).astype(int)
    cum = np.concatenate([[0.0], np.cumsum(rate[slot])])
    Lam = np.interp(th, np.arange(len(cum)), cum)
    g = np.diff(Lam); g = g[g > 0]
    out["interarrival_ks_p_time_rescaled"] = float(stats.kstest(g, "expon", args=(0, g.mean())).pvalue)
    out["rescaled_gap_cv"] = float(g.std() / g.mean())
    return out


def workload_block(created, work_hours, label):
    """Daily handling workload (sum of per-ticket hours of tickets created that day), weekdays only: safety factor q95/mean
    against the arrival-count safety factor q95/mean."""
    d = pd.DataFrame({"day": pd.to_datetime(created).dt.floor("D"), "w": np.asarray(work_hours, float)}).dropna()
    d = d[d.day.dt.dayofweek < 5]
    ww = d.groupby("day")["w"].sum(); cc = d.groupby("day").size()
    return {"label": label, "workload_q95_over_mean": float(np.percentile(ww, 95) / ww.mean()), "count_q95_over_mean": float(np.percentile(cc, 95) / cc.mean()),
            "workload_cv": float(ww.std() / ww.mean()), "count_cv": float(cc.std() / cc.mean()), "mean_daily_workload_hours": float(ww.mean())}


def service_block(hours, label):
    """hours: positive durations (hours)."""
    h = np.asarray(hours, float); h = h[np.isfinite(h) & (h > 0)]
    out = {"label": label, "n": int(len(h)), "mean": float(h.mean()), "median": float(np.median(h)), "p90": float(np.percentile(h, 90)),
           "p99": float(np.percentile(h, 99)), "cv": float(h.std() / h.mean())}
    # distribution fits (MLE) with AIC
    ll = {}
    ll["exponential"] = (stats.expon.logpdf(h, 0, h.mean()).sum(), 1)
    sh, loc, sc = stats.lognorm.fit(h, floc=0); ll["lognormal"] = (stats.lognorm.logpdf(h, sh, loc, sc).sum(), 2)
    c, loc, sc = stats.weibull_min.fit(h, floc=0); ll["weibull"] = (stats.weibull_min.logpdf(h, c, loc, sc).sum(), 2)
    out["aic"] = {k: float(2 * p - 2 * l) for k, (l, p) in ll.items()}
    out["best_fit"] = min(out["aic"], key=out["aic"].get)
    out["lognormal_sigma"] = float(sh); out["weibull_shape"] = float(c)
    out["ks_exponential_p"] = float(stats.kstest(h, "expon", args=(0, h.mean())).pvalue)
    return out


def concurrency_block(start, end, label):
    """Time-weighted distribution of open tickets vs the M/G/inf Poisson prediction."""
    d = pd.DataFrame({"s": pd.to_datetime(start), "e": pd.to_datetime(end)}).dropna()
    d = d[d.e >= d.s]
    ev = pd.concat([pd.Series(1, index=d.s), pd.Series(-1, index=d.e)]).sort_index().groupby(level=0).sum()
    lvl = ev.cumsum(); dt = np.diff(lvl.index.values).astype("timedelta64[s]").astype(float); lv = lvl.values[:-1]
    # drop the build-up/draining edges (first and last 5% of time) for steady-state comparison
    tot_t = dt.sum(); csum = np.cumsum(dt); keep = (csum > 0.05 * tot_t) & (csum < 0.95 * tot_t)
    ks = np.unique(lv[keep]); w = np.array([dt[keep & (lv == k)].sum() for k in ks]); p = w / w.sum()
    mean_obs = float((ks * p).sum()); var_obs = float(((ks - mean_obs) ** 2 * p).sum())
    cdf = np.cumsum(p)
    q = lambda a: int(ks[np.searchsorted(cdf, a)])
    return {"label": label, "time_avg_open": mean_obs, "var_over_mean": var_obs / max(mean_obs, 1e-9), "q95_observed": q(0.95),
            "q95_poisson_same_mean": int(stats.poisson.ppf(0.95, mean_obs)), "q99_observed": q(0.99), "q99_poisson_same_mean": int(stats.poisson.ppf(0.99, mean_obs))}


def load_mendeley(path):
    d = pd.read_csv(path, low_memory=False)
    for c in ("started", "ended", "issue_created", "issue_resolution_date"):
        d[c] = pd.to_datetime(d[c], utc=True, format="ISO8601").dt.tz_localize(None)
    return d


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--issues", required=True); ap.add_argument("--uci", required=True); ap.add_argument("--italian", required=True)
    ap.add_argument("--out", default="runs/triage_data.json")
    a = ap.parse_args()
    res = {}

    d = load_mendeley(a.issues)
    n_all = len(d)
    t = d[(d.issue_type == "Ticket") & (d.issue_created.dt.year >= 2017) & (d.issue_resolution == "Done")].copy()   # customer tickets, steady years
    filters = {"rows_in_file": int(n_all), "issue_type=Ticket": int((d.issue_type == "Ticket").sum()), "and created>=2017": int(((d.issue_type == "Ticket") & (d.issue_created.dt.year >= 2017)).sum()), "and resolution=Done (analysed)": int(len(t))}
    t["res_h"] = (t.issue_resolution_date - t.issue_created).dt.total_seconds() / 3600
    res["software_company"] = {
        "filters": filters,
        "arrivals": arrival_block(t.issue_created, "customer tickets 2017-2023"),
        "resolution_calendar_hours": service_block(t.res_h, "creation to resolution"),
        "in_progress_hours": service_block(t.wf_in_progress / 3600, "time in 'in progress' state"),
        "concurrency": concurrency_block(t.issue_created, t.issue_resolution_date, "open tickets"),
        "workload": workload_block(t.issue_created, t.wf_in_progress / 3600, "in-progress hours per creation day"),
        "high_priority": {"arrivals": arrival_block(t[t.issue_priority.isin(["High", "Highest", "Blocker"])].issue_created, "High/Highest/Blocker", workdays=detect_workdays(t.issue_created)),
                          "resolution_calendar_hours": service_block(t[t.issue_priority.isin(["High", "Highest", "Blocker"])].res_h, "High/Highest/Blocker")},
    }

    u = pd.read_csv(a.uci, encoding="latin-1", low_memory=False)
    for c in ("opened_at", "resolved_at", "closed_at"):
        u[c] = pd.to_datetime(u[c].replace("?", np.nan), format="%d/%m/%Y %H:%M", errors="coerce")
    g = u.groupby("number").agg(opened=("opened_at", "min"), resolved=("resolved_at", "max"), prio=("priority", "first"))
    g["res_h"] = (g.resolved - g.opened).dt.total_seconds() / 3600
    seg = (pd.Timestamp("2016-03-07"), pd.Timestamp("2016-05-28"))          # 98.9% of incidents are opened Feb 29 - Jun 1 2016; use the stationary middle weeks
    res["servicenow"] = {"arrivals": arrival_block(g.opened, "incidents, stationary segment 2016-03-07 to 2016-05-27", window=seg),
                         "resolution_calendar_hours": service_block(g.res_h, "opened to resolved"), "n_incidents": int(len(g)),
                         "share_opened_before_2016-06-02": float((g.opened < "2016-06-02").mean()),
                         "note": "concurrency not reported: the log starts and stops abruptly (build-up and cut-off artefacts)",
                         "high_priority": {"resolution_calendar_hours": service_block(g[g.prio.isin(["1 - Critical", "2 - High"])].res_h, "Critical/High"), "n": int(g.prio.isin(["1 - Critical", "2 - High"]).sum())}}

    h = pd.read_csv(a.italian)
    h["ts"] = pd.to_datetime(h.CompleteTimestamp)
    c = h.groupby("CaseID").agg(start=("ts", "min"), end=("ts", "max"))
    c["res_h"] = (c.end - c.start).dt.total_seconds() / 3600
    res["italian_helpdesk"] = {"arrivals": arrival_block(c.start, "cases 2010-2012"), "resolution_calendar_hours": service_block(c.res_h[c.res_h > 0], "first to last event"),
                               "concurrency": concurrency_block(c.start, c.end, "open cases"), "n_cases": int(len(c))}
    json.dump(res, open(a.out, "w"), indent=1, default=float)
    print(json.dumps(res, indent=1, default=float)[:12000])
