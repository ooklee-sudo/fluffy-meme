"""Sensitivity of the dynamic-pricing vs simultaneous-pricing comparison (rho = 2, 8-price grid unless varied)."""
import json, os
from dataclasses import replace
from multiprocessing import Pool
import numpy as np
from alternating import AltGame
from bertrand_mpe import Game, Params
from sensitivity import PERSIST, IID, GROWTH

HERE = os.path.dirname(os.path.abspath(__file__))
G8 = tuple(np.round(np.linspace(0.4, 1.5, 8), 4))
B = replace(Params(), prices=G8, rho=2.0)
SC = {
    "base (rho=2, 8 prices)": B,
    "rho=3": replace(B, rho=3.0), "rho=1.7": replace(B, rho=1.7),
    "mc=0.1": replace(B, mc=0.1), "mc=0.2": replace(B, mc=0.2), "mc=0.4": replace(B, mc=0.4),
    "fc x0.5": replace(B, fc=(6.0, 7.5)), "fc x2": replace(B, fc=(24.0, 30.0)),
    "demand persistent": replace(B, P_lam=PERSIST), "demand iid": replace(B, P_lam=IID), "demand growth-skewed": replace(B, P_lam=GROWTH),
    "grid 4 prices": replace(B, prices=(0.4, 0.8, 1.2, 1.5)), "grid 16 prices": replace(B, prices=tuple(np.round(np.linspace(0.4, 1.5, 16), 4))),
    "sla=0": replace(B, sla=0.0), "sla=0.6": replace(B, sla=0.6),
    "beta=0.9": replace(B, beta=0.9), "beta=0.98": replace(B, beta=0.98),
}
KEYS = ("avg_price", "profit_total", "consumer_surplus", "mean_capacity", "excess_capacity")


def one(item):
    name, p, kind, start = item
    M, L, NP = p.M, len(p.lam), len(p.prices)
    rng = np.random.default_rng(500 + start)
    if kind == "alt":
        V0 = {q: {i: rng.uniform(0, 150, (M, M, L, NP)) for i in (0, 1)} for q in (0, 1)} if start else None
        g = AltGame(p).solve(tol=1e-9, vdamp=0.5, max_iter=30000, V0=V0)
    else:
        S = M * M * L
        kw = dict(init_k=(rng.dirichlet(np.ones(3), S), rng.dirichlet(np.ones(3), S)),
                  init_V=(rng.uniform(0, 150, (M, M, L)), rng.uniform(0, 150, (M, M, L)))) if start else {}
        g = Game(p).solve_decoupled(**kw)
    s = g.summary()
    return dict(name=name, kind=kind, start=start, converged=bool(g.converged), **{k: float(s[k]) for k in KEYS})


if __name__ == "__main__":
    tasks = [(n, p, "alt", s) for n, p in SC.items() for s in (0, 1)] + [(n, p, "sim", s) for n, p in SC.items() for s in (0, 1, 2)]
    with Pool(4) as pool:
        res = pool.map(one, tasks, chunksize=1)
    json.dump(res, open(os.path.join(HERE, "results", "joint_dynamic_sens.json"), "w"), indent=1)
    print("done", len(res))
