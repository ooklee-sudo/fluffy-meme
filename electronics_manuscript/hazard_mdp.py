"""Section 8.3: solve the drift-hazard MDP numerically for Weibull drift arrivals.

State (X, u): degradation X on a 0.01 grid and days u since the last drift event
(capped at U). Each day the maintainer either does nothing or fully retrains
(X -> 0, cost c_r); then X grows by the leak eta and, if a drift event arrives,
by a unit jump. Drift inter-arrival times are Weibull with shape k, rounded up
to whole days; the scale is set so the mean is the same for every shape, so the
shapes differ only in aging (k > 1: DMRL, k = 1: memoryless, k < 1: IMRL).

Compares, for each shape:
  * the average-cost optimal policy from relative value iteration (thresholds X*(u));
  * the best memoryless threshold policy (retrain when X >= s, s ignores u);
  * the closed-form fluid approximation of Section 4.2;
  * the policy that is optimal for the opposite aging class, applied in this world.

Usage: python3 hazard_mdp.py [--out results_hazard.json]
"""
import argparse
import json
import math

import numpy as np

ETA, MU_M, ALPHA = 0.01, 1.0, 1.0
DX = 0.01                      # degradation grid step (= ETA, so the leak is one step)
X_MAX = 20.0
U_CAP = 150                    # days since last drift event; u >= U_CAP is lumped
JUMP = int(round(MU_M / DX))
NX = int(round(X_MAX / DX)) + 1
X = np.arange(NX) * DX


def weibull_hazard(k, mean_days):
    """Daily hazard h(u) = P(drift on day u+1 | none in the u days since the last one)."""
    def surv(t, scale):
        return np.exp(-(t / scale) ** k)

    n = np.arange(0, 20000)

    def discrete_mean(scale):                # E[ceil(T)] = sum_{n>=0} S(n)
        return surv(n, scale).sum()

    lo, hi = 1e-3, 1e3                       # bisection on the scale for E[ceil(T)] = mean_days
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        lo, hi = (mid, hi) if discrete_mean(mid) < mean_days else (lo, mid)
    scale = math.sqrt(lo * hi)
    u = np.arange(U_CAP + 1)
    s0, s1 = surv(u, scale), surv(u + 1, scale)
    h = 1 - s1 / s0
    h[U_CAP] = h[U_CAP - 1]                  # lumped tail state keeps the last hazard
    return h, scale, float(surv(U_CAP, scale))


def post_value(V, h):
    """E[V(next) | post-action degradation index i, age u] for every (i, u)."""
    up = np.minimum(np.arange(NX) + 1, NX - 1)
    jump = np.minimum(np.arange(NX) + 1 + JUMP, NX - 1)
    u_next = np.minimum(np.arange(U_CAP + 1) + 1, U_CAP)
    return h[None, :] * V[jump, 0][:, None] + (1 - h[None, :]) * V[up][:, u_next]


def solve(h, c_r, policy=None, tol=1e-9, max_iter=200000, damp=0.5, V0=None):
    """Relative value iteration with the aperiodicity transform.

    policy=None optimizes; otherwise policy is a boolean (NX, U+1) retrain mask to evaluate.
    Returns (gain, retrain mask, iterations, relative values); V0 warm-starts the iteration.
    """
    V = np.zeros((NX, U_CAP + 1)) if V0 is None else V0.copy()
    cost = ALPHA * X[:, None]
    for it in range(max_iter):
        W = post_value(V, h)
        q_keep = cost + W
        q_retrain = cost + c_r + W[0][None, :]
        if policy is None:
            act = q_retrain < q_keep
        else:
            act = policy
        TV = np.where(act, q_retrain, q_keep)
        D = TV - V
        lo, hi = D.min(), D.max()
        V = V + damp * D
        V -= V[0, 0]
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi), act, it, V


def thresholds(act):
    """Smallest X at which the policy retrains, for each u; also checks monotonicity in X."""
    th, monotone = [], True
    for u in range(U_CAP + 1):
        col = act[:, u]
        idx = np.argmax(col) if col.any() else None
        th.append(None if idx is None else float(X[idx]))
        if idx is not None and not col[idx:].all():
            monotone = False
    return th, monotone


def best_memoryless(h, c_r, V0, s_center):
    """Best single threshold s (ignores u): coarse scan at 0.25, then golden-section search to 0.01."""
    cache = {}

    def gain(s):
        s = round(s, 2)
        if s not in cache:
            pol = np.broadcast_to((X >= s - 1e-12)[:, None], (NX, U_CAP + 1))
            cache[s] = solve(h, c_r, policy=pol, V0=V0)[0]
        return cache[s]
    coarse = np.arange(max(0.5, round(0.5 * s_center, 1)), 1.6 * s_center, 0.25)  # around the fluid threshold
    g = [gain(s) for s in coarse]
    i = int(np.argmin(g))
    a, b = coarse[max(i - 1, 0)], coarse[min(i + 1, len(coarse) - 1)]
    phi = (math.sqrt(5) - 1) / 2
    while b - a > 0.02:
        c, d = b - phi * (b - a), a + phi * (b - a)
        if gain(c) <= gain(d):
            b = d
        else:
            a = c
    cand = np.arange(round(a, 2), round(b, 2) + 0.005, 0.01)
    best = min(cand, key=gain)
    return float(round(best, 2)), float(gain(best)), cache


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="results_hazard.json")
    ap.add_argument("--lam", type=float, default=0.1, help="mean drift-event rate per day")
    ap.add_argument("--cr", type=float, default=100.0)
    ap.add_argument("--shapes", default="0.5,1,2")
    args = ap.parse_args()

    shapes = [float(s) for s in args.shapes.split(",")]
    mean_days = 1 / args.lam
    gamma = ETA + args.lam * MU_M
    s_fluid = math.sqrt(2 * args.cr * gamma / ALPHA)
    out = {"params": {"eta": ETA, "mu_M": MU_M, "alpha": ALPHA, "lambda": args.lam, "gamma": gamma,
                      "c_r": args.cr, "dx": DX, "u_cap": U_CAP},
           "fluid": {"s_star": s_fluid, "T_star": s_fluid / gamma, "J_star": math.sqrt(2 * args.cr * gamma * ALPHA)},
           "shapes": {}}
    hazards, acts = {}, {}
    for k in shapes:
        h, scale, tail = weibull_hazard(k, mean_days)
        hazards[k] = h
        g_opt, act, iters, V_opt = solve(h, args.cr)
        acts[k] = act
        th, mono = thresholds(act)
        print(f"k={k}: optimal g*={g_opt:.4f} ({iters} iterations)", flush=True)
        s_mem, g_mem, scan = best_memoryless(h, args.cr, V_opt, s_fluid)
        g_fluid_policy = solve(h, args.cr, policy=np.broadcast_to((X >= s_fluid)[:, None], (NX, U_CAP + 1)), V0=V_opt)[0]
        out["shapes"][str(k)] = {
            "weibull_scale": scale, "tail_mass_beyond_cap": tail, "hazard": h.tolist(),
            "g_opt": g_opt, "rvi_iterations": iters, "thresholds": th, "monotone_in_X": mono,
            "s_memoryless": s_mem, "g_memoryless": g_mem, "memoryless_scan": {str(s): g for s, g in sorted(scan.items())}, "g_fluid_threshold": g_fluid_policy,
            "saving_vs_memoryless_pct": 100 * (g_mem - g_opt) / g_mem,
        }
        print(f"k={k}: scale={scale:.3f} g*={g_opt:.4f} memoryless s={s_mem:.2f} g={g_mem:.4f} "
              f"saving={100*(g_mem-g_opt)/g_mem:.2f}% fluid-s g={g_fluid_policy:.4f} monotone={mono} iters={iters}",
              flush=True)
    # each world under the policy optimal for every other shape
    for k in shapes:
        cross = {}
        for k2 in shapes:
            cross[str(k2)] = solve(hazards[k], args.cr, policy=acts[k2])[0]
            print(f"  world k={k} under policy of k={k2}: {cross[str(k2)]:.4f}", flush=True)
        out["shapes"][str(k)]["g_under_policy_of_shape"] = cross
        print(f"world k={k}: " + ", ".join(f"policy k={k2}: {g:.4f}" for k2, g in cross.items()), flush=True)
    json.dump(out, open(args.out, "w"), indent=1)


if __name__ == "__main__":
    main()
