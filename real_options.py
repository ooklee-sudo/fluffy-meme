"""Numerical analysis for "Retrain, Transfer, or Wait? A Real Options Model of AI Asset Maintenance After Platform Upgrades" (Section 6).

Implements Propositions 1-4:
  - beta: root > 1 of Q(beta) = 0.5 sigma^2 beta (beta - 1) + g beta - (rho + mu)      (eq. 2)
  - k(R) = (1 - R) / (rho + mu - g)                                                   (eq. 1)
  - v*(R) = beta / (beta - 1) * C_N / k(R)                                             (eq. 3)
  - F(v) = (k v* - C_N) (v / v*)^beta for v < v*
  - W_j(v) = C_j + k_j v - F_j(v) for v < v*_j, else C_j + C_N                          (Prop. 4)
  - Gamma(R_A, R_C) = sup_v [min{W_C(v), C_N} - (k_A v - F_A(v))]                      (eq. 6)

Usage:
  python real_options.py                      # paper tables (Sections 6.2, 6.3)
  python real_options.py --mc                 # + Monte Carlo check of Proposition 1
  python real_options.py --recovery results/act_llama.json   # use measured R_C, R_A, C_A
"""
import argparse
import json
import math
from dataclasses import dataclass, replace

import numpy as np
from scipy.optimize import brentq, minimize_scalar


@dataclass(frozen=True)
class Params:
    rho: float = 0.10   # discount rate per year
    mu: float = 2.0     # upgrade intensity per year
    g: float = 0.20     # value growth
    sigma: float = 0.40  # value volatility
    C_N: float = 1.0    # retraining cost
    C_A: float = 0.05   # ACT cost

    def __post_init__(self):
        if not self.rho + self.mu > self.g:
            raise ValueError("A5 requires rho + mu > g")


def beta(p: Params) -> float:
    a = 0.5 * p.sigma ** 2
    if a == 0:  # deterministic value: Q is linear
        return (p.rho + p.mu) / p.g if p.g > 0 else math.inf
    b = p.g - a
    c = -(p.rho + p.mu)
    return (-b + math.sqrt(b * b - 4 * a * c)) / (2 * a)


def k(R: float, p: Params) -> float:
    return (1.0 - R) / (p.rho + p.mu - p.g)


def v_star(R: float, p: Params) -> float:
    b = beta(p)
    return b / (b - 1.0) * p.C_N / k(R, p)


def option_value(v, R: float, p: Params):
    """F(v): value of the right to retrain, operating at recovery R."""
    v = np.asarray(v, dtype=float)
    vs, kk, b = v_star(R, p), k(R, p), beta(p)
    return np.where(v < vs, (kk * vs - p.C_N) * (v / vs) ** b, kk * v - p.C_N)


def W(v, R: float, C: float, p: Params):
    """Expected total cost of 'transfer with (R, C), keep the retraining option'."""
    v = np.asarray(v, dtype=float)
    kk = k(R, p)
    return np.where(v < v_star(R, p), C + kk * v - option_value(v, R, p), C + p.C_N)


def policy_costs(v, R_C: float, R_A: float, p: Params):
    return {"copy": W(v, R_C, 0.0, p), "act": W(v, R_A, p.C_A, p),
            "retrain": np.full_like(np.asarray(v, float), p.C_N)}


def gamma(R_A: float, R_C: float, p: Params) -> float:
    """Eq. 6: max cost worth paying for a transfer method with recovery R_A."""
    def gap(logv):
        v = math.exp(logv)
        return -(min(float(W(v, R_C, 0.0, p)), p.C_N)
                 - (k(R_A, p) * v - float(option_value(v, R_A, p))))
    hi = math.log(v_star(R_A, p) * 2)
    grid = np.linspace(hi - 12, hi, 4000)
    i = int(np.argmin([gap(x) for x in grid]))
    res = minimize_scalar(gap, bounds=(grid[max(i - 1, 0)], grid[min(i + 1, len(grid) - 1)]),
                          method="bounded", options={"xatol": 1e-10})
    return -res.fun


def act_region(R_C: float, R_A: float, p: Params):
    """Return (lo, hi): ACT is optimal for lo <= v < hi; None if the region is empty."""
    def diff(v):  # < 0 where ACT beats the better of copy and retrain-now
        return float(W(v, R_A, p.C_A, p)) - min(float(W(v, R_C, 0.0, p)), p.C_N)
    vs = np.geomspace(1e-4, v_star(R_A, p) * 1.5, 20000)
    d = np.array([diff(v) for v in vs])
    idx = np.where(d < 0)[0]
    if len(idx) == 0:
        return None
    i0, i1 = idx[0], idx[-1]
    lo = brentq(diff, vs[i0 - 1], vs[i0]) if i0 > 0 else vs[0]
    hi = brentq(diff, vs[i1], vs[i1 + 1]) if i1 + 1 < len(vs) else math.inf
    return lo, hi


def mc_check(R: float, p: Params, v0: float, n: int = 200_000, dt: float = 1 / 365, seed: int = 0):
    """Monte Carlo of the threshold policy: loss flow until retrain or upgrade, plus retrain cost.

    Should match W(v0, R, 0) = k v0 - F(v0) (without transfer cost)."""
    rng = np.random.default_rng(seed)
    vs = v_star(R, p)
    tau = rng.exponential(1 / p.mu, n)
    v = np.full(n, v0)
    alive = np.ones(n, bool)
    cost = np.zeros(n)
    t = 0.0
    drift = (p.g - 0.5 * p.sigma ** 2) * dt
    while alive.any() and t < 20:
        hit = alive & (v >= vs)
        cost[hit] += math.exp(-p.rho * t) * p.C_N
        alive &= ~hit
        alive &= tau > t
        cost[alive] += math.exp(-p.rho * t) * v[alive] * (1 - R) * dt
        v[alive] *= np.exp(drift + p.sigma * math.sqrt(dt) * rng.standard_normal(alive.sum()))
        t += dt
    return cost.mean(), cost.std() / math.sqrt(n)


def table_62(recov, p: Params):
    print("\n== Section 6.2: expected cost by policy ==")
    print(f"beta = {beta(p):.2f}, beta/(beta-1) = {beta(p) / (beta(p) - 1):.2f}")
    w = max(6, *(len(n) for n in recov))
    hdr = f"{'drift':>{w}} {'R_C':>6} {'R_A':>6} {'v*_C':>8} {'v*_A':>8} {'copy opt':>12} {'ACT opt':>20} {'retrain opt':>12} {'Gamma':>6}"
    print(hdr)
    rows = []
    for name, (R_C, R_A) in recov.items():
        reg = act_region(R_C, R_A, p)
        G = gamma(R_A, R_C, p)
        lo, hi = reg if reg else (float("nan"), float("nan"))
        cols = (f"{'v < %.2f' % lo:>12} {'%.2f <= v < %.2f' % (lo, hi):>20} {'v >= %.2f' % hi:>12}" if reg else
                f"{'-':>12} {'never (C_A >= Gamma)':>20} {'v >= %.2f' % v_star(R_C, p):>12}")
        print(f"{name:>{w}} {R_C:6.3f} {R_A:6.3f} {v_star(R_C, p):8.2f} {v_star(R_A, p):8.2f} {cols} {G:6.2f}")
        rows.append(dict(drift=name, R_C=R_C, R_A=R_A, v_star_copy=v_star(R_C, p),
                         v_star_act=v_star(R_A, p), act_lo=lo, act_hi=hi, gamma=G))
    return rows


def table_63(R_C, R_A, p: Params, label="0.8"):
    print(f"\n== Section 6.3: effect of upgrade frequency (drift {label}) ==")
    print(f"{'mu':>5} {'months':>7} {'v*_C':>8} {'v*_A':>8}")
    for mu in (0.5, 1, 2, 4):
        q = replace(p, mu=mu)
        print(f"{mu:5g} {12 / mu:7.0f} {v_star(R_C, q):8.2f} {v_star(R_A, q):8.2f}")
    print("sigma sensitivity of v*_A: " + ", ".join(
        f"sigma={s}: {v_star(R_A, replace(p, sigma=s)):.2f}" for s in (0.2, 0.4, 0.6)))


def plot(R_C, R_A, p: Params, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    v = np.geomspace(0.05, 20, 600)
    c = policy_costs(v, R_C, R_A, p)
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(v, c["copy"], label=f"Copy (R={R_C:.3f})")
    ax.plot(v, c["act"], label=f"ACT (R={R_A:.3f}, C={p.C_A})")
    ax.plot(v, c["retrain"], "--", label="Retrain now")
    reg = act_region(R_C, R_A, p)
    if reg:
        ax.axvspan(*reg, alpha=0.08, color="C1")
    ax.set_xscale("log")
    ax.set_xlabel("Annual adapter value v (multiples of C_N)")
    ax.set_ylabel("Expected cost per epoch (multiples of C_N)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    print(f"\nsaved {path}")


def main():
    ap = argparse.ArgumentParser()
    for f in ("rho", "mu", "g", "sigma", "C_N", "C_A"):
        ap.add_argument(f"--{f}", type=float, default=getattr(Params, f))
    ap.add_argument("--recovery", help="JSON from act_toy.py / act_llama.py with R_C, R_A (and optional C_A_over_C_N)")
    ap.add_argument("--focus", help="drift/pair label used for the sensitivity tables and the Monte Carlo check")
    ap.add_argument("--mc", action="store_true", help="Monte Carlo check of Proposition 1")
    ap.add_argument("--plot", default="results/policy_costs.png")
    ap.add_argument("--out", default="results/real_options.json")
    a = ap.parse_args()
    p = Params(a.rho, a.mu, a.g, a.sigma, a.C_N, a.C_A)

    recov = {"0.8": (0.489319, 0.691576), "0.3": (0.955040, 0.974928)}  # Section 5.2 toy values (act_toy.py)
    if a.recovery:
        d = json.load(open(a.recovery))
        clip = lambda R: min(R, 0.999)  # measured R can reach or exceed 1 (noise); the model needs R < 1
        recov = {str(r["drift"]): (clip(r["R_C"]), clip(r["R_A"])) for r in d["recovery"]}
        if any(max(r["R_C"], r["R_A"]) >= 0.999 for r in d["recovery"]):
            print("note: recovery >= 0.999 clipped to 0.999")
        if "C_A_over_C_N" in d:
            p = replace(p, C_A=d["C_A_over_C_N"] * p.C_N)
            print(f"using measured C_A/C_N = {p.C_A / p.C_N:.3f}")

    rows = table_62(recov, p)
    label = a.focus if a.focus in recov else ("0.8" if "0.8" in recov else next(iter(recov)))
    R_C, R_A = recov[label]
    table_63(R_C, R_A, p, label)

    if a.mc:
        print(f"\n== Monte Carlo check of Proposition 1 (copy, drift {label}) ==")
        for v0 in (0.5, 2.0, 4.0):
            m, se = mc_check(R_C, p, v0)
            print(f"v0={v0}: MC={m:.4f} +- {se:.4f}   closed form W={float(W(v0, R_C, 0.0, p)):.4f}")

    import os
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump({"params": p.__dict__, "beta": beta(p), "table_6_2": rows}, open(a.out, "w"), indent=2)
    plot(R_C, R_A, p, a.plot)


if __name__ == "__main__":
    main()
