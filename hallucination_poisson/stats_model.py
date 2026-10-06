"""Poisson / NHPP math from the paper (Sections 1-2) plus the tests that check it on data."""
import numpy as np
from scipy import stats

# business-hours-shaped default traffic profile (relative weight per hour of day, mean 1)
DEFAULT_PROFILE = np.array([0.2, 0.15, 0.1, 0.1, 0.15, 0.3, 0.6, 1.0, 1.5, 1.8, 1.9, 1.8,
                            1.5, 1.7, 1.8, 1.7, 1.5, 1.2, 0.9, 0.7, 0.6, 0.45, 0.3, 0.25])
DEFAULT_PROFILE = DEFAULT_PROFILE / DEFAULT_PROFILE.mean()


def capacity(lam, alpha):
    """k* = min{k : P(X<=k) >= alpha} for X ~ Poisson(lam) (generalised inverse CDF, Sec. 2.2)."""
    if lam <= 0:
        return 0
    return int(stats.poisson.ppf(alpha, lam))


def underprovision_prob(lam, k):
    """P(X > k): share of days on which a capacity of k is exceeded."""
    return float(stats.poisson.sf(k, lam)) if lam > 0 else 0.0


def simulate_traffic(days, daily_queries, rng, profile=DEFAULT_PROFILE):
    """Non-homogeneous Poisson arrivals of user queries, piecewise-constant hourly intensity.
    Returns arrival times in hours since t=0."""
    prof = np.asarray(profile, float)
    rate = daily_queries * prof / prof.sum()  # queries per hour-of-day slot
    counts = rng.poisson(np.tile(rate, days))
    hours = np.repeat(np.arange(days * 24), counts)
    return np.sort(hours + rng.random(len(hours)))


def daily_counts(times_h, days):
    return np.bincount(np.minimum((times_h // 24).astype(int), days - 1), minlength=days)


def dispersion_test(counts):
    """Index-of-dispersion test of H0: counts ~ Poisson (any mean). Returns (D, p_two_sided)."""
    n, m = len(counts), float(np.mean(counts))
    if m == 0 or n < 2:
        return float("nan"), float("nan")
    d = float((n - 1) * np.var(counts, ddof=1) / m)
    p = 2 * min(stats.chi2.cdf(d, n - 1), stats.chi2.sf(d, n - 1))
    return d, float(min(1.0, p))


def fit_hourly_intensity(times_h, days):
    """MLE of a 24-slot periodic piecewise-constant intensity (events/hour)."""
    slot = (times_h % 24).astype(int)
    return np.bincount(slot, minlength=24) / days


def homogeneity_test(times_h, days):
    """Chi-square test of H0: constant intensity over the 24 hour-of-day slots."""
    obs = np.bincount((times_h % 24).astype(int), minlength=24).astype(float)
    if obs.sum() < 24 * 5:
        return float("nan"), float("nan")
    chi, p = stats.chisquare(obs)
    return float(chi), float(p)


def time_rescaled_gaps(times_h, days, hourly_rate):
    """Time-rescaling theorem: under the fitted NHPP, Lambda(t_i)-Lambda(t_{i-1}) ~ Exp(1)."""
    cum = np.concatenate([[0.0], np.cumsum(np.tile(hourly_rate, days))])
    lam_t = np.interp(times_h, np.arange(days * 24 + 1), cum)
    return np.diff(np.concatenate([[0.0], lam_t]))


def ks_exponential(gaps):
    """KS test of gaps against an exponential with MLE mean (Lilliefors-style: p is optimistic)."""
    gaps = gaps[gaps > 0]
    if len(gaps) < 10:
        return float("nan"), float("nan")
    res = stats.kstest(gaps, "expon", args=(0, gaps.mean()))
    return float(res.statistic), float(res.pvalue)


def analyse_events(times_h, days, alpha):
    """Everything Section 2 claims, estimated from an event-time stream."""
    n = len(times_h)
    dc = daily_counts(times_h, days)
    lam = n / days
    out = {"n_events": int(n), "lambda_per_day": lam}
    out["dispersion_D"], out["dispersion_p"] = dispersion_test(dc)
    out["homogeneity_chi2"], out["homogeneity_p"] = homogeneity_test(times_h, days)
    if n >= 10:
        raw = np.diff(np.concatenate([[0.0], times_h])) / 24.0  # days
        out["ks_raw_stat"], out["ks_raw_p"] = ks_exponential(raw)
        hr = fit_hourly_intensity(times_h, days)
        out["ks_rescaled_stat"], out["ks_rescaled_p"] = ks_exponential(time_rescaled_gaps(times_h, days, hr))
        out["hourly_intensity"] = hr.tolist()
    k = capacity(lam, alpha)
    out["k_star_poisson"] = k
    out["k_star_empirical"] = int(np.quantile(dc, alpha, method="higher")) if len(dc) else 0
    out["p_exceed_k_star_poisson"] = underprovision_prob(lam, k)
    out["p_exceed_k_star_observed"] = float(np.mean(dc > k))
    kmean = int(round(lam))
    out["p_exceed_mean_capacity_poisson"] = underprovision_prob(lam, kmean)
    out["p_exceed_mean_capacity_observed"] = float(np.mean(dc > kmean))
    out["daily_counts"] = dc.tolist()
    return out
