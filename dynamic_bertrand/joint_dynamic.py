"""Capacity + alternating-move pricing: equilibrium capacity and prices versus simultaneous-move pricing.

Solves the joint game where each mover chooses (price, capacity action).  Plain value iteration converges only
for large rho; smaller rho is reached by Newton continuation.  The simultaneous-move comparison uses the same grid and rho.
"""
import json, os, time
from dataclasses import replace
import numpy as np
from alternating import AltGame
from bertrand_mpe import Game, Params

HERE = os.path.dirname(os.path.abspath(__file__))
prices = tuple(np.round(np.linspace(0.4, 1.5, 8), 4))
out = {"prices": list(prices), "runs": []}
for rho, path in ((3.0, [3.0]), (2.0, [2.0]), (1.7, [2.0, 1.7])):
    p = replace(Params(), prices=prices, rho=rho)
    t = time.time()
    alt = AltGame(p).solve_path(path) if len(path) > 1 else AltGame(p).solve(tol=1e-9, vdamp=0.5, max_iter=20000)
    row = {"rho": rho, "alt_converged": bool(alt.converged), "alt_seconds": round(time.time() - t, 1)}
    if alt.converged:
        row["alt"] = alt.summary()
    t = time.time()
    st = Game(p).solve_decoupled()
    s = st.summary()
    row["static_converged"] = bool(st.converged)
    row["static"] = {k: v for k, v in s.items() if k != "stationary"}
    row["static_seconds"] = round(time.time() - t, 1)
    out["runs"].append(row)
    a = row.get("alt")
    print(f"rho={rho}: alt conv={row['alt_converged']}", None if not a else
          {k: round(float(a[k]), 3) for k in ("avg_price", "profit_total", "consumer_surplus", "mean_capacity")},
          "| static conv=%s" % row["static_converged"],
          {k: round(float(s[k]), 3) for k in ("avg_price", "profit_total", "consumer_surplus", "mean_capacity")}, flush=True)
    json.dump(out, open(os.path.join(HERE, "results", "joint_dynamic.json"), "w"), indent=1, default=float)
