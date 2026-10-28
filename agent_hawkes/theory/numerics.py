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
mu, alpha, delta = 0.054, 0.209, 0.453           # Llama-70B, heterogeneity-adjusted estimates (mean baseline)
k, c, q, H = 1.0, 5.0, 0.06, 40.0               # illustrative costs: step 1, error 5, completion 6% per step, hand-off 40
res = {"params": dict(mu=mu, alpha=alpha, delta=delta, branching=alpha / (1 - delta), k=k, c=c, q=q, H=H)}
sol, (X, W) = solve(mu, alpha, delta, k, c, q, H); res["optimal"] = sol; res["C_U_never_hand_off"] = CU(mu, alpha, delta, k, c, q)
xs = sol["x_star"]
res["sim_threshold_rule"] = simulate(mu, alpha, delta, k, c, q, H, lambda x, N, t: x >= xs)
res["sim_never"] = simulate(mu, alpha, delta, k, c, q, H, lambda x, N, t: False)
best = None
for m in range(1, 12):
    v = simulate(mu, alpha, delta, k, c, q, H, lambda x, N, t, m=m: N >= m, n=8000)
    if best is None or v[0] < best[1][0]: best = (m, v)
res["sim_best_count_rule"] = dict(m=best[0], cost=best[1][0], handoff_share=best[1][1])
sens = []
for n_ in (0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 0.95, 1.0, 1.05):
    a = n_ * (1 - delta); s, _ = solve(mu, a, delta, k, c, q, H); cu = CU(mu, a, delta, k, c, q)
    sens.append(dict(branching=n_, alpha=round(a, 4), W0=round(s["W0"], 3), x_star=s["x_star"], C_U=(None if np.isinf(cu) else round(cu, 3)),
                     value_vs_never=(None if np.isinf(cu) else round(cu - s["W0"], 3)), value_vs_static=round(min(H, cu) - s["W0"], 3)))
res["sensitivity_branching"] = sens
json.dump(res, open("numerics.json", "w"), indent=1); print(json.dumps(res, indent=1))
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 3.2))
a1.plot(X, W, color="#2a6f97"); a1.axvline(xs, ls="--", color="k", lw=0.7); a1.set_xlabel("Excess error intensity x"); a1.set_ylabel("Minimum expected cost W(x)"); a1.set_title("a  Hand off when x ≥ x*", loc="left", fontsize=9); a1.set_xlim(0, 4)
bn = [s_["branching"] for s_ in sens]; a2.plot(bn, [s_["value_vs_static"] for s_ in sens], marker="o", color="#2a6f97", label="vs best static choice")
a2.plot([b for b, s_ in zip(bn, sens) if s_["value_vs_never"] is not None], [s_["value_vs_never"] for s_ in sens if s_["value_vs_never"] is not None], marker="s", color="#e07a5f", label="vs never handing off")
a2.set_xlabel("Branching ratio n"); a2.set_ylabel("Value of monitoring"); a2.set_title("b  Value of monitoring rises with n", loc="left", fontsize=9); a2.legend(fontsize=7, frameon=False); a2.set_yscale("log")
fig.tight_layout(); fig.savefig("fig_theory.png", dpi=200)
