"""Rust (1987)-style dynamic discrete choice model of LLM retraining.

State x: accumulated drift (0..N). Drift increments ~ Poisson(mu) per period.
Errors per period ~ Poisson(lam0 + gamma*x); per-error loss c (normalised to 1).
Choice d in {0: keep, 1: retrain}; retrain costs RC and resets x to 0.
Type-I extreme value shocks (scale 1) => logit choice probabilities, logsum EV.
"""
import argparse, json
import numpy as np
from scipy.optimize import minimize, minimize_scalar
from scipy.stats import poisson

N = 80  # state-space cap


def trans_matrix(mu, n=N):
    """P[x, x'] under 'keep': x' = min(x + D, n), D ~ Poisson(mu)."""
    P = np.zeros((n + 1, n + 1))
    for x in range(n + 1):
        k = np.arange(0, n - x)
        P[x, x + k] = poisson.pmf(k, mu)
        P[x, n] = 1 - P[x].sum()
    return P


def solve(gamma, RC, lam0=5.0, mu=1.0, beta=0.95, c=1.0, tol=1e-10):
    """Value iteration. Returns (V, EV0_keep, EV_retrain, P_retrain(x))."""
    P = trans_matrix(mu)
    x = np.arange(N + 1)
    u0 = -c * (lam0 + gamma * x)
    u1 = -RC - c * lam0 * np.ones_like(u0)
    V = np.zeros(N + 1)
    for _ in range(100000):
        EV_keep = P @ V
        EV_ret = P[0] @ V  # reset to 0, then drift arrives next period
        v0 = u0 + beta * EV_keep
        v1 = u1 + beta * EV_ret
        m = np.maximum(v0, v1)
        Vn = m + np.log(np.exp(v0 - m) + np.exp(v1 - m))  # logsum
        if np.max(np.abs(Vn - V)) < tol:
            V = Vn
            break
        V = Vn
    v0 = u0 + beta * (P @ V)
    v1 = u1 + beta * (P[0] @ V)
    p1 = 1 / (1 + np.exp(v0 - v1))
    return V, v0, v1, p1


def threshold(p1):
    """Smallest x with P(retrain) > 0.5."""
    return int(np.argmax(p1 > 0.5))


def simulate(T, gamma, RC, lam0=5.0, mu=1.0, beta=0.95, rng=None):
    rng = rng or np.random.default_rng(0)
    _, _, _, p1 = solve(gamma, RC, lam0, mu, beta)
    x = np.zeros(T, int); d = np.zeros(T, int); n_err = np.zeros(T, int)
    cur = 0
    for t in range(T):
        x[t] = cur
        d[t] = rng.random() < p1[cur]
        n_err[t] = rng.poisson(lam0 + gamma * (0 if d[t] else cur))
        base = 0 if d[t] else cur
        cur = min(base + rng.poisson(mu), N)
    return x, d, n_err, p1


def loglik_choice(RC, gamma, x, d, lam0, mu, beta):
    _, _, _, p1 = solve(gamma, RC, lam0, mu, beta)
    p = np.clip(p1[x], 1e-12, 1 - 1e-12)
    return np.sum(d * np.log(p) + (1 - d) * np.log(1 - p))


def estimate(x, d, n_err, beta=0.95):
    # Stage 1a: mu from drift increments after 'keep' (no censoring at N)
    keep = np.where(d[:-1] == 0)[0]
    mu_hat = np.mean(x[keep + 1] - x[keep])
    # Stage 1b: Poisson regression n ~ exp? Model is LINEAR in x: lam = lam0 + gamma*x
    # (identity link) -> ML by Newton on (lam0, gamma), using post-decision state.
    xe = np.where(d == 1, 0, x).astype(float)
    def nll(th):
        lam = np.maximum(th[0] + th[1] * xe, 1e-9)
        return -np.sum(n_err * np.log(lam) - lam)
    r = minimize(nll, [3.0, 0.1], method="Nelder-Mead", options=dict(xatol=1e-8, fatol=1e-10))
    lam0_hat, gamma_hat = r.x
    # Stage 2: NFXP for RC given plug-in (gamma, lam0, mu)
    r2 = minimize_scalar(lambda rc: -loglik_choice(rc, gamma_hat, x, d, lam0_hat, mu_hat, beta),
                         bounds=(1, 200), method="bounded")
    # Joint (gamma, RC) from choice data only -> identification check
    def nll_j(th):
        return -loglik_choice(th[1], th[0], x, d, lam0_hat, mu_hat, beta)
    rj = minimize(nll_j, [gamma_hat, r2.x], method="Nelder-Mead",
                  options=dict(xatol=1e-4, fatol=1e-6, maxiter=400))
    return dict(mu=mu_hat, lam0=lam0_hat, gamma=gamma_hat, RC=float(r2.x),
                gamma_joint=float(rj.x[0]), RC_joint=float(rj.x[1]))


def cycle_length(d):
    idx = np.where(d == 1)[0]
    return float(np.mean(np.diff(idx))) if len(idx) > 1 else np.nan


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=100)
    ap.add_argument("--T", type=int, default=3000)
    ap.add_argument("--out", default="results.json")
    a = ap.parse_args()
    G, RC0, L0, MU, B = 0.5, 40.0, 5.0, 1.0, 0.95

    out = {}
    # (1) single-run replication of the research plan's table
    x, d, n, p1 = simulate(a.T, G, RC0, L0, MU, B, np.random.default_rng(1))
    th = threshold(p1)
    out["single_run"] = dict(threshold=th, error_rate_at_threshold=L0 + G * th,
                             ratio_to_base=(L0 + G * th) / L0, mean_cycle=cycle_length(d),
                             estimates=estimate(x, d, n, B))
    # (2) counterfactual in RC (and mu = competitive/drift pressure)
    out["cf_RC"] = {rc: threshold(solve(G, rc, L0, MU, B)[3]) for rc in [10, 20, 40, 80, 160]}
    out["cf_mu"] = {m: threshold(solve(G, RC0, L0, m, B)[3]) for m in [0.5, 1.0, 1.5, 2.0]}
    out["cf_beta"] = {b: threshold(solve(G, RC0, L0, MU, b)[3]) for b in [0.90, 0.95, 0.99]}
    # (3) Monte Carlo of the estimators
    ests = []
    for r in range(a.reps):
        x, d, n, _ = simulate(a.T, G, RC0, L0, MU, B, np.random.default_rng(100 + r))
        ests.append(estimate(x, d, n, B))
    keys = ests[0].keys()
    out["mc"] = {k: dict(mean=float(np.mean([e[k] for e in ests])),
                         sd=float(np.std([e[k] for e in ests]))) for k in keys}
    # (4) sample-size sensitivity (weekly data: 52 per year)
    out["mc_T"] = {}
    for T in [100, 250, 500, 1000]:
        es = [estimate(*simulate(T, G, RC0, L0, MU, B, np.random.default_rng(900 + r))[:3], B)
              for r in range(min(a.reps, 50))]
        out["mc_T"][T] = dict(RC_mean=float(np.mean([e["RC"] for e in es])),
                              RC_sd=float(np.std([e["RC"] for e in es])),
                              gamma_mean=float(np.mean([e["gamma"] for e in es])))
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out, indent=1))
