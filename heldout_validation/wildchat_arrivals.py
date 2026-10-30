"""Real request arrivals from WildChat-1M (allenai, ODC-BY) as a stress test of the Poisson / over-dispersion assumptions.

Only the request timestamp column is used. Hallucination status is NOT observed in WildChat (no gold answers);
the per-request hallucination outcomes come from the measured SQuAD cascade, so this tests arrival structure only.

Steps: download each parquet shard, keep timestamps, delete the shard; then
  - daily request counts, weekday effect, trend-adjusted local CV (leave-one-out ~8-week local mean)
  - index of dispersion of daily counts (weekday-stratified)
  - 14-day-window CV (min / median) to compare with the BurstGPT figures in Section 5.5
  - hour-of-day profile and within-hour Fano factors
  - stress test: replay the measured multipliers on event streams with mean 10 and 120 per day and
    report how often a Poisson-sized plan (95% quantile) is exceeded, in-sample and causal (trailing 20 days)
"""
import json, os, subprocess, sys
import numpy as np
import pyarrow.parquet as pq
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
TMP = "/tmp/wildchat"
os.makedirs(TMP, exist_ok=True)
NSHARD = 14
BASE = "https://huggingface.co/datasets/allenai/WildChat-1M/resolve/main/data/train-{:05d}-of-00014.parquet"
rng = np.random.default_rng(0)


def collect():
    ts = []
    for k in range(NSHARD):
        npy = f"{TMP}/ts_{k}.npy"
        if not os.path.exists(npy):
            p = f"{TMP}/shard{k}.parquet"
            if not os.path.exists(p):
                subprocess.run(["curl", "-sL", "-m", "900", "-o", p, BASE.format(k)], check=True)
            t = pq.read_table(p, columns=["timestamp", "toxic"], use_threads=False).to_pandas()
            np.save(npy, t["timestamp"].dt.tz_convert("UTC").dt.tz_localize(None).astype("datetime64[s]").astype("int64").to_numpy())
            os.remove(p)
        ts.append(np.load(npy))
        print("shard", k, len(ts[-1]), flush=True)
    return np.sort(np.concatenate(ts))


def daily(ts):
    day = ts // 86400
    d0, d1 = day.min(), day.max()
    cnt = np.bincount(day - d0, minlength=d1 - d0 + 1)
    dates = np.arange(d0, d1 + 1)
    wd = (dates + 4) % 7  # 1970-01-01 was a Thursday -> index 0 = Monday
    return dates, cnt.astype(float), wd


def local_cv(cnt, half=28, mask=None):
    """Pearson dispersion of counts against a leave-one-out local mean (after weekday effect removal) -> CV of the rate."""
    n = len(cnt)
    out = np.full(n, np.nan)
    for i in range(n):
        lo, hi = max(0, i - half), min(n, i + half + 1)
        idx = [j for j in range(lo, hi) if j != i and (mask is None or mask[j])]
        if len(idx) >= 20:
            out[i] = cnt[idx].mean()
    ok = ~np.isnan(out) & (out > 0)
    if mask is not None:
        ok &= mask
    mu = out[ok]
    pear = np.sum((cnt[ok] - mu) ** 2 / mu) / ok.sum()  # ~ 1 + mean*c^2
    c2 = max((pear - 1) * ok.sum() / np.sum(mu), 0)
    return float(np.sqrt(c2)), float(pear), int(ok.sum())


def window_cv(cnt, w=14, minc=1000):
    out = []
    for i in range(len(cnt) - w + 1):
        x = cnt[i:i + w]
        if (x > minc).all():
            out.append(x.std(ddof=1) / x.mean())
    return out


def stress(mult, lam, causal_window=20, reps=400):
    """Replay measured multipliers (rescaled to mean 1) on a stream with mean lam/day; Poisson plan exceedance."""
    n = len(mult)
    exc_in, exc_ca = [], []
    for _ in range(reps):
        x = rng.poisson(lam * mult)
        # in-sample two-sided local mean over ~40 days (leave-one-out), plan = Poisson 95% quantile of that mean
        e, c = 0, 0
        ne, nc = 0, 0
        for i in range(n):
            lo, hi = max(0, i - 20), min(n, i + 21)
            loc = (x[lo:hi].sum() - x[i]) / (hi - lo - 1)
            if loc > 0:
                e += x[i] > stats.poisson.ppf(0.95, loc); ne += 1
            if i >= causal_window:
                tr = x[i - causal_window:i].mean()
                if tr > 0:
                    c += x[i] > stats.poisson.ppf(0.95, tr); nc += 1
        exc_in.append(e / max(ne, 1)); exc_ca.append(c / max(nc, 1))
    return float(np.mean(exc_in)), float(np.mean(exc_ca))


def main():
    ts = collect()
    dates, cnt, wd = daily(ts)
    full = cnt > 0
    out = {"n_requests": int(len(ts)), "n_days": int(len(cnt)), "first_day": int(dates[0]), "last_day": int(dates[-1]),
           "median_daily": float(np.median(cnt[cnt > 0])), "min_daily": float(cnt[cnt > 0].min()), "max_daily": float(cnt.max()),
           "zero_days": int((cnt == 0).sum())}
    # hour-of-day profile (UTC)
    hour = (ts % 86400) // 3600
    prof = np.bincount(hour, minlength=24) / len(ts)
    out["hour_profile_peak_to_trough"] = float(prof.max() / prof.min())
    # weekday effect removal
    wmean = np.array([cnt[(wd == k) & full].mean() for k in range(7)])
    adj = cnt / wmean[wd] * wmean.mean()
    out["weekend_over_weekday"] = float(wmean[5:].mean() / wmean[:5].mean())
    # trend-adjusted CV, all days and after dropping days below 35% of the 41-day rolling median
    cv_all, pear_all, n_all = local_cv(adj, mask=full)
    med = np.array([np.median(adj[max(0, i - 20):i + 21]) for i in range(len(adj))])
    keep = full & (adj >= 0.35 * med)
    cv_ex, pear_ex, n_ex = local_cv(adj, mask=keep)
    out.update(cv_net_of_trend_all=cv_all, cv_net_of_trend_excl=cv_ex, pearson_all=pear_all, pearson_excl=pear_ex,
               days_all=n_all, days_excl=n_ex, excluded_low_days=int(full.sum() - keep.sum()))
    # naive dispersion index of daily counts, weekday stratified
    num = sum(np.sum((cnt[(wd == k) & full] - cnt[(wd == k) & full].mean()) ** 2 / cnt[(wd == k) & full].mean()) for k in range(7))
    dof = int(full.sum() - 7)
    out["stratified_dispersion_index"] = float(num / dof)
    wc = window_cv(cnt)
    out["window14_cv_min"] = float(np.min(wc)) if wc else None
    out["window14_cv_median"] = float(np.median(wc)) if wc else None
    out["n_windows14"] = len(wc)
    # within-hour Fano factors at 10 s, 1 min, 10 min on the busiest 30 days (counts per bin)
    top = np.argsort(cnt)[-30:]
    fano = {}
    for w, name in ((10, "10s"), (60, "1min"), (600, "10min")):
        vals = []
        for d in top:
            t = ts[(ts // 86400) == dates[d]] % 86400
            c = np.bincount((t // w).astype(int), minlength=86400 // w).astype(float)
            h = c.reshape(24, -1)  # per hour bins
            m, v = h.mean(1), h.var(1, ddof=1)
            vals.append(np.median(v[m > 0] / m[m > 0]))
        fano[name] = float(np.median(vals))
    out["fano_median_busy_days"] = fano
    # stress test with multipliers from the full series and from a trend-adjusted sub-series
    mult = (adj / adj[full].mean())[full]
    mult_net = (adj / np.where(med > 0, med, np.nan))[full & (med > 0)]
    mult_net = mult_net[~np.isnan(mult_net)]
    mult_net = mult_net / mult_net.mean()
    out["stress"] = {}
    for label, m in (("raw_multipliers", mult), ("net_of_trend_multipliers", mult_net)):
        m = np.asarray(m)
        out["stress"][label] = {str(l): dict(zip(("insample", "causal"), stress(m, l))) for l in (10, 120)}
        out["stress"][label]["cv"] = float(m.std(ddof=1))
    json.dump(out, open(os.path.join(RES, "wildchat_arrivals.json"), "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
