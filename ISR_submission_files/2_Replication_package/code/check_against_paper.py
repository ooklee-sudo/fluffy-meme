"""Compare the numbers produced by this package with the numbers printed in the manuscript. Prints PASS or FAIL per item.

  python code/check_against_paper.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import arrival_robustness as AR
import monopoly_duopoly as M
import policy_regions as PR
import release_intensity as RI

rows = []
def check(name, got, want, tol):
    ok = abs(got - want) <= tol
    rows.append(ok); print(f"{'PASS' if ok else 'FAIL'}  {name}: got {got:.3f}, paper {want}, tol {tol}")

import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    out, mu, lr, p = RI.main()
for f, want in [("Llama", 1.67), ("Gemma", 1.15), ("Phi", 1.31), ("Qwen", 2.54), ("Mistral", 2.66), ("DeepSeek", 2.47)]:
    check(f"Table 3 mu_hat {f}", out[f][0], want, 0.011)
check("Table 3 pooled rate", mu, 1.97, 0.011); check("Table 3 LR statistic (T is rounded to 0.01 year in the input file)", lr, 3.43, 0.03)
for r, (v5, p5, v7, p7) in {0.3: (2.48, 1.84, 2.472, 1.830), 0.5: (2.58, 2.02, 2.574, 2.005), 0.7: (2.86, 2.61, 2.846, 2.582), 0.8: (3.30, 4.08, 3.279, 4.024)}.items():
    check(f"Table 5 muV R={r}", M.optimum(r, M.THETA, M.Em_static), v5, 0.006); check(f"Table 5 muP R={r}", M.optimum(r, 1.0, M.Em_static), p5, 0.006)
    check(f"Table 7 muV dyn R={r}", M.optimum(r, M.THETA, M.Em_dynamic), v7, 0.0006); check(f"Table 7 muP dyn R={r}", M.optimum(r, 1.0, M.Em_dynamic), p7, 0.0006)
for R, want in ((0.5, 0.928), (0.7, 0.952)):
    check(f"Section 6 duopoly mu* R={R}", M.mu_duopoly_symmetric(R), want, 0.0006)
a = M.asymmetric_check()
check("Numerical Finding 1 price (frontier)", a["prices"][0], 26.4, 0.2); check("Numerical Finding 1 price (stable)", a["prices"][1], 17.3, 0.2)
check("Numerical Finding 1 mean value (frontier)", a["mean_value"][0], 18.2, 0.15); check("Numerical Finding 1 mean value (stable)", a["mean_value"][1], 22.8, 0.15)
check("Numerical Finding 1 equilibrium: owner 1 gain from deviating on the grid", a["best_response_payoffs"][0] - a["payoffs"][0], 0.0, 0.01)
check("Numerical Finding 1 equilibrium: owner 2 gain from deviating on the grid", a["best_response_payoffs"][1] - a["payoffs"][1], 0.0, 0.01)
for fam, mu_, vc, vt, reg, G in PR.table():
    want = {"Gemma": (3.50, 6.90, 0.38), "Phi": (3.91, 7.72, 0.39), "Llama": (4.84, 9.55, 0.40), "DeepSeek": (6.87, 13.55, 0.42), "Qwen": (7.05, 13.90, 0.42), "Mistral": (7.35, 14.49, 0.42)}[fam]
    check(f"Table 4 v* copy {fam}", vc, want[0], 0.04); check(f"Table 4 v* transfer {fam}", vt, want[1], 0.08); check(f"Table 4 Gamma {fam}", G, want[2], 0.025)
want6 = {"Gemma": (0.965, 0.954), "Phi": (0.961, 0.960), "Llama": (0.980, 0.969), "Qwen": (0.984, 0.980), "Mistral": (0.990, 0.981), "DeepSeek": (0.981, 0.979)}
import csv
for r in csv.DictReader(open(os.path.join(os.path.dirname(__file__), "..", "data", "release_counts.csv"))):
    g, d = AR.multipliers(float(r["mean_gap_months"]) / 12, float(r["cv_gaps"]))
    check(f"Table 6 gamma/Poisson {r['family']}", g, want6[r["family"]][0], 0.0006); check(f"Table 6 deterministic/Poisson {r['family']}", d, want6[r["family"]][1], 0.0006)
print(f"\n{sum(rows)} of {len(rows)} checks passed")
sys.exit(0 if all(rows) else 1)
