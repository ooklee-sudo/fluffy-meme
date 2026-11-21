"""Simulate a wide CSV with the same columns as export_csv.py, with KNOWN effects, to test analysis_study2.py.

  python quant_cost/webapp/simulate_study2.py --out /tmp/sim.csv --n 200 --incident-effect 0.4
The simulated data contain no real responses.
"""
import argparse
import math

import numpy as np
import pandas as pd

LAT = {"V1": "ABCD", "V2": "BCDA", "V3": "CDAB", "V4": "DABC"}
CELLS = [("C1", 2, 1), ("C2", 2, 2), ("C3", 6, 1), ("C4", 6, 2)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--incident-effect", type=float, default=0.4, help="reduction of the lambda slope in the incident group (SD units of S)")
    ap.add_argument("--format-effect", type=float, default=0.5, help="log-odds effect of showing cost on local choice")
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    rows = []
    for i in range(a.n):
        g = i % 8  # eight groups: news (2) crossed with Latin-square version (4), as in the survey
        inc = g % 2
        ver = list(LAT)[(g // 2) % 4]
        order = rng.permutation(4)
        u_w, u_c = rng.normal(0, 0.5), rng.normal(0, 1.0)
        r = {"pid": f"S{i:04d}", "session": "x", "completed": True, "eligible": True, "screenedOut": False, "declined": False,
             "news": "incident" if inc else "neutral", "incident": inc, "version": ver, "excluded": 0,
             "ex_attention": 0, "ex_comprehension": 0, "ex_c1": 0, "ex_speed": 0, "ex_straightline": 0,
             "GP": rng.normal(10 + 3 * inc, 5), "S8": int(rng.choice([1, 2, 3, 4], p=[.15, .4, .3, .15])),
             "P2": int(rng.integers(1, 8)), "numeracy": int(rng.integers(0, 4)), "R1": int(rng.integers(1, 8)),
             "P3_1": int(rng.choice([1, 2, 3])), "P3_2": int(rng.choice([2, 4, 5])), "P3_3": int(rng.choice([1, 6, 4]))}
        for k in range(1, 5):
            r[f"PC{k}"] = int(rng.integers(1, 8))
        ln2, ln6, loc, lns = [], [], [], []
        for j, (c, lam, perf) in enumerate(CELLS):
            slope = math.log(3) - a.incident_effect * inc  # the incident group responds less to lambda
            lnw = math.log(0.02) + u_w + (slope if lam == 6 else 0.0) + 0.2 * inc + rng.normal(0, 0.8)
            q5 = float(np.clip(4 - 0.5 * (perf == 1) + rng.normal(0, 1), 1, 7))
            p = 1 / (1 + math.exp(-(u_c + 0.8 * (lam == 6) + a.format_effect * (perf == 2) - 0.1 * q5 + 0.4)))
            local = int(rng.random() < p)
            q4 = float(np.clip(lam + rng.normal(2 * inc, 3), 0, 100))
            r.update({f"pos_{c}": int(order[j]) + 1, f"case_{c}": LAT[ver][j], f"lam_{c}": lam, f"perf_{c}": perf,
                      f"lnWTPL_{c}": lnw, f"local_{c}": local, f"Q5_{c}": q5, f"excess_{c}": q4 - lam})
            (ln6 if lam == 6 else ln2).append(lnw)
            lns.append(lnw)
            loc.append(local)
        r["S"] = np.mean(ln6) - np.mean(ln2)
        r["meanLnWTPL"] = float(np.mean(lns))
        r["n_local"] = sum(loc)
        rows.append(r)
    pd.DataFrame(rows).to_csv(a.out, index=False)
    print("wrote", a.out, len(rows), "simulated participants")


if __name__ == "__main__":
    main()
