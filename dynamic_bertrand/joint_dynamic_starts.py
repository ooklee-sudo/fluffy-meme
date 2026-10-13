"""Multiple-start check for the joint dynamic-pricing game and its simultaneous-move comparison (rho = 2, 8 prices)."""
import json, os
from dataclasses import replace
from multiprocessing import Pool
import numpy as np
from alternating import AltGame
from bertrand_mpe import Game, Params

HERE = os.path.dirname(os.path.abspath(__file__))
prices = tuple(np.round(np.linspace(0.4, 1.5, 8), 4))
RHO = 2.0
p = replace(Params(), prices=prices, rho=RHO)
M, L, NP = p.M, len(p.lam), len(p.prices)


def alt_start(seed):
    rng = np.random.default_rng(seed)
    V0 = {q: {i: rng.uniform(0, 150, (M, M, L, NP)) for i in (0, 1)} for q in (0, 1)} if seed else None
    g = AltGame(p).solve(tol=1e-9, vdamp=0.5, max_iter=20000, V0=V0)
    s = g.summary()
    return dict(seed=seed, converged=bool(g.converged), **{k: float(s[k]) for k in ("avg_price", "profit_total", "consumer_surplus", "mean_capacity", "excess_capacity", "mean_nodes_A", "mean_nodes_B")})


def static_start(seed):
    rng = np.random.default_rng(seed)
    S = M * M * L
    kw = {}
    if seed:
        kw = dict(init_k=(rng.dirichlet(np.ones(3), S), rng.dirichlet(np.ones(3), S)),
                  init_V=(rng.uniform(0, 150, (M, M, L)), rng.uniform(0, 150, (M, M, L))))
    g = Game(p).solve_decoupled(**kw)
    s = g.summary()
    return dict(seed=seed, converged=bool(g.converged), **{k: float(s[k]) for k in ("avg_price", "profit_total", "consumer_surplus", "mean_capacity", "excess_capacity", "mean_nodes_A", "mean_nodes_B")})


if __name__ == "__main__":
    with Pool(4) as pool:
        alt = pool.map(alt_start, range(0, 9))
        sta = pool.map(static_start, range(0, 9))
    json.dump({"rho": RHO, "alternating": alt, "simultaneous": sta}, open(os.path.join(HERE, "results", "joint_dynamic_starts.json"), "w"), indent=1)
    for name, rows in (("alternating", alt), ("simultaneous", sta)):
        print(name)
        for r in rows:
            print("  seed", r["seed"], r["converged"], "cap=%.1f p=%.3f pi=%.2f CS=%.2f" % (r["mean_capacity"], r["avg_price"], r["profit_total"], r["consumer_surplus"]))
