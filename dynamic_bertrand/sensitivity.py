"""Sensitivity, equilibrium-selection and proposition checks for the dynamic Bertrand MPE.

python sensitivity.py [--workers 4]        # writes results/sensitivity/*.json and sensitivity_summary.json
"""
import argparse
import glob
import json
import os
from dataclasses import replace
from multiprocessing import Pool

import numpy as np

from bertrand_mpe import Game, Params

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results", "sens2")
BASE = Params()
PERSIST = ((0.9, 0.07, 0.03), (0.05, 0.9, 0.05), (0.03, 0.07, 0.9))
IID = ((1 / 3,) * 3,) * 3
GROWTH = ((0.4, 0.3, 0.3), (0.2, 0.4, 0.4), (0.1, 0.2, 0.7))

SCENARIOS = {
    "base": BASE,
    "rho=0.5": replace(BASE, rho=0.5), "rho=2": replace(BASE, rho=2.0), "rho=4": replace(BASE, rho=4.0),
    "mc=0.1": replace(BASE, mc=0.1), "mc=0.2": replace(BASE, mc=0.2), "mc=0.4": replace(BASE, mc=0.4),
    "fc x0.5": replace(BASE, fc=(6.0, 7.5)), "fc x2": replace(BASE, fc=(24.0, 30.0)),
    "fc symmetric (13.5,13.5)": replace(BASE, fc=(13.5, 13.5)),
    "demand persistent": replace(BASE, P_lam=PERSIST), "demand iid": replace(BASE, P_lam=IID),
    "demand growth-skewed": replace(BASE, P_lam=GROWTH),
    "beta=0.9": replace(BASE, beta=0.9), "beta=0.98": replace(BASE, beta=0.98),
    "grid 8 prices": replace(BASE, prices=tuple(np.round(np.linspace(0.4, 1.5, 8), 4))),
    "grid 16 prices": replace(BASE, prices=tuple(np.round(np.linspace(0.4, 1.5, 16), 4))),
    "sla=0": replace(BASE, sla=0.0), "sla=0.6": replace(BASE, sla=0.6),
    "price ratio 0.31 (8 prices)": replace(BASE, prices=tuple(np.round(np.linspace(0.465, 1.5, 8), 4))),
}


def pure_ne_prices(p):
    """Proposition 3: symmetric pure NE prices of the stage game when K_A, K_B >= lambda."""
    pr = list(p.prices)
    ne = [pr[0]]
    for k in range(1, len(pr)):
        if pr[k - 1] - p.mc <= (pr[k] - p.mc) / 2 + 1e-12:
            ne.append(pr[k])
    return ne


def checks(g, p):
    """Numerical checks of Propositions 1 and 3 and of price monotonicity in rival capacity."""
    pr = np.array(p.prices)
    sA, sB = g.sigma
    PA, _ = g.action_parts(sA)
    PB, _ = g.action_parts(sB)
    Ep = 0.5 * (PA @ pr + PB @ pr)
    out = {}
    # Prop 1: scarcity => top price strictly dominant => modal price is the top price
    dom_ok, modal_ok, n1 = True, True, 0
    for a in range(p.M):
        for b in range(p.M):
            for l, D in enumerate(p.lam):
                if p.kappa * (a + b) <= D and a > 0 and b > 0:
                    n1 += 1
                    prof = g.profit[0][a, b, l]          # (pa, pb)
                    dom_ok &= bool((prof[-1, :][None, :] > prof[:-1, :]).all())
                    modal_ok &= bool(PA[a, b, l].argmax() == len(pr) - 1 and PB[a, b, l].argmax() == len(pr) - 1)
    out["prop1_states"] = n1
    out["prop1_top_price_strictly_dominant"] = dom_ok
    out["prop1_top_price_modal"] = modal_ok
    # Prop 3: abundance => symmetric pure NE; compare to QRE modal price
    ne = pure_ne_prices(p)
    modal = []
    for a in range(p.M):
        for b in range(p.M):
            for l, D in enumerate(p.lam):
                if p.kappa * min(a, b) >= D:
                    modal.append((float(pr[PA[a, b, l].argmax()]), float(pr[PB[a, b, l].argmax()])))
    out["prop3_ne_prices"] = [float(x) for x in ne]
    out["prop3_states"] = len(modal)
    out["prop3_modal_in_ne_set"] = bool(all(x in [float(y) for y in ne] and y in [float(z) for z in ne] for x, y in modal)) if modal else None
    out["prop3_mean_modal_price"] = float(np.mean([x for x, _ in modal])) if modal else None
    # monotonicity: A's expected price non-increasing in rival nodes (and B's in A's)
    EA, EB = PA @ pr, PB @ pr
    tot, viol = 0, 0
    for l in range(len(p.lam)):
        for a in range(p.M):
            d = np.diff(EA[a, :, l]); tot += len(d); viol += int((d > 1e-6).sum())
        for b in range(p.M):
            d = np.diff(EB[:, b, l]); tot += len(d); viol += int((d > 1e-6).sum())
    out["price_monotone_violations"] = viol
    out["price_monotone_pairs"] = tot
    # price when capacity is abundant vs scarce
    out["mean_E_price_abundant"] = float(np.mean([Ep[a, b, l] for a in range(p.M) for b in range(p.M) for l, D in enumerate(p.lam) if p.kappa * min(a, b) >= D])) if modal else None
    return out


def solve_models(p, init_k=None, init_V=None, cartel=True):
    res = {}
    g = Game(p).solve_decoupled(init_k=init_k, init_V=init_V)
    res["bertrand"] = {**{k: v for k, v in g.summary().items() if k != "stationary"},
                       "converged": bool(g.converged), "iters": int(g.outer_iters), "stage_gap": float(g.stage_gap)}
    ck = checks(g, p)
    if cartel:
        gc = Game(p).solve_cartel()
        res["cartel"] = {**{k: v for k, v in gc.summary().items() if k != "stationary"}, "converged": bool(gc.converged)}
        gs = Game(replace(p, competition="share", prices=(p.prices[-1],))).solve_decoupled()
        res["share"] = {**{k: v for k, v in gs.summary().items() if k != "stationary"}, "converged": bool(gs.converged)}
    return res, ck


def fname(name, start):
    key = name.replace(" ", "_").replace("(", "").replace(")", "").replace(",", "_").replace("/", "")
    return os.path.join(OUT, f"scn_{key}__start{start}.json")


def run_scenario(item):
    """One scenario from one starting point: start 0 = uniform strategies, k>0 = random start k."""
    name, p, start = item
    f = fname(name, start)
    if os.path.exists(f):
        return name, start
    if start == 0:
        res, ck = solve_models(p)
    else:
        rng = np.random.default_rng(1000 + start)
        S, L = p.M * p.M, len(p.lam)
        init_k = (rng.dirichlet(np.ones(3), S * L), rng.dirichlet(np.ones(3), S * L))
        init_V = (rng.uniform(0, 150, (p.M, p.M, L)), rng.uniform(0, 150, (p.M, p.M, L)))
        res, ck = solve_models(p, init_k, init_V, cartel=False)
    json.dump({"name": name, "start": start,
               "params": {k: (list(v) if isinstance(v, tuple) else v) for k, v in p.__dict__.items()},
               "models": res, "checks": ck}, open(f, "w"), indent=1, default=lambda o: list(o))
    return name, start


def run_seed(seed):
    f = os.path.join(OUT, f"seed_{seed:02d}.json")
    if os.path.exists(f):
        return seed
    rng = np.random.default_rng(seed)
    S = BASE.M * BASE.M * len(BASE.lam)
    init_k = (rng.dirichlet(np.ones(3), S), rng.dirichlet(np.ones(3), S))
    init_V = (rng.uniform(0, 150, (BASE.M, BASE.M, len(BASE.lam))), rng.uniform(0, 150, (BASE.M, BASE.M, len(BASE.lam))))
    res, ck = solve_models(BASE, init_k, init_V, cartel=False)
    json.dump({"seed": seed, "bertrand": res["bertrand"]}, open(f, "w"), indent=1)
    return seed


def summarize():
    sc = {}
    for f in sorted(glob.glob(os.path.join(OUT, "scn_*.json"))):
        d = json.load(open(f)); sc.setdefault(d["name"], {})[str(d["start"])] = d
    seeds = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(OUT, "seed_*.json")))]
    json.dump({"scenarios": sc, "seeds": seeds}, open(os.path.join(os.path.dirname(OUT), "sens2_summary.json"), "w"), indent=1)
    return sc, seeds


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seeds", type=int, default=0)
    ap.add_argument("--starts", type=int, default=3)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    with Pool(a.workers) as pool:
        tasks = [(n, p, st) for n, p in SCENARIOS.items() for st in range(a.starts + 1)]
        for n in pool.imap_unordered(run_scenario, tasks):
            print("done", n, flush=True)
        for s in pool.imap_unordered(run_seed, range(a.seeds)):
            print("seed", s, flush=True)
    summarize()
    print("finished")
