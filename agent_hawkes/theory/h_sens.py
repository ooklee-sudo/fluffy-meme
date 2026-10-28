"""Value of monitoring vs hand-off cost H (Llama-70B calibration).
Proposition 6: the value is maximised where H equals the expected cost of letting the agent finish."""
import json
import numpy as np
import learning as L
from model_core import solve, CU
est = json.load(open("../hawkes_re_results_all.json"))["swe-agent-llama-70b"]["re_hawkes"]
a, s = est["re_shape"], est["re_scale"]; mu = a * s; k, c, q = 1.0, 5.0, 0.06
cu_c = CU(mu, est["alpha"], est["delta"], k, c, q); cu_l = (k + c * mu) / q
grid = sorted(set(np.round(np.arange(16, 34.01, 0.5), 2).tolist() + [round(cu_c, 3), round(cu_l, 3), 40.0]))
rows = []
for H in grid:
    L.H = H; lv = L.learn(a, s)["learning_value"]
    sol, _ = solve(mu, est["alpha"], est["delta"], k, c, q, H)
    rows.append(dict(H=H, contagion_value=round(min(H, cu_c) - sol["W0"], 4), learning_value=round(lv, 4)))
out = dict(C_U_contagion=cu_c, C_U_learning=cu_l, rows=rows,
           argmax_contagion=max(rows, key=lambda r: r["contagion_value"])["H"],
           argmax_learning=max(rows, key=lambda r: r["learning_value"])["H"])
json.dump(out, open("h_sensitivity.json", "w"), indent=1)
print({k_: v for k_, v in out.items() if k_ != "rows"}, max(r["contagion_value"] for r in rows), max(r["learning_value"] for r in rows))
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(4.6, 3.2))
Hs = [r["H"] for r in rows]
ax.plot(Hs, [r["contagion_value"] for r in rows], color="#e07a5f", label="contagion value (μ known, α > 0)")
ax.plot(Hs, [r["learning_value"] for r in rows], color="#2a6f97", label="learning value (μ unknown, α = 0)")
ax.axvline(cu_c, ls="--", lw=0.7, color="#e07a5f"); ax.axvline(cu_l, ls="--", lw=0.7, color="#2a6f97")
ax.set_xlabel("Hand-off cost H"); ax.set_ylabel("Value of monitoring"); ax.set_xlim(16, 34)
ax.legend(fontsize=7, frameon=False); fig.tight_layout(); fig.savefig("fig_theory_H.png", dpi=200)
