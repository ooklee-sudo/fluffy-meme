"""State-level behaviour in the two equilibria found in the base scenario (uniform start vs random start 1)."""
import json, os
import numpy as np
from bertrand_mpe import Game, Params

HERE = os.path.dirname(os.path.abspath(__file__))
p = Params()
S = p.M * p.M * len(p.lam)
out = {}
rng = np.random.default_rng(1)             # same stream as the first equilibrium-selection run (seed 1)
L = len(p.lam)
init_k = (rng.dirichlet(np.ones(3), S), rng.dirichlet(np.ones(3), S))
init_V = (rng.uniform(0, 150, (p.M, p.M, L)), rng.uniform(0, 150, (p.M, p.M, L)))
lam = {"Low": 0, "Med": 1, "High": 2}
for name, kw in (("uniform_start", {}), ("random_start_seed1", dict(init_k=init_k, init_V=init_V))):
    g = Game(p).solve_decoupled(**kw)
    sm = g.summary()
    states = {f"({a},{b},{n})": g.state_report(a, b, lam[n])
              for a, b, n in [(1, 1, "Med"), (1, 1, "High"), (2, 1, "High"), (2, 2, "Med"), (2, 2, "High"), (3, 3, "Med"), (3, 3, "Low")]}
    out[name] = {"mean_capacity": sm["mean_capacity"], "avg_price": sm["avg_price"], "converged": bool(g.converged),
                 "profit_total": sm["profit_total"], "consumer_surplus": sm["consumer_surplus"],
                 "mean_nodes_A": sm["mean_nodes_A"], "mean_nodes_B": sm["mean_nodes_B"], "states": states}
    print(name, round(sm["mean_capacity"], 2), round(sm["avg_price"], 3), g.converged, flush=True)
json.dump(out, open(os.path.join(HERE, "results", "equilibria_states.json"), "w"), indent=1)
