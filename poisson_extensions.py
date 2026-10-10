"""Beyond the Poisson-upgrade assumption: Monte Carlo extensions of real_options.py.

real_options.py assumes upgrades arrive as a Poisson process (exponential epoch length, rate mu) and the
adapter value v follows a GBM.  Here the threshold policy ("retrain once v >= theta") is simulated when

  A. epoch lengths are not exponential, with the mean fixed at 1/mu
       - hyperexponential, CV > 1  (clustered releases: bursts and long quiet spells; renewal proxy for Hawkes)
       - Erlang, CV < 1            (regular release cadence)
       - deterministic             (CV = 0)
  B. v gets compound-Poisson jumps (Merton jump-diffusion, drift compensated so E[v] still grows at g)

For each scenario it reports the cost of the Poisson-optimal thresholds v*_C, v*_A, the best threshold
found by simulation, the regret of using the Poisson one, and the ACT-optimal region of v.
One simulated X-path (log v / v0) serves every starting value v0, threshold and policy.

Usage:
  python poisson_extensions.py                 # defaults: toy drift-0.8 recovery, 30k paths
  python poisson_extensions.py --n 60000 --R_C 0.955 --R_A 0.975   # drift 0.3 values
"""
import argparse
import json
import math
import os
from dataclasses import replace

import numpy as np

from real_options import Params, W, act_region, v_star

BG = 0.5826  # Broadie-Glasserman discrete-monitoring barrier shift


def epoch_sampler(kind, mu, cv=None):
    m = 1.0 / mu
    if kind == "exp":
        return lambda rng, n: rng.exponential(m, n)
    if kind == "det":
        return lambda rng, n: np.full(n, m)
    if kind == "erlang":
        k = max(1, round(1.0 / cv ** 2))
        return lambda rng, n: rng.gamma(k, m / k, n)
    if kind == "hyper":  # balanced-means two-phase hyperexponential with the given CV
        c2 = cv ** 2
        p1 = 0.5 * (1 + math.sqrt((c2 - 1) / (c2 + 1)))
        l1, l2 = 2 * p1 / m, 2 * (1 - p1) / m

        def f(rng, n):
            fast = rng.random(n) < p1
            return np.where(fast, rng.exponential(1 / l1, n), rng.exponential(1 / l2, n))
        return f
    raise ValueError(kind)


def simulate(p: Params, sampler, barriers, n, dt, tmax, jumps=None, seed=0):
    """Simulate X = log(v_t / v_0) until the upgrade epoch ends.

    Returns, for each path and each (sorted) barrier b, the integral of disc*e^X dt accumulated before the
    barrier is first reached (Lhit), the discount factor at that time (Dhit; 0 = never reached before the
    upgrade) and the integral up to the upgrade (Lfin)."""
    rng = np.random.default_rng(seed)
    L = len(barriers)
    tau = sampler(rng, n)
    Lhit = np.zeros((n, L), np.float32)
    Dhit = np.zeros((n, L), np.float32)
    Lfin = np.zeros(n)
    lam_j, m_j, s_j = jumps if jumps else (0.0, 0.0, 0.0)
    comp = lam_j * (math.exp(m_j + 0.5 * s_j ** 2) - 1.0)  # compensator keeps E[v] growing at g
    drift = (p.g - comp - 0.5 * p.sigma ** 2) * dt
    vol = p.sigma * math.sqrt(dt)

    idx = np.arange(n)
    X = np.zeros(n)
    M = np.zeros(n)
    cum = np.zeros(n)
    ptr = np.zeros(n, np.int64)
    t = 0.0
    while len(idx) and t < tmax:
        disc = math.exp(-p.rho * t)
        newp = np.searchsorted(barriers, M, side="right")
        cnt = newp - ptr
        tot = int(cnt.sum())
        if tot:
            rows = np.repeat(np.arange(len(idx)), cnt)
            offs = np.arange(tot) - np.repeat(np.cumsum(cnt) - cnt, cnt)
            cols = np.repeat(ptr, cnt) + offs
            Lhit[idx[rows], cols] = cum[rows]
            Dhit[idx[rows], cols] = disc
        ptr = newp
        gone = (tau[idx] <= t) | (ptr >= L)
        if gone.any():
            Lfin[idx[gone]] = cum[gone]
            keep = ~gone
            idx, X, M, cum, ptr = idx[keep], X[keep], M[keep], cum[keep], ptr[keep]
            if not len(idx):
                break
        cum += disc * np.exp(X) * dt
        step = drift + vol * rng.standard_normal(len(idx))
        if lam_j:
            k = rng.poisson(lam_j * dt, len(idx))
            if k.any():
                step += k * m_j + np.sqrt(k) * s_j * rng.standard_normal(len(idx))
        X += step
        np.maximum(M, X, out=M)
        t += dt
    if len(idx):  # horizon reached
        Lfin[idx] = cum
    return Lhit, Dhit, Lfin


def cost_surface(Lhit, Dhit, Lfin, barriers, order, v0s, thetas, R, C_up, p):
    """Expected total cost C_up + loss + retrain for every (v0, theta); rows of Lhit are barrier-sorted."""
    out = np.zeros((len(v0s), len(thetas)))
    se = np.zeros_like(out)
    for a, v0 in enumerate(v0s):
        A = v0 * (1.0 - R)
        for b_i, th in enumerate(thetas):
            j = order[a, b_i]
            hit = Dhit[:, j] > 0
            c = np.where(hit, A * Lhit[:, j] + Dhit[:, j] * p.C_N, A * Lfin)
            out[a, b_i] = C_up + c.mean()
            se[a, b_i] = c.std() / math.sqrt(len(c))
    return out, se


def region(v0s, cost_act, cost_other):
    """ACT-optimal interval from linear interpolation (in log v) of cost_act - cost_other."""
    lv = np.log(v0s)
    d = cost_act - cost_other
    neg = np.where(d < 0)[0]
    if len(neg) == 0:
        return None

    def cross(i, j):  # sign change of d between grid points i, j
        return math.exp(lv[i] + (lv[j] - lv[i]) * d[i] / (d[i] - d[j]))
    i0, i1 = neg[0], neg[-1]
    lo = cross(i0 - 1, i0) if i0 > 0 else float(v0s[0])
    hi = cross(i1, i1 + 1) if i1 + 1 < len(v0s) else math.inf
    return lo, hi


def run_scenario(name, p, R_C, R_A, sampler, jumps, a):
    v0s = np.geomspace(0.05, 16.0, a.nv0)
    thC, thA = v_star(R_C, p), v_star(R_A, p)
    mult = np.geomspace(0.4, 2.5, a.nth)
    thetas = np.unique(np.concatenate([thC * mult, thA * mult, [thC, thA]]))
    shift = BG * p.sigma * math.sqrt(a.dt)
    logb = np.log(thetas[None, :] / v0s[:, None]) - shift
    flat = logb.ravel()
    srt = np.argsort(flat)
    barriers = flat[srt]
    order = np.empty(flat.shape, np.int64)
    order[srt] = np.arange(len(flat))
    order = order.reshape(logb.shape)

    Lhit, Dhit, Lfin = simulate(p, sampler, barriers, a.n, a.dt, a.tmax, jumps, seed=a.seed)
    cC, seC = cost_surface(Lhit, Dhit, Lfin, barriers, order, v0s, thetas, R_C, 0.0, p)
    cA, seA = cost_surface(Lhit, Dhit, Lfin, barriers, order, v0s, thetas, R_A, p.C_A, p)

    def pick(cost, ref):  # threshold minimising mean cost over start values well below the Poisson one
        rows = v0s < 0.6 * ref
        return int(np.argmin(cost[rows].mean(0)))
    kC, kA = pick(cC, thC), pick(cA, thA)
    iC, iA = int(np.argmin(abs(thetas - thC))), int(np.argmin(abs(thetas - thA)))

    def regret(cost, k, ref_i, ref):
        rows = v0s < 0.6 * ref
        return float((cost[rows, ref_i] / cost[rows, k] - 1).mean())

    copy_opt = np.minimum(cC[:, kC], p.C_N)
    act_opt = cA[:, kA]
    reg_sim = region(v0s, act_opt, copy_opt)
    # Poisson-calibrated thresholds in the same scenario
    reg_pthr = region(v0s, cA[:, iA], np.minimum(cC[:, iC], p.C_N))
    res = dict(
        scenario=name,
        theta_copy_best=float(thetas[kC]), theta_copy_poisson=float(thC),
        theta_act_best=float(thetas[kA]), theta_act_poisson=float(thA),
        regret_copy=regret(cC, kC, iC, thC), regret_act=regret(cA, kA, iA, thA),
        act_region_best=reg_sim, act_region_poisson_thr=reg_pthr,
        v0=v0s.tolist(), cost_copy=copy_opt.tolist(), cost_act=act_opt.tolist(),
        se_max=float(max(seC[:, kC].max(), seA[:, kA].max())),
    )
    return res, (v0s, cC, seC, thetas, iC)


def fmt_region(r):
    if r is None:
        return "never"
    lo, hi = r
    return f"{lo:5.2f} <= v < {'inf' if math.isinf(hi) else format(hi, '5.2f')}"


def main():
    ap = argparse.ArgumentParser()
    for f in ("rho", "mu", "g", "sigma", "C_N", "C_A"):
        ap.add_argument(f"--{f}", type=float, default=getattr(Params, f))
    ap.add_argument("--R_C", type=float, default=0.489319, help="copy recovery (toy drift 0.8)")
    ap.add_argument("--R_A", type=float, default=0.691576, help="ACT recovery (toy drift 0.8)")
    ap.add_argument("--n", type=int, default=30000)
    ap.add_argument("--dt", type=float, default=1 / 200)
    ap.add_argument("--tmax", type=float, default=40.0)
    ap.add_argument("--nv0", type=int, default=24)
    ap.add_argument("--nth", type=int, default=15)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="results/poisson_extensions.json")
    ap.add_argument("--plot", default="results/poisson_extensions.png")
    a = ap.parse_args()
    p = Params(a.rho, a.mu, a.g, a.sigma, a.C_N, a.C_A)
    R_C, R_A = a.R_C, a.R_A

    scen = [
        ("Poisson (CV=1)", epoch_sampler("exp", p.mu), None, 1.0),
        ("Hyperexp CV=2", epoch_sampler("hyper", p.mu, 2.0), None, 2.0),
        ("Hyperexp CV=3", epoch_sampler("hyper", p.mu, 3.0), None, 3.0),
        ("Erlang CV=0.5", epoch_sampler("erlang", p.mu, 0.5), None, 0.5),
        ("Deterministic", epoch_sampler("det", p.mu), None, 0.0),
        ("Poisson + jumps (1/yr)", epoch_sampler("exp", p.mu), (1.0, 0.2, 0.3), 1.0),
        ("Poisson + jumps (3/yr)", epoch_sampler("exp", p.mu), (3.0, 0.2, 0.3), 1.0),
    ]
    print(f"params: {p}\nR_C={R_C}, R_A={R_A}; v*_C={v_star(R_C, p):.3f}, v*_A={v_star(R_A, p):.3f}; "
          f"n={a.n}, dt={a.dt:.4f}")
    reg0 = act_region(R_C, R_A, p)
    print(f"closed-form (Poisson, GBM) ACT region: {fmt_region(reg0)}\n")

    results, base = [], None
    for name, sampler, jumps, _cv in scen:
        r, extra = run_scenario(name, p, R_C, R_A, sampler, jumps, a)
        if base is None:
            base = extra
            v0s, cC, seC, thetas, iC = extra
            print("check vs closed form (copy, theta = v*_C):")
            for v0 in (0.2, 1.0, 2.0):
                i = int(np.argmin(abs(v0s - v0)))
                print(f"  v0={v0s[i]:.2f}: MC={cC[i, iC]:.4f} +- {seC[i, iC]:.4f}   "
                      f"W={float(W(v0s[i], R_C, 0.0, p)):.4f}")
            print()
        results.append(r)
        print(f"{name:24s} theta_C {r['theta_copy_best']:.2f} (Poisson {r['theta_copy_poisson']:.2f}) "
              f"regret {100 * r['regret_copy']:5.1f}% | theta_A {r['theta_act_best']:.2f} "
              f"(Poisson {r['theta_act_poisson']:.2f}) regret {100 * r['regret_act']:5.1f}% | "
              f"ACT region: {fmt_region(r['act_region_best'])}   [se<={r['se_max']:.3f}]")

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump({"params": p.__dict__, "R_C": R_C, "R_A": R_A, "n": a.n, "dt": a.dt,
               "closed_form_act_region": reg0, "scenarios": results}, open(a.out, "w"), indent=2)
    print(f"\nsaved {a.out}")

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
    for r in results[:5]:
        ax[0].plot(r["v0"], r["cost_act"], label=r["scenario"])
    ax[0].plot(results[0]["v0"], np.minimum(results[0]["cost_copy"], p.C_N), "k:", label="copy (Poisson)")
    ax[0].set_xscale("log")
    ax[0].set_xlabel("v")
    ax[0].set_ylabel("expected cost (ACT, best threshold)")
    ax[0].legend(fontsize=7)
    ax[0].grid(alpha=0.3)
    names = [r["scenario"] for r in results]
    for i, r in enumerate(results):
        reg = r["act_region_best"]
        if reg:
            ax[1].barh(i, min(reg[1], 50) - reg[0], left=reg[0], color="C1", alpha=0.7)
    ax[1].set_yticks(range(len(names)))
    ax[1].set_yticklabels(names, fontsize=8)
    ax[1].set_xscale("log")
    ax[1].set_xlabel("ACT-optimal range of v")
    ax[1].grid(alpha=0.3)
    ax[1].invert_yaxis()
    fig.tight_layout()
    fig.savefig(a.plot, dpi=150)
    print(f"saved {a.plot}")


if __name__ == "__main__":
    main()
