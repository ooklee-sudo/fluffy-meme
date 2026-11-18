"""Numerical illustration of the delegation / hand-off model with self-exciting errors.
State x = excess error intensity; errors e_t ~ Poisson(mu + x_t); x_{t+1} = delta x_t + alpha e_t.
Each step costs k + c e_t; the task completes after a step with probability q; the firm may hand off at cost H.
W(x) = min{ H, k + c(mu + x) + (1 - q) E[ W(delta x + alpha e) ] }.
Outputs: hand-off threshold x*, W(0), cost of never handing off C_U (closed form), value of monitoring, and a comparison with the
best rule based on the error count, by simulation; sensitivity to the branching ratio n = alpha / (1 - delta)."""
import json
import numpy as np
from scipy.stats import poisson
def solve(mu, alpha, delta, k, c, q, H, xmax=12.0, nx=1201, emax=40):
    X = np.linspace(0, xmax, nx); W = np.full(nx, H); e = np.arange(emax + 1)
    P = poisson.pmf(e[None, :], (mu + X)[:, None]); P /= P.sum(1, keepdims=True)
    Xn = np.clip(delta * X[:, None] + alpha * e[None, :], 0, xmax)
    for it in range(5000):
        cont = k + c * (mu + X) + (1 - q) * (P * np.interp(Xn, X, W)).sum(1)
        Wn = np.minimum(H, cont)
        if np.max(np.abs(Wn - W)) < 1e-9: break
        W = Wn
    stop = cont >= H; xs = X[np.argmax(stop)] if stop.any() else np.inf
    return dict(W0=float(W[0]), x_star=float(xs), cont0=float(cont[0])), (X, W)
def CU(mu, alpha, delta, k, c, q):
    rho = delta + alpha
    if (1 - q) * rho >= 1: return np.inf
    base = (k + c * mu) / q
    if abs(1 - rho) < 1e-12: return base + c * alpha * mu * sum((1 - q) ** t * t for t in range(5000))
    return base + c * alpha * mu / (1 - rho) * (1 / q - 1 / (1 - (1 - q) * rho))
def simulate(mu, alpha, delta, k, c, q, H, rule, n=20000, seed=0, tmax=400):
    rng = np.random.default_rng(seed); tot = 0.0; handed = 0
    for _ in range(n):
        x = 0.0; N = 0; cost = 0.0
        for t in range(tmax):
            if rule(x, N, t): cost += H; handed += 1; break
            ev = rng.poisson(mu + x); cost += k + c * ev; N += ev; x = delta * x + alpha * ev
            if rng.random() < q: break
        tot += cost
    return tot / n, handed / n
