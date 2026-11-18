"""Derailment extension: an error derails the task with probability theta; a derailed task still finishes, but its
output is wrong and costs F. Errors per step ~ Poisson(mu) (no contagion). The belief that the task is derailed after N
errors is 1 - (1 - theta)^N, so the state is the error count N.
(1) theta from the fault-injection experiment: theta = 1 - success(injected) / success(control), task-clustered bootstrap;
    for the multi arm, per injection: 1 - ratio^(1 / mean injections).
(2) Proposition 7: the closed-form count threshold N* (monotone case of optimal stopping) against value iteration on N.
(3) Value of the count rule over the best static choice, by theta and F.
Writes derail.json and fig_derail.png."""
import json, math
from pathlib import Path
import numpy as np
from scipy.stats import poisson

HERE = Path(__file__).resolve().parent
RES = HERE.parent / "inject" / "results"
MAXREP = {"deepseek": 2}
k, c, q, H, mu = 1.0, 5.0, 0.06, 40.0, 0.054


def load(m):
    out = {}
    for l in open(RES / f"{m}.jsonl"):
        r = json.loads(l)
        if r.get("ok") and r["rep"] < MAXREP.get(m, 99): out[r["key"]] = r
    return list(out.values())


def theta_est(m, B=2000):
    R = load(m); tasks = sorted({r["domain"] + ":" + r["task"] for r in R})
    by = {t: {a: [] for a in ("control", "single", "blame", "multi")} for t in tasks}; ninj = []
    for r in R:
        by[r["domain"] + ":" + r["task"]][r["arm"]].append(r["reward"] or 0.0)
        if r["arm"] == "multi": ninj.append(r["n_inj"])
    mi = float(np.mean(ninj))
    def th(ts):
        s = {a: np.mean([v for t in ts for v in by[t][a]]) for a in by[ts[0]]}
        return {"single": 1 - s["single"] / s["control"], "blame": 1 - s["blame"] / s["control"],
                "multi_per_injection": 1 - (s["multi"] / s["control"]) ** (1 / mi)}
    est = th(tasks); rng = np.random.default_rng(1); bs = []
    for _ in range(B): bs.append(th([tasks[i] for i in rng.integers(0, len(tasks), len(tasks))]))
    return {a: dict(theta=float(est[a]), ci=[float(np.percentile([b[a] for b in bs], 2.5)), float(np.percentile([b[a] for b in bs], 97.5))])
            for a in est} | {"mean_injections_multi": mi}


def n_star(theta, F, mu=mu):
    """Smallest N at which handing off beats one more step followed by hand-off (monotone case)."""
    if qH_lhs(F) <= 0: return 0
    if theta <= 0: return math.inf
    rhs = (1 - (q * H - k - c * mu) / (q * F)) * math.exp(mu * theta)
    if rhs <= 0: return math.inf
    return max(0, math.ceil(math.log(rhs) / math.log(1 - theta) - 1e-12))


def qH_lhs(F): return q * H - k - c * mu  # positive: an un-derailed agent is cheaper than the human


def solve(theta, F, Nmax=60, emax=10):
    """Value iteration on the error count N."""
    e = np.arange(emax + 1); pe = poisson.pmf(e, mu); pe /= pe.sum()
    N = np.arange(Nmax + 1); W = np.full(Nmax + 1, H)
    for _ in range(5000):
        Nn = np.minimum(N[:, None] + e[None, :], Nmax)
        pi_after = 1 - (1 - theta) ** Nn                       # derailed after this step's errors
        cont = k + c * mu + (pe[None, :] * (q * F * pi_after + (1 - q) * W[Nn])).sum(1)
        Wn = np.minimum(H, cont)
        if np.max(np.abs(Wn - W)) < 1e-10: break
        W = Wn
    stop = cont >= H
    return dict(W0=float(W[0]), n_star=int(N[np.argmax(stop)]) if stop.any() else None)


def never_cost(theta, F):
    s = q * math.exp(-mu * theta) / (1 - (1 - q) * math.exp(-mu * theta))  # P(no derailment by completion)
    return (k + c * mu) / q + F * (1 - s)


if __name__ == "__main__":
    out = {"params": dict(k=k, c=c, q=q, H=H, mu=mu), "theta": {m: theta_est(m) for m in ("llama8b", "llama70b", "deepseek")}}
    rows = []
    for m, lab in (("llama8b", "Llama-8B"), ("llama70b", "Llama-70B"), ("deepseek", "DeepSeek-V3.1")):
        th = max(0.0, out["theta"][m]["single"]["theta"])
        for F in (40.0, 60.0, 100.0):
            s = solve(th, F); cu = never_cost(th, F)
            rows.append(dict(model=lab, theta=round(th, 3), F=F, n_star_closed=n_star(th, F) if th > 0 else None, n_star_dp=s["n_star"],
                             W0=round(s["W0"], 3), never=round(cu, 3), value_vs_static=round(min(H, cu) - s["W0"], 3)))
    out["calibrated"] = rows
    grid = []
    for th in (0.0, 0.05, 0.1, 0.2, 0.3, 0.5):
        for F in (40.0, 60.0, 100.0):
            s = solve(th, F); cu = never_cost(th, F)
            grid.append(dict(theta=th, F=F, n_star_closed=(n_star(th, F) if th > 0 else None), n_star_dp=s["n_star"],
                             value_vs_static=round(min(H, cu) - s["W0"], 3)))
    out["grid"] = grid
    json.dump(out, open(HERE / "derail.json", "w"), indent=1); print(json.dumps(out, indent=1))
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(4.6, 3.2)); ths = np.linspace(0.01, 0.5, 50)
    for F, col in ((40.0, "#9cc5e0"), (60.0, "#2a6f97"), (100.0, "#173f5f")):
        ax.plot(ths, [min(H, never_cost(t, F)) - solve(t, F)["W0"] for t in ths], color=col, label=f"F = {F:g}")
    for m, mk in (("llama70b", "o"), ("deepseek", "s")):
        t = out["theta"][m]["single"]["theta"]; ax.axvline(t, ls=":", color="k", lw=0.7)
        ax.text(t + 0.005, ax.get_ylim()[1] * 0.9 if ax.get_ylim()[1] > 0 else 1, {"llama70b": "70B", "deepseek": "DeepSeek"}[m], fontsize=7)
    ax.set_xlabel("Derailment probability per error θ"); ax.set_ylabel("Value of the count rule"); ax.legend(fontsize=7, frameon=False)
    fig.tight_layout(); fig.savefig(HERE / "fig_derail.png", dpi=200)
