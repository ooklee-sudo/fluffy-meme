"""Behavioral extension of the real options model (real_options.py): what a biased decision maker loses.

The normative model (Props. 1-4) gives the optimal policy among {copy, ACT, retrain now} and the
retraining threshold v*. Here the decision maker picks the policy and the threshold using *perceived*
parameters; the cost of that choice is then evaluated under the *true* parameters.
regret(v) = true cost of the biased choice - true cost of the optimal choice  (multiples of C_N).

Biases (all enter through the perceived problem; defaults are illustrative, not estimated):
  present bias (pb)     future loss flow is weighted by pb < 1 (beta-delta), retraining cost is paid now
                        -> k_perceived = pb * k   -> threshold too high (retrains too late)
  loss aversion (lam)   the performance shortfall is coded as a loss with weight lam > 1
                        -> k_perceived = lam * k  -> threshold too low (retrains too early)
  status quo (phi)      switching (retraining) cost is inflated: C_N_perceived = phi * C_N
                        -> threshold too high, and retrain-now looks too expensive
  overconfidence (sig)  volatility underestimated: sigma_perceived = sig_ratio * sigma
  planning fallacy (mu) upgrade frequency underestimated: mu_perceived = mu_ratio * mu
  ambiguity aversion    the unknown recovery of ACT is evaluated pessimistically: R_A_perceived = R_A - amb

The cost of following a threshold T (retrain when v reaches T) at recovery R with transfer cost C is
  W(v; T) = C + k v - (k T - C_N) (v / T)^beta   for v < T,   C + C_N otherwise
which equals W_j(v) of Prop. 4 when T = v*_j (see real_options.W).

Usage:
  python behavioral_options.py
  python behavioral_options.py --recovery results/pairs_summary.json --pb 0.8 --lam 2.25
"""
import argparse
import json
import os
from dataclasses import dataclass, replace

import numpy as np

import real_options as ro
from real_options import Params, beta, k


@dataclass(frozen=True)
class Bias:
    pb: float = 1.0         # present bias (beta-delta), <= 1
    lam: float = 1.0        # loss aversion on the performance shortfall, >= 1
    phi: float = 1.0        # status quo: retraining cost inflation, >= 1
    sig_ratio: float = 1.0  # overconfidence: perceived sigma / true sigma, <= 1
    mu_ratio: float = 1.0   # planning fallacy: perceived mu / true mu, <= 1
    amb: float = 0.0        # ambiguity aversion: subtracted from R_A, >= 0


NEUTRAL = Bias()


def perceived_params(p: Params, b: Bias) -> Params:
    return replace(p, sigma=p.sigma * b.sig_ratio, mu=p.mu * b.mu_ratio, C_N=p.C_N * b.phi)


def k_perceived(R: float, pp: Params, b: Bias) -> float:
    return b.pb * b.lam * k(R, pp)


def threshold_perceived(R: float, pp: Params, b: Bias) -> float:
    bt = beta(pp)
    return bt / (bt - 1.0) * pp.C_N / k_perceived(R, pp, b)


def W_perceived(v, R: float, C: float, pp: Params, b: Bias):
    v = np.asarray(v, dtype=float)
    T, kk, bt = threshold_perceived(R, pp, b), k_perceived(R, pp, b), beta(pp)
    F = np.where(v < T, (kk * T - pp.C_N) * (v / T) ** bt, kk * v - pp.C_N)
    return np.where(v < T, C + kk * v - F, C + pp.C_N)


def W_true(v, R: float, C: float, T: float, p: Params):
    """True expected cost of transferring with (R, C) and retraining at threshold T."""
    v = np.asarray(v, dtype=float)
    kk = k(R, p)
    return np.where(v < T, C + kk * v - (kk * T - p.C_N) * (v / T) ** beta(p), C + p.C_N)


def evaluate(v, R_C: float, R_A: float, p: Params, b: Bias):
    """Biased choice among (copy, ACT, retrain now) at each v, its true cost, and the regret."""
    pp = perceived_params(p, b)
    R_A_p = max(R_A - b.amb, 0.0)
    perc = np.stack([W_perceived(v, R_C, 0.0, pp, b),
                     W_perceived(v, R_A_p, p.C_A, pp, b),
                     np.full(len(v), pp.C_N)])
    choice = perc.argmin(axis=0)
    T_C, T_A = threshold_perceived(R_C, pp, b), threshold_perceived(R_A_p, pp, b)
    true = np.stack([W_true(v, R_C, 0.0, T_C, p), W_true(v, R_A, p.C_A, T_A, p), np.full(len(v), p.C_N)])
    chosen = np.take_along_axis(true, choice[None], axis=0)[0]
    c = ro.policy_costs(v, R_C, R_A, p)
    opt_choice = np.stack([c["copy"], c["act"], c["retrain"]])
    opt = opt_choice.min(axis=0)
    return dict(choice=choice, opt_choice=opt_choice.argmin(axis=0), cost=chosen, opt=opt,
                regret=np.maximum(chosen - opt, 0.0), T_C=T_C, T_A=T_A)


def summarize(R_C: float, R_A: float, p: Params, b: Bias, v):
    e = evaluate(v, R_C, R_A, p, b)
    i = int(np.argmax(e["regret"]))
    return dict(
        thr_ratio_copy=e["T_C"] / ro.v_star(R_C, p),
        thr_ratio_act=e["T_A"] / ro.v_star(R_A, p),
        mean_regret=float(e["regret"].mean()),
        max_regret=float(e["regret"][i]),
        v_at_max_regret=float(v[i]),
        wrong_policy_share=float((e["choice"] != e["opt_choice"]).mean()),
    )


SCENARIOS = {
    "present bias":     lambda a: Bias(pb=a.pb),
    "loss aversion":    lambda a: Bias(lam=a.lam),
    "status quo":       lambda a: Bias(phi=a.phi),
    "overconfidence":   lambda a: Bias(sig_ratio=a.sig_ratio),
    "planning fallacy": lambda a: Bias(mu_ratio=a.mu_ratio),
    "ambiguity aversion": lambda a: Bias(amb=a.amb),
}
SWEEPS = {  # bias field -> value at intensity 0 and 1
    "pb": (1.0, 0.5), "lam": (1.0, 3.0), "phi": (1.0, 3.0),
    "sig_ratio": (1.0, 0.3), "mu_ratio": (1.0, 0.3), "amb": (0.0, 0.3),
}
SWEEP_LABEL = {"pb": "present bias (pb)", "lam": "loss aversion (lam)", "phi": "status quo (phi)",
               "sig_ratio": "sigma ratio", "mu_ratio": "mu ratio", "amb": "ambiguity (amb)"}


def plot(recov, p: Params, scen, v, path_regret, path_sweep):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    label = "0.8" if "0.8" in recov else next(iter(recov))
    R_C, R_A = recov[label]

    fig, ax = plt.subplots(figsize=(7.5, 4.4))
    for name, b in scen.items():
        ax.plot(v, evaluate(v, R_C, R_A, p, b)["regret"], label=name)
    ax.set_xscale("log")
    ax.set_xlabel("Annual adapter value v (multiples of C_N)")
    ax.set_ylabel("Regret vs optimal policy (multiples of C_N)")
    ax.set_title(f"Cost of each bias alone (drift {label})")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path_regret, dpi=150)

    fig, axes = plt.subplots(2, 3, figsize=(10, 5.6), sharey=True)
    xs = np.linspace(0, 1, 21)
    for ax, (field, (lo, hi)) in zip(axes.ravel(), SWEEPS.items()):
        vals = lo + xs * (hi - lo)
        for name, (rc, ra) in recov.items():
            ys = [evaluate(v, rc, ra, p, replace(NEUTRAL, **{field: x}))["regret"].mean() for x in vals]
            ax.plot(vals, ys, label=f"drift {name}")
        ax.set_xlabel(SWEEP_LABEL[field])
        ax.grid(alpha=0.3)
    axes[0, 0].set_ylabel("Mean regret (x C_N)")
    axes[1, 0].set_ylabel("Mean regret (x C_N)")
    axes[0, 0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(path_sweep, dpi=150)
    print(f"saved {path_regret}, {path_sweep}")


def main():
    ap = argparse.ArgumentParser()
    for f in ("rho", "mu", "g", "sigma", "C_N", "C_A"):
        ap.add_argument(f"--{f}", type=float, default=getattr(Params, f))
    d = Bias()
    ap.add_argument("--pb", type=float, default=0.7, help="present bias, 1 = none")
    ap.add_argument("--lam", type=float, default=1.5, help="loss aversion, 1 = none")
    ap.add_argument("--phi", type=float, default=1.5, help="status quo cost inflation, 1 = none")
    ap.add_argument("--sig-ratio", type=float, default=0.5, help="perceived/true sigma, 1 = none")
    ap.add_argument("--mu-ratio", type=float, default=0.5, help="perceived/true mu, 1 = none")
    ap.add_argument("--amb", type=float, default=0.1, help="ambiguity penalty on R_A, 0 = none")
    ap.add_argument("--recovery", help="JSON from act_toy.py / act_llama.py / run_pairs.py (as in real_options.py)")
    ap.add_argument("--out", default="results/behavioral_options.json")
    ap.add_argument("--plot-regret", default="results/behavioral_regret.png")
    ap.add_argument("--plot-sweep", default="results/behavioral_sweep.png")
    a = ap.parse_args()
    p = Params(a.rho, a.mu, a.g, a.sigma, a.C_N, a.C_A)

    recov = {"0.8": (0.489319, 0.691576), "0.3": (0.955040, 0.974928)}  # Section 5.2 toy values
    if a.recovery:
        data = json.load(open(a.recovery))
        clip = lambda R: min(R, 0.999)
        recov = {str(r["drift"]): (clip(r["R_C"]), clip(r["R_A"])) for r in data["recovery"]}
        if "C_A_over_C_N" in data:
            p = replace(p, C_A=data["C_A_over_C_N"] * p.C_N)

    v = np.geomspace(0.05, 20, 800)
    scen = {name: f(a) for name, f in SCENARIOS.items()}
    scen["all combined"] = Bias(a.pb, a.lam, a.phi, a.sig_ratio, a.mu_ratio, a.amb)

    # sanity: no bias -> no regret
    for name, (rc, ra) in recov.items():
        assert evaluate(v, rc, ra, p, NEUTRAL)["regret"].max() < 1e-9, "neutral decision maker must have zero regret"

    print(f"beta = {beta(p):.2f}; regret in multiples of C_N, averaged over v in [0.05, 20] (log-uniform)")
    out = {}
    for label, (R_C, R_A) in recov.items():
        print(f"\n== drift {label}: R_C={R_C:.3f}, R_A={R_A:.3f} ==")
        print(f"{'bias':>20} {'v*_C ratio':>10} {'v*_A ratio':>10} {'mean regret':>11} {'max regret':>10} {'at v':>7} {'wrong policy':>12}")
        out[label] = {}
        for name, b in scen.items():
            s = summarize(R_C, R_A, p, b, v)
            out[label][name] = {**s, "bias": b.__dict__}
            print(f"{name:>20} {s['thr_ratio_copy']:10.2f} {s['thr_ratio_act']:10.2f} {s['mean_regret']:11.3f} "
                  f"{s['max_regret']:10.3f} {s['v_at_max_regret']:7.2f} {s['wrong_policy_share']:11.0%}")

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump({"params": p.__dict__, "biases": {n: b.__dict__ for n, b in scen.items()}, "results": out},
              open(a.out, "w"), indent=2)
    plot(recov, p, scen, v, a.plot_regret, a.plot_sweep)


if __name__ == "__main__":
    main()
