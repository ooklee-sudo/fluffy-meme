"""Real options + NHPP: when to retrain if a new base model may arrive any day.

Combines nhpp_retrain.py (errors as an NHPP) with real_options.py (base-model
upgrades as a Poisson process with intensity mu).

Model (time in days)
--------------------
State: age t since the last reset. Error intensity lambda(t) = expected errors per
day at age t, increasing (fitted NHPP times traffic). Error cost c_e per error.
  - Retrain: pay C_r, age -> 0.                                   (firm's choice)
  - Upgrade: a new base model arrives at rate mu; the firm migrates, pays C_U,
    age -> 0.                                                       (exogenous)
Discount rate rho. Expected discounted cost from age t, V(t), solves on t < T

    rho V = c_e lambda(t) + V'(t) + mu (C_U + V(0) - V(t))
    V(T) = C_r + V(0)        (value matching)
    V'(T) = 0                (smooth pasting, optimal T)

With r = rho + mu and I_r(T) = int_0^T e^{-r s} c_e lambda(s) ds,

    V(0; T) = r [I_r(T) + mu C_U (1 - e^{-rT}) / r + e^{-rT} C_r] / (rho (1 - e^{-rT}))

and the optimal threshold satisfies

    c_e lambda(T*) = (rho + mu) C_r + rho V(0) - mu C_U.

As rho -> 0 and mu = 0 this is c_e lambda(T*) = g* (average-cost rule of
nhpp_retrain.py). The term mu C_r is the real option: a retrain is wasted when an
upgrade arrives soon after, so waiting is worth more when upgrades are frequent.

Usage
-----
    python ro_nhpp.py                       # tables, MC check, simulation, figure
    python ro_nhpp.py --mu 4 --cr 20000     # other parameters (mu per year)
    python ro_nhpp.py --csv logs.csv --mu 2 # real logs: fit NHPP, print T* with/without option
"""
import argparse
import csv
import json
import math
import os
from dataclasses import dataclass

import numpy as np
from scipy.special import gamma as G, gammainc

from nhpp_retrain import NHPPPolicy, World, fit_best

DAYS_PER_YEAR = 365.0


# ---------------------------------------------------------------------------
# Intensities with closed-form discounted integrals
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class PowerSum:
    """lambda(s) = sum_j c_j s^p_j  (p_j > -1)."""
    terms: tuple

    def __call__(self, s):
        s = np.asarray(s, float)
        return sum(c * s ** p for c, p in self.terms)

    def disc_int(self, T, r):
        """int_0^T e^{-r s} lambda(s) ds (vectorised in T)."""
        T = np.asarray(T, float)
        if r == 0:
            return sum(c * T ** (p + 1) / (p + 1) for c, p in self.terms)
        return sum(c * G(p + 1) * gammainc(p + 1, r * T) / r ** (p + 1) for c, p in self.terms)


@dataclass(frozen=True)
class Exponential:
    """lambda(s) = c e^{b s}."""
    c: float
    b: float

    def __call__(self, s):
        return self.c * np.exp(self.b * np.asarray(s, float))

    def disc_int(self, T, r):
        T = np.asarray(T, float)
        d = self.b - r
        if abs(d) < 1e-12:
            return self.c * T
        with np.errstate(over="ignore"):
            return self.c * np.expm1(d * T) / d


def intensity_from_fit(fit, traffic):
    """Errors per day from a nhpp_retrain.Fit (rate per request times traffic)."""
    c = traffic * math.exp(fit.a)
    return Exponential(c, fit.b) if fit.shape == "loglinear" else PowerSum(((c, fit.b),))


def intensity_true(world: World, tau):
    c = world.traffic * world.rho0
    return PowerSum(((c, 0.0), (c * tau ** -world.k, world.k)))


# ---------------------------------------------------------------------------
# Value function and optimal threshold
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Econ:
    c_r: float = 5000.0     # retraining cost
    c_u: float = 5000.0     # migration cost when a new base model arrives
    c_e: float = 1.0        # cost per error
    rho: float = 0.10 / DAYS_PER_YEAR
    mu: float = 2.0 / DAYS_PER_YEAR   # upgrades per day

    def with_mu(self, mu):
        return Econ(self.c_r, self.c_u, self.c_e, self.rho, mu)


def V0(T, lam, e: Econ):
    """Expected discounted cost from a fresh model under threshold T (T may be inf)."""
    T = np.asarray(T, float)
    r = e.rho + e.mu
    x = np.exp(-r * T)
    I = e.c_e * lam.disc_int(T, r)
    return r * (I + e.mu * e.c_u * (1 - x) / r + x * e.c_r) / (e.rho * (1 - x))


def optimal_T(lam, e: Econ, t_max=10 * DAYS_PER_YEAR):
    """Returns (T*, V0(T*)); T* = inf if never retraining (only upgrades) is best."""
    grid = np.geomspace(0.5, t_max, 600)
    v = V0(grid, lam, e)
    i = int(np.nanargmin(v))
    lo, hi = grid[max(i - 1, 0)], grid[min(i + 1, len(grid) - 1)]
    for _ in range(60):  # golden-section refine
        m1, m2 = lo + 0.382 * (hi - lo), lo + 0.618 * (hi - lo)
        if V0(m1, lam, e) < V0(m2, lam, e):
            hi = m2
        else:
            lo = m1
    T = 0.5 * (lo + hi)
    vT = float(V0(T, lam, e))
    if i == len(grid) - 1:
        v_inf = float(V0(np.inf, lam, e))
        if np.isfinite(v_inf) and v_inf <= vT:
            return math.inf, v_inf
    return float(T), vT


def smooth_pasting_gap(T, v0, lam, e: Econ):
    lhs = e.c_e * float(lam(T))
    rhs = (e.rho + e.mu) * e.c_r + e.rho * v0 - e.mu * e.c_u
    return lhs, rhs


def mc_value(T, lam, e: Econ, n=40000, horizon=30 * DAYS_PER_YEAR, seed=0):
    """Monte Carlo of V(0; T): exact upgrade times, expected error flow integrated."""
    rng = np.random.default_rng(seed)
    total = np.zeros(n)
    for j in range(n):
        t, cost = 0.0, 0.0
        while t < horizon:
            u = rng.exponential(1 / e.mu) if e.mu > 0 else math.inf
            d = math.exp(-e.rho * t)
            if u < T:
                cost += d * (e.c_e * float(lam.disc_int(u, e.rho)) + math.exp(-e.rho * u) * e.c_u)
                t += u
            else:
                cost += d * (e.c_e * float(lam.disc_int(T, e.rho)) + math.exp(-e.rho * T) * e.c_r)
                t += T
        total[j] = cost
    return float(total.mean()), float(total.std() / math.sqrt(n))


# ---------------------------------------------------------------------------
# Analyses
# ---------------------------------------------------------------------------
def table_mu(world, e: Econ, cr_list=(2000, 5000, 20000, 50000), mu_list=(0, 0.5, 1, 2, 4)):
    """T* and value of the waiting option by upgrade frequency (true intensity)."""
    lam = intensity_true(world, world.tau_median)
    rows = []
    print("\n== T* by upgrade frequency (tau = %g d) ==" % world.tau_median)
    print(f"{'C_r':>7}{'mu/yr':>7}{'T* (d)':>9}{'V0':>12}{'P(upgrade first)':>18}"
          f"{'myopic T*':>11}{'option value':>14}")
    for cr in cr_list:
        base = Econ(cr, e.c_u, e.c_e, e.rho, 0.0)
        T_my, _ = optimal_T(lam, base)
        for mu_y in mu_list:
            ee = base.with_mu(mu_y / DAYS_PER_YEAR)
            T, v = optimal_T(lam, ee)
            v_my = float(V0(T_my, lam, ee))  # ignore upgrades when choosing T
            p_up = 1 - math.exp(-ee.mu * T) if math.isfinite(T) else 1.0
            ov = 100 * (v_my - v) / v
            print(f"{cr:>7g}{mu_y:>7g}{T:>9.1f}{v:>12.0f}{p_up:>18.2f}{T_my:>11.1f}{ov:>13.2f}%")
            rows.append(dict(c_r=cr, mu_per_year=mu_y, T_star=T, V0=v, p_upgrade_first=p_up,
                             T_myopic=T_my, option_value_pct=ov))
    return rows


def check(world, e: Econ):
    # MC truncates at 30 years, so check at rho = 1/yr (truncation error e^-30).
    e = Econ(e.c_r, e.c_u, e.c_e, 1.0 / DAYS_PER_YEAR, e.mu)
    lam = intensity_true(world, world.tau_median)
    T, v = optimal_T(lam, e)
    lhs, rhs = smooth_pasting_gap(T, v, lam, e)
    m, se = mc_value(T, lam, e, n=4000)
    print(f"\n== Checks (C_r={e.c_r:g}, mu={e.mu * DAYS_PER_YEAR:g}/yr, rho=1/yr) ==")
    T_hi_cu, _ = optimal_T(lam, Econ(e.c_r, 10 * e.c_u, e.c_e, e.rho, e.mu))
    print(f"T* = {T:.2f} d; with C_U x10: {T_hi_cu:.2f} d (migration cost does not move T*)")
    print(f"smooth pasting: c_e lambda(T*) = {lhs:.2f}  vs  (rho+mu)C_r + rho V0 - mu C_U = {rhs:.2f}")
    print(f"V0 closed form = {v:.0f}   Monte Carlo = {m:.0f} ± {se:.0f}")
    return dict(T_star=T, V0=v, sp_lhs=lhs, sp_rhs=rhs, mc_mean=m, mc_se=se)


@dataclass
class ROPolicy:
    """Online: refit the NHPP on the current cycle, retrain when age >= T*(fit, mu)."""
    e: Econ
    min_days: int = 7
    alpha: float = 0.05
    traffic_window: int = 28

    def decide(self, n_hist, y_hist):
        age = len(y_hist)
        if age < self.min_days:
            return False
        t = np.arange(age) + 0.5
        fit = fit_best(t, n_hist, y_hist)
        if fit.p_trend > self.alpha:
            return False
        lam = intensity_from_fit(fit, float(np.mean(n_hist[-self.traffic_window:])))
        T, _ = optimal_T(lam, self.e)
        return age >= T


def simulate_up(policy, world: World, e: Econ, days, seed):
    """Like nhpp_retrain.simulate, plus base-model upgrades at rate mu (forced reset, cost C_U).

    Returns undiscounted cost per day (rho is tiny over the horizon)."""
    rng = np.random.default_rng(seed)
    up_rng = np.random.default_rng(seed + 10 ** 6)  # same upgrade dates across policies
    upgrades = set(np.cumsum(up_rng.exponential(1 / e.mu, 200)).astype(int)) if e.mu > 0 else set()
    tau = world.tau_median * math.exp(world.tau_sd_log * rng.standard_normal())
    n_hist, y_hist = [], []
    cost, n_ret, n_up = 0.0, 0, 0
    for d in range(days):
        age = len(y_hist) + 0.5
        n = int(world.traffic * (1 + 0.2 * math.sin(2 * math.pi * d / 7)) * rng.lognormal(0, 0.05))
        lam = n * float(world.true_rate(age, tau)) * rng.gamma(world.overdisp, 1 / world.overdisp)
        y = int(rng.poisson(lam))
        n_hist.append(n)
        y_hist.append(y)
        cost += e.c_e * y
        reset = False
        if d in upgrades:
            cost += e.c_u
            n_up += 1
            reset = True
        elif policy(np.array(n_hist), np.array(y_hist), tau):
            cost += e.c_r
            n_ret += 1
            reset = True
        if reset:
            n_hist, y_hist = [], []
            tau = world.tau_median * math.exp(world.tau_sd_log * rng.standard_normal())
    return cost / days, n_ret, n_up


def run_simulation(world, e: Econ, days, seeds):
    myopic_e = e.with_mu(0.0)
    avg = NHPPPolicy(e.c_r, e.c_e)
    ro, my = ROPolicy(e), ROPolicy(myopic_e)
    oracle_cache = {}

    def oracle(n, y, tau, ee=e):
        key = (tau, ee.mu)
        if key not in oracle_cache:
            oracle_cache[key] = optimal_T(intensity_true(world, tau), ee)[0]
        return len(y) >= oracle_cache[key]

    pols = {
        "RO-NHPP (proposed)": lambda n, y, tau: ro.decide(n, y),
        "Myopic NHPP (mu=0)": lambda n, y, tau: my.decide(n, y),
        "Avg-cost NHPP": lambda n, y, tau: avg.decide(n, y)[0],
        "Oracle RO (true lambda)": oracle,
        "Oracle myopic": lambda n, y, tau: oracle(n, y, tau, myopic_e),
        "Fixed 60d": lambda n, y, tau: len(y) >= 60,
    }
    out, per_seed = {}, {}
    for name, pol in pols.items():
        res = np.array([simulate_up(pol, world, e, days, 2000 + s) for s in range(seeds)])
        per_seed[name] = res[:, 0]
        out[name] = {"cost_per_day_mean": float(res[:, 0].mean()),
                     "cost_per_day_se": float(res[:, 0].std(ddof=1) / math.sqrt(seeds)),
                     "retrains_mean": float(res[:, 1].mean()),
                     "upgrades_mean": float(res[:, 2].mean())}
    ref = out["RO-NHPP (proposed)"]["cost_per_day_mean"]
    ref_s = per_seed["RO-NHPP (proposed)"]
    print(f"\n== Simulation with upgrades: {seeds} seeds x {days} d, mu={e.mu * DAYS_PER_YEAR:g}/yr, "
          f"C_r={e.c_r:g}, C_U={e.c_u:g} ==")
    print(f"{'policy':<25}{'cost/day':>10}{'± se':>7}{'retrains':>10}{'upgrades':>10}"
          f"{'vs RO-NHPP':>12}{'paired se':>11}")
    for name, v in out.items():
        diff = 100 * (per_seed[name] / ref_s - 1)
        v["vs_ro_nhpp_pct"] = float(diff.mean())
        v["vs_ro_nhpp_pct_se"] = float(diff.std(ddof=1) / math.sqrt(seeds)) if name != "RO-NHPP (proposed)" else 0.0
        print(f"{name:<25}{v['cost_per_day_mean']:>10.1f}{v['cost_per_day_se']:>7.1f}"
              f"{v['retrains_mean']:>10.1f}{v['upgrades_mean']:>10.1f}{v['vs_ro_nhpp_pct']:>11.1f}%"
              f"{v['vs_ro_nhpp_pct_se']:>10.1f}%")
    return out


def plot(world, e: Econ, rows, sim, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    lam = intensity_true(world, world.tau_median)
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.5))
    mus = np.linspace(0, 6, 61)
    for cr in sorted({r["c_r"] for r in rows}):
        base = Econ(cr, e.c_u, e.c_e, e.rho, 0.0)
        T_my, _ = optimal_T(lam, base)
        Ts, ovs = [], []
        for m in mus:
            ee = base.with_mu(m / DAYS_PER_YEAR)
            T, v = optimal_T(lam, ee)
            Ts.append(T)
            ovs.append(100 * (float(V0(T_my, lam, ee)) - v) / v)
        ax[0].plot(mus, Ts, label=f"C_r = {cr:g}")
        ax[1].plot(mus, ovs, label=f"C_r = {cr:g}")
    ax[0].set(title="(a) optimal retrain age T* vs upgrade rate", xlabel="base-model upgrades per year (mu)",
              ylabel="T* (days)")
    ax[1].set(title="(b) value of the waiting option", xlabel="base-model upgrades per year (mu)",
              ylabel="cost saved vs. ignoring upgrades (%)")
    for a in ax[:2]:
        a.legend()
        a.grid(alpha=0.3)
    names = list(sim)
    m = [sim[k]["cost_per_day_mean"] for k in names]
    se = [sim[k]["cost_per_day_se"] for k in names]
    colors = ["#2ca02c" if k.startswith("RO-NHPP") else "#7f7f7f" if k.startswith("Oracle") else "#aec7e8"
              for k in names]
    ax[2].barh(names[::-1], m[::-1], xerr=se[::-1], color=colors[::-1])
    ax[2].set_xlim(min(m) * 0.95, max(m) * 1.02)
    ax[2].set(title=f"(c) simulation, mu = {e.mu * DAYS_PER_YEAR:g}/yr (lower is better)",
              xlabel="cost per day")
    fig.tight_layout()
    fig.savefig(path, dpi=130)


def run_csv(args, e: Econ):
    with open(args.csv, newline="") as f:
        rows = list(csv.DictReader(f))
    start = 0
    if rows and "retrained" in rows[0]:
        marks = [i for i, r in enumerate(rows) if str(r["retrained"]).strip() in ("1", "true", "True")]
        start = marks[-1] if marks else 0
    n = np.array([float(r["requests"]) for r in rows[start:]])
    y = np.array([float(r["errors"]) for r in rows[start:]])
    if len(y) < 3:
        print("Need at least 3 days since the last retrain.")
        return
    fit = fit_best(np.arange(len(y)) + 0.5, n, y)
    lam = intensity_from_fit(fit, float(np.mean(n[-28:])))
    print(f"{len(y)} days since last reset. NHPP shape {fit.shape}, b={fit.b:.4f}, trend p={fit.p_trend:.3g}")
    T_my, _ = optimal_T(lam, e.with_mu(0.0))
    T, v = optimal_T(lam, e)
    print(f"T* ignoring upgrades: {T_my:.1f} d   T* with mu={e.mu * DAYS_PER_YEAR:g}/yr: {T:.1f} d")
    ok = fit.p_trend <= 0.05 and len(y) >= T
    print(f"Decision today: {'RETRAIN' if ok else 'keep'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cr", type=float, default=5000.0)
    ap.add_argument("--cu", type=float, default=5000.0, help="migration cost at a base-model upgrade")
    ap.add_argument("--ce", type=float, default=1.0)
    ap.add_argument("--rho", type=float, default=0.10, help="discount rate per year")
    ap.add_argument("--mu", type=float, default=4.0, help="base-model upgrades per year")
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--days", type=int, default=730)
    ap.add_argument("--csv")
    ap.add_argument("--no-plot", action="store_true")
    a = ap.parse_args()
    e = Econ(a.cr, a.cu, a.ce, a.rho / DAYS_PER_YEAR, a.mu / DAYS_PER_YEAR)
    if a.csv:
        return run_csv(a, e)

    world = World()
    rows = table_mu(world, e)
    chk = check(world, e)
    sim = run_simulation(world, e, a.days, a.seeds)
    os.makedirs("results", exist_ok=True)
    json.dump({"params": {**e.__dict__, "world": world.__dict__}, "table_mu": rows, "check": chk,
               "simulation": sim}, open("results/ro_nhpp.json", "w"), indent=2)
    if not a.no_plot:
        plot(world, e, rows, sim, "results/ro_nhpp.png")
    print("\nWrote results/ro_nhpp.json" + ("" if a.no_plot else ", results/ro_nhpp.png"))


if __name__ == "__main__":
    main()
