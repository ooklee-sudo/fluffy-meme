"""Typed failure-model analysis on public production data.

  python -I run_failure_models.py --burstgpt DIR --incidents CSV --out runs/failure_models.json
"""
import argparse
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from failure_models import (typed_capacity, Seasonal, episodes_from_minutes, fit_profile, hawkes_test, hill_tail_index, profile_slots)  # noqa: E402
from real_data import load_burstgpt  # noqa: E402


def incidents_block(path, n_boot):
    d = pd.read_csv(path, parse_dates=["start_timestamp"])
    d = d[d["start_timestamp"] >= "2023-03-01"].copy()
    d["start"] = d["start_timestamp"].dt.tz_localize(None)
    t0 = pd.Timestamp("2023-03-01"); t1 = pd.Timestamp("2024-08-31")
    T = (t1 - t0).total_seconds() / 3600
    hours = pd.date_range(t0, t1, freq="h", inclusive="left")
    slot_hours = np.bincount(profile_slots(hours), minlength=48).astype(float)
    out = {}
    groups = {"all providers": d, "OpenAI": d[d.provider == "openai"], "Anthropic": d[d.provider == "anthropic"], "impact>=2": d[d.incident_impact_level >= 2]}
    for name, x in groups.items():
        th = np.sort(((x["start"] - t0).dt.total_seconds() / 3600).values)
        # break exact ties by 1 second so that the likelihood is well defined
        th = th + np.arange(len(th)) * (1 / 3600) * 1e-3
        s = fit_profile(profile_slots(pd.DatetimeIndex(x["start"])), slot_hours)
        seas = Seasonal(np.datetime64(t0), T, s / (np.sum(s * slot_hours) / slot_hours.sum()))
        out[name] = hawkes_test(th, seas, T, n_boot=n_boot, rng=np.random.default_rng(1))
        # level-adjusted baseline: seasonal profile x monthly level (absorbs slow changes of the incident rate that would otherwise look like excitation)
        months = pd.period_range(t0, t1 - pd.Timedelta(hours=1), freq="M")
        hr_idx = pd.date_range(t0, t1, freq="h", inclusive="left")
        mon_of_hour = np.searchsorted(np.array([m.start_time for m in months]), hr_idx.values, side="right") - 1
        exp_prof = np.array([np.sum(s[profile_slots(hr_idx[mon_of_hour == k])]) for k in range(len(months))])
        cnt_m = np.bincount(np.searchsorted(np.array([m.start_time for m in months]), x["start"].values, side="right") - 1, minlength=len(months)).astype(float)
        lvl = np.maximum(cnt_m / np.maximum(exp_prof, 1e-9), 1e-4)
        lvl = lvl / (np.sum(lvl * np.array([np.sum(mon_of_hour == k) for k in range(len(months))])) / len(hr_idx))
        hourly_mult = lvl[mon_of_hour]
        seas_l = Seasonal(np.datetime64(t0), T, s / (np.sum(s * slot_hours) / slot_hours.sum()), hourly_mult=hourly_mult)
        out[name + "__level_adjusted"] = hawkes_test(th, seas_l, T, n_boot=n_boot, rng=np.random.default_rng(1))
        if name == "all providers":
            exp_m = cnt_m.sum() * (exp_prof / exp_prof.sum())
            chi, pv = stats.chisquare(cnt_m, f_exp=exp_m)
            out["monthly_counts_all"] = {"months": [str(m) for m in months], "counts": cnt_m.astype(int).tolist(), "homogeneity_chi2": float(chi), "df": int(len(months) - 1), "p": float(pv)}
    return out


def burst_block(path, n_boot):
    df = load_burstgpt(path)
    sec = df["t"].astype(np.int64).values
    # contiguous time axis: remove the unrecorded gap between the two segments
    gap_start = 121 * 86400; gap_len = (225 - 121) * 86400
    sec = np.where(sec >= 225 * 86400, sec - gap_len, sec)
    fail = df["failed"].values
    nmin = int(sec.max() // 60) + 1
    m_all = np.bincount(sec // 60, minlength=nmin); m_f = np.bincount(sec[fail] // 60, minlength=nmin)
    st, en, sz = episodes_from_minutes(m_f, m_all)
    out = {"failed_requests": int(fail.sum()), "requests": int(len(sec)), "n_episodes": int(len(st))}
    out["share_of_failures_in_episodes"] = float(sz.sum() / fail.sum())
    out["share_of_minutes_in_episodes"] = float(sum(e - s + 1 for s, e in zip(st, en)) / max(1, (m_all > 0).sum()))
    dur = (en - st + 1).astype(float)
    out["episode_duration_minutes"] = {"median": float(np.median(dur)), "mean": float(dur.mean()), "p90": float(np.percentile(dur, 90)), "max": float(dur.max())}
    out["episode_size"] = {"median": float(np.median(sz)), "mean": float(sz.mean()), "p90": float(np.percentile(sz, 90)), "p99": float(np.percentile(sz, 99)), "max": float(sz.max()),
                           "hill_tail_index": hill_tail_index(sz), "cv": float(sz.std() / sz.mean())}
    ls = np.log(sz); out["episode_size_lognormal"] = {"mu": float(ls.mean()), "sigma": float(ls.std(ddof=1))}
    # background (non-episode) failures: failure share outside episodes
    mask = np.ones(nmin, bool)
    for s, e in zip(st, en):
        mask[s:e + 1] = False
    bg_f = m_f[mask].sum(); bg_n = m_all[mask].sum()
    out["background_failure_rate_per_request"] = float(bg_f / bg_n)
    fo = m_f[mask & (m_all >= 50)]; ao = m_all[mask & (m_all >= 50)]
    # dispersion of background failure counts per minute vs binomial thinning of requests (should be ~1 if background is Poisson-thinned)
    exp_ = ao * (bg_f / bg_n)
    out["background_minute_pearson_dispersion"] = float(np.mean((fo - exp_) ** 2 / np.maximum(exp_ * (1 - bg_f / bg_n), 1e-9)))
    # arrivals of episodes
    start_h = np.sort(st / 60.0)
    T = nmin / 60.0
    days = np.bincount((st // 1440).astype(int), minlength=int(nmin // 1440) + 1)
    out["episodes_per_day"] = {"mean": float(days.mean()), "dispersion_index": float(days.var(ddof=1) / days.mean()), "max": int(days.max())}
    gaps = np.diff(start_h); gaps = gaps[gaps > 0]
    out["episode_interarrival_hours"] = {"median": float(np.median(gaps)), "mean": float(gaps.mean()), "cv": float(gaps.std() / gaps.mean())}
    # seasonal profile by hour-of-day only (calendar weekdays unknown): weekday/weekend slots share one profile
    hours = pd.date_range("2000-01-03", periods=int(np.ceil(T)), freq="h")
    slot_hours = np.bincount(profile_slots(hours), minlength=48).astype(float)
    hod = (start_h % 24).astype(int)
    cnt = np.bincount(hod, minlength=24).astype(float)
    prof24 = np.maximum(cnt / cnt.mean(), 1e-3); prof24 = np.maximum(prof24, 0.05)
    s48 = np.concatenate([prof24, prof24])
    seas = Seasonal(np.datetime64("2000-01-03"), T, s48 / s48.mean())
    out["hawkes_episodes"] = hawkes_test(start_h + np.arange(len(start_h)) * 1e-6, seas, T, n_boot=n_boot, rng=np.random.default_rng(2))
    out["episode_arrivals_daily_series"] = days.tolist()
    # ---- volume-conditional analyses (request volume ranges over two orders of magnitude)
    req_day = np.bincount(sec // 86400, minlength=int(nmin // 1440) + 1).astype(float)
    ep_day = np.bincount((st // 1440).astype(int), minlength=len(req_day)).astype(float)
    exp_ep = ep_day.sum() * req_day / req_day.sum()
    okd = exp_ep >= 1.0
    out["episodes_conditional_on_volume"] = {"pearson_dispersion_daily": float(np.sum((ep_day[okd] - exp_ep[okd]) ** 2 / exp_ep[okd]) / (okd.sum() - 1)), "days_used": int(okd.sum())}
    fail_day = np.bincount(sec[fail] // 86400, minlength=len(req_day)).astype(float)
    exp_f = fail_day.sum() * req_day / req_day.sum()
    okf = exp_f >= 1.0
    out["failed_requests_conditional_on_volume"] = {"pearson_dispersion_daily": float(np.sum((fail_day[okf] - exp_f[okf]) ** 2 / exp_f[okf]) / (okf.sum() - 1)), "days_used": int(okf.sum())}
    out["episode_size_second_moment_ratio"] = {"empirical_EX2_over_EX": float(np.mean(sz ** 2) / np.mean(sz)), "lognormal_implied": float(np.exp(ls.mean() + 1.5 * ls.var(ddof=1)))}
    hour_vol = np.bincount(sec // 3600, minlength=int(nmin // 60) + 1).astype(float)
    hv = hour_vol / hour_vol[hour_vol > 0].mean()
    seas_x = Seasonal(np.datetime64("2000-01-03"), T, np.ones(48), hourly_mult=hv)
    out["hawkes_episodes_exposure_adjusted"] = hawkes_test(start_h + np.arange(len(start_h)) * 1e-6, seas_x, T, n_boot=n_boot, rng=np.random.default_rng(3))
    # sensitivity of the episode definition
    sens = []
    for rt, mf, mg in ((0.2, 5, 10), (0.2, 5, 60), (0.1, 5, 30), (0.5, 5, 10), (0.2, 20, 30)):
        st2, en2, sz2 = episodes_from_minutes(m_f, m_all, rate_thr=rt, min_fail=mf, merge_gap=mg)
        sh2 = np.sort(st2 / 60.0)
        d2 = np.bincount((st2 // 1440).astype(int), minlength=int(nmin // 1440) + 1)
        hh = hawkes_test(sh2 + np.arange(len(sh2)) * 1e-6, seas, T, n_boot=30, rng=np.random.default_rng(5))
        sens.append({"rate_thr": rt, "min_fail": mf, "merge_gap_min": mg, "n_episodes": int(len(st2)), "share_of_failures": float(sz2.sum() / fail.sum()),
                     "dispersion_index_daily": float(d2.var(ddof=1) / d2.mean()), "hawkes_alpha": hh["hawkes"]["alpha"], "halflife_h": hh["excitation_halflife_hours"],
                     "boot_p": hh["bootstrap_p"], "ks_hawkes_p": hh["ks_rescaled_p_hawkes"], "median_size": float(np.median(sz2)), "p99_size": float(np.percentile(sz2, 99))})
    out["sensitivity"] = sens
    return out


def typed_scenarios(res):
    """Illustrative organisation with three human-handled classes (parameters from our estimates; classes assumed independent):
    H hallucinations after the classifier-only cascade L1+L2 (Qwen2.5-0.5B run: measured lambda; daily-rate CV c_H assumed within the range
       estimated from the steady ticket streams),
    P provider incidents that affect the organisation (lambda and day-of-week-stratified dispersion index of the incident history),
    S own serving-failure episodes (episode rate and daily dispersion index of the BurstGPT episodes; fine and coarse definitions; and the
       volume-conditional dispersion as a third value)."""
    tri = json.load(open("runs/triage_data.json"))
    cs = [tri["software_company"]["arrivals"]["detrended"]["implied_daily_rate_cv"], tri["italian_helpdesk"]["arrivals"]["detrended"]["implied_daily_rate_cv"]]
    lam_h = next(c["lambda_per_day"] for c in json.load(open("runs/qwen05/analysis_sla500.json"))["configs"] if c["config"] == "L1+L2")
    inc = json.load(open("runs/real_data.json"))["incidents"]["counts"]["all providers"]
    P = (inc["lambda_per_day"], inc["stratified_dispersion_index"])
    sens = res["burstgpt"]["sensitivity"]
    vol_phi = res["burstgpt"]["episodes_conditional_on_volume"]["pearson_dispersion_daily"]
    DAYS_REC = 231.0                                   # recorded days in BurstGPT
    out = {"lambda_H": lam_h, "cv_H_range_from_steady_ticket_streams": cs, "P": {"lambda": P[0], "phi": P[1]}, "days_recorded": DAYS_REC, "mc_days": 400000, "mc_seed": 0, "scenarios": []}
    for c_h in (0.3, float(np.mean(cs)), 0.45):
        phi_h = 1 + lam_h * c_h ** 2
        for name, sc, phi_s in (("fine (10-min merge)", sens[0], sens[0]["dispersion_index_daily"]), ("coarse (60-min merge)", sens[1], sens[1]["dispersion_index_daily"]),
                                ("coarse episodes, volume-conditional dispersion", sens[1], max(1.0, vol_phi))):
            lam_s = sc["n_episodes"] / DAYS_REC
            out["scenarios"].append({"c_H": c_h, "phi_H": phi_h, "S_definition": name, "S_lambda": lam_s, "S_phi": phi_s,
                                     "H_only": typed_capacity({"H": (lam_h, phi_h)}),
                                     "H_plus_P": typed_capacity({"H": (lam_h, phi_h), "P": P}),
                                     "all_classes": typed_capacity({"H": (lam_h, phi_h), "P": P, "S": (lam_s, phi_s)})})
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--burstgpt", required=True); ap.add_argument("--incidents", required=True)
    ap.add_argument("--out", default="runs/failure_models.json"); ap.add_argument("--boot", type=int, default=200)
    a = ap.parse_args()
    res = {"incidents": incidents_block(a.incidents, a.boot), "burstgpt": burst_block(a.burstgpt, a.boot)}
    res["typed_capacity"] = typed_scenarios(res)
    json.dump(res, open(a.out, "w"), indent=1, default=float)
    print(json.dumps({k: v for k, v in res["burstgpt"].items() if k != "episode_arrivals_daily_series"}, indent=1, default=float)[:6000])
    for k, v in res["incidents"].items():
        if k == "monthly_counts_all":
            continue
        print(k, {x: (round(y, 3) if isinstance(y, float) else y) for x, y in v.items() if x in ("n", "lr", "bootstrap_p", "mean_cluster_size", "excitation_halflife_hours", "ks_rescaled_p_nhpp", "ks_rescaled_p_hawkes")}, v["hawkes"], v["aic"])
