"""Typed failure models: NHPP with a seasonal profile, Hawkes (self-exciting) extension, compound-Poisson episodes,
and a superposition simulator for capacity.

Hawkes with exponential kernel and fixed periodic baseline profile s(t) (mean 1):
    lambda(t) = mu0 * s(t) + sum_{t_i<t} alpha * beta * exp(-beta (t - t_i))     alpha = branching ratio, beta in 1/hour
"""
import numpy as np
from scipy import optimize, stats


# ------------------------------------------------------------------ seasonal profile (weekday/weekend x hour)
def profile_slots(dt_index):
    """Slot id 0..47 (weekday/weekend x hour) for a DatetimeIndex."""
    return (dt_index.dayofweek >= 5).astype(int) * 24 + dt_index.hour


def fit_profile(slot_of_event, slot_hours):
    """s[k] = event rate in slot k relative to the overall mean rate; slot_hours[k] = total observed hours in slot k."""
    cnt = np.bincount(slot_of_event, minlength=48).astype(float)
    rate = cnt / np.maximum(slot_hours, 1e-9)
    mean_rate = cnt.sum() / slot_hours.sum()
    return np.maximum(rate / mean_rate, 1e-3)


class Seasonal:
    """Piecewise-constant intensity multiplier over a 48-slot (weekday/weekend x hour) cycle, time in hours from t0."""
    def __init__(self, t0, T, s):
        self.t0, self.T, self.s = t0, T, s
        grid = np.arange(0, int(np.ceil(T)) + 1)
        idx = t0 + np.array(grid, dtype="timedelta64[h]")
        import pandas as pd
        self.slot = profile_slots(pd.DatetimeIndex(idx))
        self.cum = np.concatenate([[0.0], np.cumsum(s[self.slot])])   # integral of s on hour grid
        self.grid = grid

    def at(self, th):
        return self.s[self.slot[np.minimum(np.floor(th).astype(int), len(self.slot) - 1)]]

    def integral(self, th):
        return np.interp(th, np.arange(len(self.cum)), self.cum)


def loglik(params, th, seas, T):
    mu0, alpha, beta = np.exp(params[0]), 1 / (1 + np.exp(-params[1])), np.exp(params[2])
    s_i = seas.at(th)
    A = np.zeros(len(th))
    for i in range(1, len(th)):
        A[i] = np.exp(-beta * (th[i] - th[i - 1])) * (A[i - 1] + 1.0)
    lam = mu0 * s_i + alpha * beta * A
    return np.sum(np.log(lam)) - mu0 * seas.integral(T) - alpha * np.sum(1 - np.exp(-beta * (T - th)))


def fit_hawkes(th, seas, T, fix_alpha_zero=False, starts=None):
    """MLE of (mu0, alpha, beta). Returns dict with params and loglik. alpha=0 gives the NHPP."""
    n = len(th)
    mu_hat = n / seas.integral(T)
    if fix_alpha_zero:
        return {"mu0": mu_hat, "alpha": 0.0, "beta": np.nan, "ll": float(np.sum(np.log(mu_hat * seas.at(th))) - n)}
    best = None
    for b0 in (0.05, 0.5, 5.0) if starts is None else starts:
        x0 = np.array([np.log(mu_hat * 0.8), -1.0, np.log(b0)])
        r = optimize.minimize(lambda p: -loglik(p, th, seas, T), x0, method="L-BFGS-B",
                              bounds=[(-20, 5), (-12, 12), (np.log(1e-3), np.log(1e3))])
        if best is None or r.fun < best.fun:
            best = r
    p = best.x
    return {"mu0": float(np.exp(p[0])), "alpha": float(1 / (1 + np.exp(-p[1]))), "beta": float(np.exp(p[2])), "ll": float(-best.fun)}


def simulate_nhpp(mu0, seas, T, rng):
    """Thinning simulation of the seasonal NHPP on [0, T] hours."""
    smax = seas.s.max()
    n = rng.poisson(mu0 * smax * T)
    t = np.sort(rng.random(n) * T)
    keep = rng.random(n) < seas.at(t) / smax
    return t[keep]


def hawkes_test(th, seas, T, n_boot=200, rng=None):
    """Self-excitation test: LR of Hawkes vs seasonal NHPP, with a parametric-bootstrap p-value under the NHPP null."""
    rng = rng or np.random.default_rng(0)
    h = fit_hawkes(th, seas, T)
    n0 = fit_hawkes(th, seas, T, fix_alpha_zero=True)
    lr = 2 * (h["ll"] - n0["ll"])
    sims = []
    for _ in range(n_boot):
        ts = simulate_nhpp(n0["mu0"], seas, T, rng)
        if len(ts) < 5:
            continue
        hb = fit_hawkes(ts, seas, T, starts=(0.5,))
        nb = fit_hawkes(ts, seas, T, fix_alpha_zero=True)
        sims.append(2 * (hb["ll"] - nb["ll"]))
    sims = np.array(sims)
    aic = {"nhpp": -2 * n0["ll"] + 2 * 1, "hawkes": -2 * h["ll"] + 2 * 3}
    # time-rescaling residuals under the Hawkes fit
    beta, alpha, mu0 = h["beta"], h["alpha"], h["mu0"]
    comp = mu0 * seas.integral(th)
    ex = np.zeros(len(th)); A = 0.0
    cum_ex = np.zeros(len(th))
    for i in range(len(th)):
        cum_ex[i] = alpha * np.sum(1 - np.exp(-beta * (th[i] - th[:i]))) if i else 0.0
    Lam = comp + cum_ex
    g = np.diff(np.concatenate([[0.0], Lam])); g = g[g > 0]
    ks_h = stats.kstest(g, "expon", args=(0, 1.0)).pvalue
    Lam0 = mu0 * 0 + n0["mu0"] * seas.integral(th)
    g0 = np.diff(np.concatenate([[0.0], Lam0])); g0 = g0[g0 > 0]
    ks_0 = stats.kstest(g0, "expon", args=(0, 1.0)).pvalue
    return {"n": int(len(th)), "hawkes": h, "nhpp_mu0": n0["mu0"], "lr": float(lr), "bootstrap_p": float((np.sum(sims >= lr) + 1) / (len(sims) + 1)),
            "aic": aic, "ks_rescaled_p_nhpp": float(ks_0), "ks_rescaled_p_hawkes": float(ks_h),
            "mean_cluster_size": float(1 / (1 - h["alpha"])) if h["alpha"] < 1 else float("inf"),
            "excitation_halflife_hours": float(np.log(2) / h["beta"])}


# ------------------------------------------------------------------ compound Poisson: episodes of correlated failures
def episodes_from_minutes(fail_minute_counts, req_minute_counts, rate_thr=0.2, min_fail=5, merge_gap=10):
    """Detect outage-like episodes: minutes with failure share > rate_thr and >= min_fail failures; merge runs separated by <= merge_gap minutes.
    Returns arrays (start_minute, end_minute, failures)."""
    share = np.where(req_minute_counts > 0, fail_minute_counts / np.maximum(req_minute_counts, 1), 0.0)
    hot = np.where((share > rate_thr) & (fail_minute_counts >= min_fail))[0]
    if len(hot) == 0:
        return np.array([]), np.array([]), np.array([])
    new = np.concatenate([[True], np.diff(hot) > merge_gap])
    gid = np.cumsum(new) - 1
    starts = np.array([hot[gid == g].min() for g in range(gid[-1] + 1)])
    ends = np.array([hot[gid == g].max() for g in range(gid[-1] + 1)])
    sizes = np.array([fail_minute_counts[s:e + 1].sum() for s, e in zip(starts, ends)])
    return starts, ends, sizes


def hill_tail_index(x, k=None):
    x = np.sort(np.asarray(x, float))[::-1]
    k = k or max(5, int(0.2 * len(x)))
    return float(1.0 / np.mean(np.log(x[:k] / x[k])))


# ------------------------------------------------------------------ superposition simulator
def simulate_typed_days(days, classes, rng):
    """classes: list of dict(kind='poisson'|'negbin'|'hawkes_days'|'compound', params). Returns array days x classes of daily event counts."""
    out = np.zeros((days, len(classes)))
    for j, c in enumerate(classes):
        if c["kind"] == "poisson":
            out[:, j] = rng.poisson(c["lam"], days)
        elif c["kind"] == "negbin":          # Gamma-mixed Poisson: daily multiplier with CV c
            m = rng.gamma(1 / c["cv"] ** 2, c["cv"] ** 2, days)
            out[:, j] = rng.poisson(c["lam"] * m)
        elif c["kind"] == "hawkes_days":     # cluster (Hawkes branching) process: Poisson parents x geometric cluster sizes
            parents = rng.poisson(c["lam"] * (1 - c["alpha"]), days)
            out[:, j] = [np.sum(rng.geometric(1 - c["alpha"], p)) if p else 0 for p in parents]
        elif c["kind"] == "compound":        # episodes (Poisson) x heavy-tailed sizes (lognormal)
            ep = rng.poisson(c["lam"], days)
            out[:, j] = [np.sum(np.ceil(rng.lognormal(c["mu"], c["sigma"], e))) if e else 0 for e in ep]
    return out


def nb_counts(lam, phi, days, rng):
    """Daily counts with mean lam and dispersion index phi = Var/mean (negative binomial; Poisson if phi <= 1)."""
    if phi <= 1.0 + 1e-9:
        return rng.poisson(lam, days)
    r = lam / (phi - 1.0)
    return rng.negative_binomial(r, r / (r + lam), days)


def typed_capacity(classes, alpha=0.95, days=400000, seed=0):
    """classes: dict name -> (lam, phi). Compare the 95% daily capacity of the superposition under (a) one Poisson on the total,
    (b) independent class-specific negative binomials, and report how often (a)'s plan is exceeded under (b)."""
    rng = np.random.default_rng(seed)
    tot = sum(l for l, _ in classes.values())
    typed = sum(nb_counts(l, p, days, rng) for l, p in classes.values())
    k_naive = int(stats.poisson.ppf(alpha, tot))
    k_typed = int(np.quantile(typed, alpha, method="higher"))
    var_tot = sum(l * p for l, p in classes.values())
    return {"lambda_total": tot, "k_naive_poisson": k_naive, "k_typed": k_typed,
            "naive_plan_exceeded_share": float(np.mean(typed > k_naive)), "target": 1 - alpha,
            "effective_dispersion": float(var_tot / tot), "k_normal_approx": float(tot + stats.norm.ppf(alpha) * np.sqrt(var_tot))}
