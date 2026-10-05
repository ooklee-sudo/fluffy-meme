"""Tables and diagnostics for the Section 6 experiment, from the JSON written by tofu_experiment.py.

    python analyze.py --dir results/pf [--method ga]
Prints Table 1 / Table 2 style summaries and writes analysis_<method>.json and eps_vs_strength_<method>.png.
Conventions (see Section 6.1/6.3): U = author component (mean over the 4 groups) + general component;
Shapley sums and eps(empty) use U; the L1 norms and the sequential comparison use the author component.
rho(T) = (1/n) sum_{j not in T}(U^_j - U_j);  kappa(T) = -[(1/n) sum_{j in T}(U^_j - U_j) + (U^_gen - U_gen)],
so that eps = rho - kappa holds exactly and rho(empty) is the mean excess on the forgotten groups.
"""
import argparse
import itertools
import json
import os

import numpy as np

import shapley as sh

n = 4
ALL = tuple(range(n))


def mk(S):
    return "".join("1" if i in S else "0" for i in range(n))


def table(res, f):
    return {frozenset(S): f(res[mk(S)]) for r in range(n + 1) for S in itertools.combinations(ALL, r)}


def spearman(a, b):
    from scipy.stats import spearmanr
    return float(spearmanr(a, b).correlation)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "pf"))
    ap.add_argument("--method", default="ga")
    a = ap.parse_args()
    ret = json.load(open(os.path.join(a.dir, "retrain.json")))
    unl = json.load(open(os.path.join(a.dir, f"unlearn_{a.method}.json")))
    noise = json.load(open(os.path.join(a.dir, "noise.json"))) if os.path.exists(os.path.join(a.dir, "noise.json")) else None
    cfg = json.load(open(os.path.join(a.dir, f"config_{a.method}.json")))

    Utot = lambda e: float(np.mean(e["groups"]) + e["general"])
    Uaut = lambda e: float(np.mean(e["groups"]))
    U, UA = sh.as_game(table(ret, Utot)), sh.as_game(table(ret, Uaut))
    v, vA = sh.contribution_game(U), sh.contribution_game(UA)
    N, E = frozenset(ALL), frozenset()
    phi, phiA, loo = sh.shapley(v, n), sh.shapley(vA, n), sh.leave_one_out(v, n)
    out = dict(method=a.method, U_empty_author=UA(E), vN=v(N), vN_author=vA(N), vN_general=v(N) - vA(N),
               phi=phi.tolist(), loo=loo.tolist(), loo_over_phi=(loo / phi).tolist(),
               replication_gain=[sh.replication_gain_formula(v, n, i) for i in ALL], by_strength={})
    print(f"retrained baseline U(empty): author={UA(E):.3f}   v(N)={v(N):.3f} (author {vA(N):.3f}, general {v(N) - vA(N):+.3f})")
    print(f"exact Shapley  : {np.round(phi, 3)}  (sum {phi.sum():.3f})")
    print(f"leave-one-out  : {np.round(loo, 3)}  LOO/Shapley {np.round(loo / phi, 3)}")
    print(f"replication gain by group (Prop. 2 formula, P6): {np.round(out['replication_gain'], 4)}")
    if noise:
        print("retraining seed noise (author comp.): " + ", ".join(f"{k}: sd={d['std']:.4f}" for k, d in noise.items()))
    dup = [int(x) for x in cfg["dup"].split(",")] if cfg.get("dup") else None

    hdr = "s   eps(0)   rho(0)   kappa(0)  sum_phi^ [=vN-eps]  L1(phi(eps)) author   spearman   L1(seq-set)  relearn 0->5"
    print("\n" + hdr)
    strengths = unl["strengths"]
    rows = []
    for s in strengths:
        sd = unl["set"][str(s)]
        Uh = sh.as_game(table(sd, Utot)); UhA = sh.as_game(table(sd, Uaut))
        r = sh.additive_bias_check(U, Uh, n)
        eps = sh.residual_game(Uh, U); epsA = sh.residual_game(UhA, UA)
        full = sd["0000"]; fe = ret["0000"]
        rho = sum(full["groups"][j] - fe["groups"][j] for j in ALL) / n
        kappa = -(full["general"] - fe["general"])
        assert abs((rho - kappa) - eps(E)) < 1e-9
        l1 = float(np.abs(sh.shapley(epsA, n)).sum())
        rank = spearman(r["phi_hat"], phi) if np.ptp(r["phi_hat"]) > 0 and np.ptp(phi) > 0 else float("nan")
        # sequential estimate on the author component along the sampled/enumerated removal orders
        seq = {k: float(np.mean(e["groups"])) for k, e in unl["seq"][str(s)].items()}
        orders = [tuple(o) for o in unl["orders"]]
        phi_seq, _, sums = sh.sequential_estimate(lambda p: seq[str(tuple(p))], n, orders)
        l1_seq = float(np.abs(phi_seq - sh.shapley(sh.estimated_game(UhA, UA(E)), n)).sum())
        d = dict(eps_empty=eps(E), rho_empty=rho, kappa_empty=kappa, sum_phi_hat=r["sum_hat"], sum_err=r["sum_err"],
                 decomposition_err=r["decomposition_err"], l1_phi_eps_author=l1, spearman=rank,
                 phi_hat=r["phi_hat"].tolist(), phi_seq_author=phi_seq.tolist(), l1_seq_vs_set_author=l1_seq,
                 unlearned_author_at_empty=Uaut(full))
        if unl["relearn"].get(str(s)):
            d["relearn"] = unl["relearn"][str(s)]
        if len(orders) == 24:                                             # P5: exact identity + Prop 5 bound
            chk = sh.sequential_bias_check(UA, lambda p: seq[str(tuple(p))], n)
            d.update(prop4_sum_err=chk["sum_err"], prop5_gap=chk["prop5_gap"], prop5_bound=chk["prop5_bound"],
                     path_gap_lower_bound=chk["path_gap_lower_bound"])
        if dup:
            d["bias_slope_on_k"] = float(np.polyfit(dup, np.array(d["phi_hat"]) - phi, 1)[0])
        out["by_strength"][str(s)] = d
        rl = d.get("relearn")
        print(f"{s:<3} {eps(E):+8.3f} {rho:+8.3f} {kappa:+8.3f}   {r['sum_hat']:+8.3f} [{v(N) - eps(E):+.3f}]      {l1:8.3f}"
              f"           {rank:+6.2f}     {l1_seq:8.3f}      "
              + (f"{rl['before']:.3f} -> {rl['after']:.3f}" if rl else "-"))
        rows.append((s, eps(E), rho, kappa, rl))
    if unl.get("relearn_control"):
        out["relearn_control"] = unl["relearn_control"]
        c = unl["relearn_control"]
        print(f"\nrelearning control on the RETRAINED {{}}-model: {c['before']:.3f} -> {c['after']:.3f}  "
              f"(only the part above this is attributable to residual knowledge)")
    if any("prop4_sum_err" in d for d in out["by_strength"].values()):
        print("\nP5 / Prop. 4-5 with all 24 removal orders (author component):")
        for s, d in out["by_strength"].items():
            print(f"  s={s}: sum identity err={d['prop4_sum_err']:.1e}  Prop5 gap={d['prop5_gap']:.4f} <= bound={d['prop5_bound']:.4f}"
                  f"  half order-gap on full set={d['path_gap_lower_bound']:.4f}")
    # sign change of eps(empty) by linear interpolation (Section 6.4 reports ~19 steps/group)
    e = [r[1] for r in rows]; ss = [r[0] for r in rows]
    for k in range(len(e) - 1):
        if e[k] > 0 >= e[k + 1]:
            out["sign_change_steps_per_group"] = ss[k] + (ss[k + 1] - ss[k]) * e[k] / (e[k] - e[k + 1])
            print(f"\neps(empty) changes sign at about {out['sign_change_steps_per_group']:.1f} steps per group")
    json.dump(out, open(os.path.join(a.dir, f"analysis_{a.method}.json"), "w"), indent=1)

    try:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(9, 3.4))
        ax[0].axhline(0, c="k", lw=.6); ax[0].plot(ss, e, "o-", label=r"$\varepsilon(\emptyset)$")
        ax[0].plot(ss, [r[2] for r in rows], "s--", label=r"$\kappa(\emptyset)$"); ax[0].set_xlabel("steps per group"); ax[0].legend()
        ax[0].set_title("Aggregate bias vs. unlearning strength")
        ok = [r for r in rows if r[4]]
        if ok:
            ax[1].plot([r[0] for r in ok], [r[4]["before"] for r in ok], "o-", label="before attack")
            ax[1].plot([r[0] for r in ok], [r[4]["after"] for r in ok], "s-", label="after relearning")
            ax[1].axhline(UA(E), c="gray", ls=":", label="retrained baseline")
            if "relearn_control" in out:
                ax[1].axhline(out["relearn_control"]["after"], c="r", ls=":", label="retrained + attack")
            ax[1].set_xlabel("steps per group"); ax[1].set_title("Author performance at T = {}"); ax[1].legend(fontsize=7)
        fig.tight_layout(); fig.savefig(os.path.join(a.dir, f"eps_vs_strength_{a.method}.png"), dpi=150)
    except Exception as ex:                                               # plotting is optional
        print("plot skipped:", ex)


if __name__ == "__main__":
    main()
