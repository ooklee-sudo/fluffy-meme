"""When to retrain an LLM: model error counts in production logs as an NHPP.

Model
-----
Logs are daily bins. Day i (age t_i days since the last retrain) has n_i requests
and y_i errors (hallucination flags, thumbs-down, failed evals, ...).

    y_i ~ Poisson(n_i * rho(t_i))          rho = error rate per request

Two NHPP intensity shapes, both Poisson GLMs with offset log(n_i):
    loglinear (Cox-Lewis):   log rho(t) = a + b t
    power     (Crow-AMSAA):  log rho(t) = a + b log t
b > 0 means the model is degrading. The shape with lower AIC is used.
Overdispersion is handled quasi-Poisson style: standard errors are scaled by
phi = Pearson chi2 / df.

Decision rule
-------------
Retraining costs C_r, each error costs C_e, retraining resets the error rate.
With expected daily traffic n, lambda(t) = n rho(t) and Lambda(T) = int_0^T lambda.
The long-run cost per day of retraining every T days is

    g(T) = (C_r + C_e Lambda(T)) / T

and its minimum T* solves  T lambda(T) - Lambda(T) = C_r / C_e.
(power shape: T* = [C_r (b+1) / (C_e n e^a b)]^(1/(b+1)).)

Online policy: each day, refit on the data since the last retrain. Retrain when
the trend is significant (one-sided Wald test on b) and the current age >= T*.

Usage
-----
    python nhpp_retrain.py                         # simulation study + figures
    python nhpp_retrain.py --seeds 10 --days 365   # quicker
    python nhpp_retrain.py --csv logs.csv --cr 5000 --ce 1
        CSV columns: requests, errors and optionally retrained (1 on the first day
        after a retrain). Prints the fit, T*, and whether to retrain today.
"""
import argparse
import csv
import json
import math
import os
from dataclasses import dataclass

import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm

SHAPES = ("loglinear", "power")


# ---------------------------------------------------------------------------
# Fitting
# ---------------------------------------------------------------------------
@dataclass
class Fit:
    shape: str
    a: float
    b: float
    cov: np.ndarray   # 2x2, already scaled by phi
    phi: float        # dispersion (1 = Poisson)
    aic: float
    n_days: int

    @property
    def z(self) -> float:
        return self.b / math.sqrt(self.cov[1, 1])

    @property
    def p_trend(self) -> float:
        """One-sided p-value for H0: b <= 0 (no degradation)."""
        return float(norm.sf(self.z))


def _feature(t, shape):
    t = np.asarray(t, dtype=float)
    return t if shape == "loglinear" else np.log(t)


def fit_glm(t, n, y, shape: str) -> Fit:
    """Poisson GLM  log E[y] = log n + a + b f(t), fitted by Newton-Raphson."""
    t, n, y = (np.asarray(v, dtype=float) for v in (t, n, y))
    X = np.column_stack([np.ones_like(t), _feature(t, shape)])
    off = np.log(n)
    w = np.array([math.log(max(y.sum(), 0.5) / n.sum()), 0.0])
    for _ in range(100):
        mu = np.exp(off + X @ w)
        H = X.T @ (X * mu[:, None])
        step = np.linalg.solve(H, X.T @ (y - mu))
        w = w + step
        if np.max(np.abs(step)) < 1e-10:
            break
    mu = np.exp(off + X @ w)
    H = X.T @ (X * mu[:, None])
    df = max(len(y) - 2, 1)
    phi = max(float(np.sum((y - mu) ** 2 / mu) / df), 1.0)
    ll = float(np.sum(y * np.log(np.where(y > 0, mu, 1.0)) - mu))  # up to a constant
    return Fit(shape, float(w[0]), float(w[1]), np.linalg.inv(H) * phi, phi,
               2 * 2 - 2 * ll, len(y))


def fit_best(t, n, y) -> Fit:
    fits = [fit_glm(t, n, y, s) for s in SHAPES]
    return min(fits, key=lambda f: f.aic)


# ---------------------------------------------------------------------------
# Intensity and optimal retraining age
# ---------------------------------------------------------------------------
def rate(t, shape, a, b):
    """Error rate per request at age t."""
    return np.exp(a + b * _feature(t, shape))


def cum_errors(T, shape, a, b, traffic):
    """Lambda(T): expected errors in the first T days after a retrain."""
    if shape == "loglinear":
        return traffic * math.exp(a) * (T if abs(b) < 1e-12 else math.expm1(b * T) / b)
    return traffic * math.exp(a) * T ** (b + 1) / (b + 1)


def t_star(shape, a, b, traffic, c_r, c_e, t_max=1e4) -> float:
    """Age that minimises the cost per day (C_r + C_e Lambda(T)) / T."""
    if b <= 0:
        return math.inf
    k = c_r / c_e
    if shape == "power":
        return (k * (b + 1) / (traffic * math.exp(a) * b)) ** (1 / (b + 1))

    def h(T):
        return T * traffic * rate(T, shape, a, b) - cum_errors(T, shape, a, b, traffic) - k

    hi = 1.0
    while h(hi) < 0:  # h is increasing when b > 0; double until it crosses zero
        hi *= 2
        if hi > t_max:
            return math.inf
    return brentq(h, 1e-9, hi)


def cost_rate(T, shape, a, b, traffic, c_r, c_e):
    return (c_r + c_e * cum_errors(T, shape, a, b, traffic)) / T


def t_star_interval(fit: Fit, traffic, c_r, c_e, level=0.8, draws=400, rng=None):
    """Parametric-bootstrap interval for T* from the asymptotic normal of (a, b)."""
    rng = rng or np.random.default_rng(0)
    ws = rng.multivariate_normal([fit.a, fit.b], fit.cov, size=draws)
    ts = np.array([t_star(fit.shape, a, b, traffic, c_r, c_e) for a, b in ws])
    ts.sort()  # may contain inf (no degradation in that draw); np.quantile would give nan
    lo = ts[int((1 - level) / 2 * (draws - 1))]
    hi = ts[int((1 + level) / 2 * (draws - 1))]
    return float(lo), float(hi)


# ---------------------------------------------------------------------------
# Online policy
# ---------------------------------------------------------------------------
@dataclass
class NHPPPolicy:
    c_r: float
    c_e: float
    min_days: int = 7        # don't decide before this many days of data
    alpha: float = 0.05      # trend test level
    max_age: float = 365.0   # safety cap
    traffic_window: int = 28

    def decide(self, n_hist, y_hist):
        """Data since the last retrain (day 1..age). Returns (retrain?, info)."""
        age = len(y_hist)
        if age >= self.max_age:
            return True, {"reason": "max_age"}
        if age < self.min_days:
            return False, {"reason": "warmup"}
        t = np.arange(age) + 0.5
        fit = fit_best(t, n_hist, y_hist)
        traffic = float(np.mean(n_hist[-self.traffic_window:]))
        ts = t_star(fit.shape, fit.a, fit.b, traffic, self.c_r, self.c_e)
        info = {"shape": fit.shape, "b": fit.b, "p": fit.p_trend, "phi": fit.phi, "t_star": ts}
        if fit.p_trend > self.alpha:
            return False, {**info, "reason": "no_trend"}
        return age >= ts, {**info, "reason": "t_star"}


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
@dataclass
class World:
    """Ground truth: rho(t) = rho0 (1 + (t / tau)^k); tau is redrawn at each retrain."""
    traffic: float = 20000.0
    rho0: float = 0.01
    k: float = 1.5
    tau_median: float = 60.0
    tau_sd_log: float = 0.4
    overdisp: float = 50.0   # gamma shape of day-level rate noise (inf = pure Poisson)

    def true_rate(self, t, tau):
        return self.rho0 * (1 + (np.asarray(t, float) / tau) ** self.k)

    def true_cum(self, T, tau):
        return self.traffic * self.rho0 * (T + tau * (T / tau) ** (self.k + 1) / (self.k + 1))

    def oracle_t_star(self, tau, c_r, c_e):
        def h(T):
            return T * self.traffic * self.true_rate(T, tau) - self.true_cum(T, tau) - c_r / c_e
        return brentq(h, 1e-6, 1e5)

    def global_g_star(self, c_r, c_e, draws=20000, seed=0):
        """Optimal long-run cost per day when tau is known at the start of each cycle.

        Per-cycle T*(tau) is not jointly optimal: the renewal-reward optimum retrains
        each cycle when the current cost rate c_e n rho_tau(t) reaches one shared
        level g*, where g* = E[C_r + C_e Lambda_tau(T)] / E[T] (fixed point).
        """
        rng = np.random.default_rng(seed)
        taus = self.tau_median * np.exp(self.tau_sd_log * rng.standard_normal(draws))
        base = c_e * self.traffic * self.rho0

        def ratio(g):
            T = taus * np.maximum(g / base - 1, 1e-12) ** (1 / self.k)
            return float(np.mean(c_r + c_e * self.true_cum(T, taus)) / np.mean(T))

        return brentq(lambda g: ratio(g) - g, base * (1 + 1e-9), base * 1e3)

    def oracle_age(self, tau, g_star, c_e):
        return tau * max(g_star / (c_e * self.traffic * self.rho0) - 1, 0) ** (1 / self.k)


def simulate(policy, world: World, days, c_r, c_e, seed):
    """Run one horizon. policy(n_hist, y_hist, tau) -> bool. Returns cost, retrains, trace."""
    rng = np.random.default_rng(seed)
    tau = world.tau_median * math.exp(world.tau_sd_log * rng.standard_normal())
    n_hist, y_hist = [], []
    errors, retrains = 0, 0
    trace = []
    for d in range(days):
        age = len(y_hist) + 0.5
        n = int(world.traffic * (1 + 0.2 * math.sin(2 * math.pi * d / 7)) * rng.lognormal(0, 0.05))
        lam = n * float(world.true_rate(age, tau))
        if math.isfinite(world.overdisp):
            lam *= rng.gamma(world.overdisp, 1 / world.overdisp)
        y = int(rng.poisson(lam))
        n_hist.append(n)
        y_hist.append(y)
        errors += y
        trace.append((d, age, n, y, tau))
        if policy(np.array(n_hist), np.array(y_hist), tau):
            retrains += 1
            n_hist, y_hist = [], []
            tau = world.tau_median * math.exp(world.tau_sd_log * rng.standard_normal())
    return c_e * errors + c_r * retrains, retrains, errors, trace


def make_policies(world, c_r, c_e):
    nhpp = NHPPPolicy(c_r, c_e)
    g_star = world.global_g_star(c_r, c_e)
    pols = {
        "NHPP (proposed)": lambda n, y, tau: nhpp.decide(n, y)[0],
        "Oracle": lambda n, y, tau: len(y) >= world.oracle_age(tau, g_star, c_e),
        "Per-cycle T*": lambda n, y, tau: len(y) >= world.oracle_t_star(tau, c_r, c_e),
    }
    for T in (30, 60, 90, 180):
        pols[f"Fixed {T}d"] = (lambda T: lambda n, y, tau: len(y) >= T)(T)

    def threshold(n, y, tau, ratio=1.5):
        # Retrain when the 7-day error rate exceeds 1.5x the first week's.
        if len(y) < 14:
            return False
        base = y[:7].sum() / n[:7].sum()
        return y[-7:].sum() / n[-7:].sum() > ratio * base

    pols["Threshold 1.5x"] = threshold
    pols["Never"] = lambda n, y, tau: False
    return pols


def run_study(args):
    world = World()
    c_r, c_e = args.cr, args.ce
    pols = make_policies(world, c_r, c_e)
    out = {}
    for name, pol in pols.items():
        costs, rets = [], []
        for s in range(args.seeds):
            c, r, _, _ = simulate(pol, world, args.days, c_r, c_e, seed=1000 + s)
            costs.append(c / args.days)
            rets.append(r)
        out[name] = {"cost_per_day_mean": float(np.mean(costs)),
                     "cost_per_day_se": float(np.std(costs, ddof=1) / math.sqrt(len(costs))),
                     "retrains_mean": float(np.mean(rets))}
    best = out["Oracle"]["cost_per_day_mean"]
    for v in out.values():
        v["regret_vs_oracle_pct"] = 100 * (v["cost_per_day_mean"] / best - 1)

    print(f"\nSimulation: {args.seeds} seeds x {args.days} days, C_r={c_r:g}, C_e={c_e:g}, "
          f"tau median={world.tau_median:g}d (oracle T* at median tau = "
          f"{world.oracle_t_star(world.tau_median, c_r, c_e):.1f}d)")
    print(f"{'policy':<18}{'cost/day':>12}{'± se':>8}{'retrains':>10}{'vs oracle':>11}")
    for name, v in sorted(out.items(), key=lambda kv: kv[1]["cost_per_day_mean"]):
        print(f"{name:<18}{v['cost_per_day_mean']:>12.1f}{v['cost_per_day_se']:>8.1f}"
              f"{v['retrains_mean']:>10.1f}{v['regret_vs_oracle_pct']:>10.1f}%")

    fit_check = shape_recovery(world, c_r, c_e)
    print("\nOne cycle, fitted after 30 days of data (tau = 60):")
    for k_, v in fit_check.items():
        print(f"  {k_}: {v}")

    os.makedirs("results", exist_ok=True)
    with open("results/nhpp_retrain.json", "w") as f:
        json.dump({"params": {"c_r": c_r, "c_e": c_e, "days": args.days, "seeds": args.seeds,
                              "world": world.__dict__},
                   "policies": out, "fit_check": fit_check}, f, indent=2)
    if not args.no_plot:
        plot(world, c_r, c_e, out)
    print("\nWrote results/nhpp_retrain.json" + ("" if args.no_plot else ", results/nhpp_retrain.png"))


def shape_recovery(world, c_r, c_e, days=30, seed=7):
    rng = np.random.default_rng(seed)
    tau = world.tau_median
    t = np.arange(days) + 0.5
    n = np.full(days, int(world.traffic))
    lam = n * world.true_rate(t, tau) * rng.gamma(world.overdisp, 1 / world.overdisp, days)
    y = rng.poisson(lam)
    fit = fit_best(t, n, y)
    ts = t_star(fit.shape, fit.a, fit.b, world.traffic, c_r, c_e)
    lo, hi = t_star_interval(fit, world.traffic, c_r, c_e, rng=rng)
    return {"shape": fit.shape, "b": round(fit.b, 4), "trend_p": float(f"{fit.p_trend:.2g}"),
            "phi": round(fit.phi, 2), "t_star_hat": round(ts, 1),
            "t_star_80pct": [round(lo, 1), round(hi, 1)],
            "t_star_true": round(world.oracle_t_star(tau, c_r, c_e), 1)}


def plot(world, c_r, c_e, study):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(1, 3, figsize=(16, 4.5))

    # (a) one horizon under the NHPP policy
    nhpp = NHPPPolicy(c_r, c_e)
    tstars = []

    def pol(n, y, tau):
        r, info = nhpp.decide(n, y)
        tstars.append(info.get("t_star", np.nan) if info.get("reason") != "no_trend" else np.nan)
        return r

    _, _, _, tr = simulate(pol, world, 365, c_r, c_e, seed=1000)
    tr = np.array(tr)
    d, age, n, y = tr[:, 0], tr[:, 1], tr[:, 2], tr[:, 3]
    ax[0].plot(d, 1000 * y / n, ".", ms=3, color="#888", label="observed")
    ax[0].plot(d, 1000 * world.true_rate(age, tr[:, 4]), color="#1f77b4", label="true rate")
    for x in d[1:][age[1:] < age[:-1]]:
        ax[0].axvline(x, color="#d62728", lw=0.8, alpha=0.6)
    ax[0].set(title="(a) NHPP policy over one year (red = retrain)", xlabel="day",
              ylabel="errors per 1000 requests")
    ax[0].legend(loc="upper left")

    # (b) cost-rate curve and T*
    tau = world.tau_median
    T = np.linspace(5, 250, 300)
    g = (c_r + c_e * world.true_cum(T, tau)) / T
    ts = world.oracle_t_star(tau, c_r, c_e)
    ax[1].plot(T, g, color="#1f77b4")
    ax[1].axvline(ts, ls="--", color="k")
    ax[1].text(ts, g.max() * 0.97, f"  T* = {ts:.0f}d", va="top")
    ax[1].set(title=r"(b) cost per day $g(T)=(C_r+C_e\Lambda(T))/T$", xlabel="retrain every T days",
              ylabel="cost per day")

    # (c) policy comparison
    names = sorted(study, key=lambda k: study[k]["cost_per_day_mean"])
    names = [k for k in names if k != "Never"]
    m = [study[k]["cost_per_day_mean"] for k in names]
    se = [study[k]["cost_per_day_se"] for k in names]
    colors = ["#2ca02c" if k.startswith("NHPP") else "#7f7f7f" if k in ("Oracle", "Per-cycle T*")
              else "#aec7e8" for k in names]
    ax[2].barh(names[::-1], m[::-1], xerr=se[::-1], color=colors[::-1])
    ax[2].set_xlim(min(m) * 0.9, max(m) * 1.03)
    ax[2].set(title="(c) mean cost per day (lower is better)", xlabel="cost per day")

    fig.tight_layout()
    fig.savefig("results/nhpp_retrain.png", dpi=130)


# ---------------------------------------------------------------------------
# Real logs
# ---------------------------------------------------------------------------
def run_csv(args):
    with open(args.csv, newline="") as f:
        rows = list(csv.DictReader(f))
    n = np.array([float(r["requests"]) for r in rows])
    y = np.array([float(r["errors"]) for r in rows])
    start = 0
    if rows and "retrained" in rows[0]:
        marks = [i for i, r in enumerate(rows) if str(r["retrained"]).strip() in ("1", "true", "True")]
        start = marks[-1] if marks else 0
    n, y = n[start:], y[start:]
    print(f"{len(y)} days since the last retrain (rows {start}..{len(rows) - 1})")
    if len(y) < 3:
        print("Need at least 3 days of data.")
        return
    t = np.arange(len(y)) + 0.5
    traffic = float(np.mean(n[-28:]))
    for s in SHAPES:
        fit = fit_glm(t, n, y, s)
        print(f"  {s:<9}  a={fit.a:.4f}  b={fit.b:.4f}  trend p={fit.p_trend:.3g}  "
              f"phi={fit.phi:.2f}  AIC={fit.aic:.1f}")
    fit = fit_best(t, n, y)
    ts = t_star(fit.shape, fit.a, fit.b, traffic, args.cr, args.ce)
    lo, hi = t_star_interval(fit, traffic, args.cr, args.ce)
    print(f"Chosen shape: {fit.shape}. Expected traffic {traffic:.0f}/day.")
    print(f"T* = {ts:.1f} days (80% interval {lo:.1f}-{hi:.1f})")
    retrain, info = NHPPPolicy(args.cr, args.ce).decide(n, y)
    print(f"Decision today (age {len(y)}): {'RETRAIN' if retrain else 'keep'}  [{info['reason']}]")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", help="daily log CSV with columns requests, errors[, retrained]")
    ap.add_argument("--cr", type=float, default=5000.0, help="retraining cost (in units of C_e)")
    ap.add_argument("--ce", type=float, default=1.0, help="cost per error")
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--days", type=int, default=730)
    ap.add_argument("--no-plot", action="store_true")
    args = ap.parse_args()
    run_csv(args) if args.csv else run_study(args)


if __name__ == "__main__":
    main()
