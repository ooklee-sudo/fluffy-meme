"""Metrics shared by the studies."""
import math
import numpy as np
from scipy import optimize, stats

_ANCHORS_H = [0, 2, 4, 5, 7, 9, 11, 12.5, 14, 16, 18, 20, 21.5, 23, 24]
_ANCHORS_V = [0.6, 0.3, 0.15, 0.15, 0.5, 0.9, 1.3, 1.5, 1.2, 1.1, 1.5, 2.0, 2.2, 1.4, 0.6]


def reference_hourly():
    """Assumed stylized bimodal daily profile (piecewise-linear, not the
    simulator's functional form). Not empirical data."""
    v = np.interp(np.arange(24) + 0.5, _ANCHORS_H, _ANCHORS_V)
    return v / v.sum()


REF_SIGMA, REF_MEDIAN, REF_TRUNC = 1.2, 0.5, 48.0


def reference_delay_cdf(x):
    """Log-normal (median 0.5 h) truncated at 48 h. Assumed, not empirical."""
    x = np.asarray(x, float)
    full = stats.lognorm.cdf(x, s=REF_SIGMA, scale=REF_MEDIAN)
    top = stats.lognorm.cdf(REF_TRUNC, s=REF_SIGMA, scale=REF_MEDIAN)
    return np.clip(full, 0, top) / top


def hourly_dist(events):
    c = np.zeros(24)
    for t, a, act, iid, d in events:
        if act < 3:
            c[int(t % 24)] += 1
    return c


def reply_delays(events):
    return np.array([d for t, a, act, iid, d in events if act == 1])


def behaviour_metrics(events):
    c = hourly_dist(events)
    p = c / c.sum()
    ref = reference_hourly()
    r = float(np.corrcoef(p, ref)[0, 1])
    tv = float(0.5 * np.abs(p - ref).sum())
    chi2 = float((((c - ref * c.sum()) ** 2) / (ref * c.sum())).sum())
    d = reply_delays(events)
    d = d[d <= REF_TRUNC]
    ks = float(stats.kstest(d, reference_delay_cdf).statistic) if len(d) else float("nan")
    return dict(r=r, tv=tv, chi2=chi2, ks=ks,
                med_delay=float(np.median(d)) if len(d) else float("nan"),
                frac_5min=float((d < 5 / 60).mean()) if len(d) else float("nan"),
                tail24=float((d > 24).mean()) if len(d) else float("nan"),
                n=int(c.sum()))


def hourly_counts_series(events, horizon):
    h = np.zeros(int(horizon))
    for t, a, act, iid, d in events:
        if act < 3 and t < horizon:
            h[int(t)] += 1
    return h


def hawkes_branching(times, t0, T):
    """MLE of Hawkes with constant background mu and kernel alpha*beta*exp(-beta s);
    branching ratio = alpha. Times measured from t0 over window [0, T]."""
    x = np.sort(np.asarray(times, float) - t0)
    x = x[(x >= 0) & (x <= T)]
    n = len(x)
    if n < 10:
        return float("nan"), float("nan")

    def nll(th):
        mu, al, be = np.exp(th[0]), 1 / (1 + np.exp(-th[1])), np.exp(th[2])
        R = 0.0
        ll = 0.0
        prev = None
        for i in range(n):
            if i > 0:
                R = math.exp(-be * (x[i] - x[i - 1])) * (1 + R)
            ll += math.log(mu + al * be * R)
        ll -= mu * T + al * float((1 - np.exp(-be * (T - x))).sum())
        return -ll

    best = None
    for b0 in (1.0, 4.0):
        res = optimize.minimize(nll, [math.log(max(n / T * 0.2, 1e-3)), 1.5, math.log(b0)],
                                method="Nelder-Mead", options=dict(maxiter=600, xatol=1e-4, fatol=1e-6))
        if best is None or res.fun < best.fun:
            best = res
    th = best.x
    return float(1 / (1 + math.exp(-th[1]))), float(math.exp(th[2]))
