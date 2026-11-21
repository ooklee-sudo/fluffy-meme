"""Reproduce the drift analysis (Table 2) and the policy table (Table 3) of the IJDS manuscript.

Inputs: results/gpu8_gsm8k_seed0_firstpass.csv (1-2B runs) and results/pairs/*.json (70M-410M CPU runs).
Usage:  python analyze_drift.py
"""
import csv
import glob
import json
import math
from dataclasses import replace

import numpy as np
from scipy import stats
from scipy.optimize import brentq

import real_options as ro

SIZES = {"pythia-70m": 0.07, "pythia-160m": 0.16, "pythia-410m": 0.41}


def median_drift(r):
    d = sorted(v["drift"] for v in r["act_info"].values())
    return d[len(d) // 2]


def load():
    rows = list(csv.DictReader(open("results/gpu8_gsm8k_seed0_firstpass.csv")))
    cp = []  # (family, pair, params_b, drift, R_C)
    for r in rows:
        if r["upgrade_type"] == "continued_pretraining":
            fam = "olmo2-1b" if r["family"] == "olmo2" else r["pair"].split()[0]
            cp.append((fam, r["pair"], float(r["params_b"]), float(r["drift"]), float(r["R_C"])))
    for p in sorted(glob.glob("results/pairs/pythia*.json")) + sorted(glob.glob("results/pairs_seeds/*.json")):
        r = json.load(open(p))
        fam = r["pair"].split()[0]
        cp.append((fam, r["pair"], SIZES[fam], median_drift(r), r["recovery"][0]["R_C"]))
    return rows, cp


def drift_table(cp):
    fams = sorted({c[0] for c in cp})
    series = {f: sorted([c for c in cp if c[0] == f and "seed1" not in c[1]], key=lambda c: c[3]) for f in fams}
    multi = [f for f in fams if len(series[f]) >= 3]
    for f in multi:
        rho = stats.spearmanr([c[3] for c in series[f]], [c[4] for c in series[f]]).statistic
        print(f"Spearman(drift, R_C) {f:12s} {rho:+.2f}  (n={len(series[f])})")

    def slope(groups):  # common slope of log(1-R) on drift with family fixed effects
        xs, ys = [], []
        for g in groups:
            d = np.array([c[3] for c in series[g]])
            y = np.log(1 - np.array([c[4] for c in series[g]]))
            xs.append(d - d.mean()); ys.append(y - y.mean())
        xs, ys = np.concatenate(xs), np.concatenate(ys)
        return xs @ ys / (xs @ xs)

    for calib in ("largest", "smallest"):
        err = []
        for f in multi:
            b = slope([g for g in multi if g != f])
            c0 = series[f][-1] if calib == "largest" else series[f][0]
            a = math.log(1 - c0[4]) - b * c0[3]
            err += [abs(1 - math.exp(a + b * c[3]) - c[4]) for c in series[f] if c is not c0]
        print(f"within family, calibrated on {calib:8s}: n={len(err)} MAE={np.mean(err):.3f} max={max(err):.3f}")

    X = np.array([[1, c[3], math.log10(c[2])] for c in cp]); y = np.array([math.log(1 - c[4]) for c in cp])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    print(f"pooled in-sample R^2 = {1 - ((y - X @ b) ** 2).sum() / ((y - y.mean()) ** 2).sum():.2f}")
    err = []
    for f in fams:
        tr = [i for i, c in enumerate(cp) if c[0] != f]
        bb, *_ = np.linalg.lstsq(X[tr], y[tr], rcond=None)
        err += [abs(1 - math.exp(X[i] @ bb) - cp[i][4]) for i, c in enumerate(cp) if c[0] == f]
    print(f"pooled, family left out: n={len(err)} MAE={np.mean(err):.3f} max={max(err):.3f}")


def policy_table(rows):
    p = ro.Params()
    print(f"\nbeta = {ro.beta(p):.2f}")
    print(f"{'pair':22s} {'R_C':>6s} {'v*_C':>7s} {'C_A':>5s} {'Gamma':>6s} {'breakeven':>9s}")
    for r in rows:
        RC, RA, C = max(min(float(r["R_C"]), 0.999), 0.0), min(float(r["R_A"]), 0.999), float(r["C_A_over_C_N"])
        q = replace(p, C_A=C)
        G = ro.gamma(max(RA, 0.0), RC, q)
        be = brentq(lambda x: ro.gamma(x, RC, q) - C, RC + 1e-6, 0.9989)
        print(f"{r['pair']:22s} {float(r['R_C']):6.3f} {ro.v_star(RC, q):7.2f} {C:5.2f} {G:6.3f} {be:9.3f}")


if __name__ == "__main__":
    rows, cp = load()
    drift_table(cp)
    policy_table(rows)
