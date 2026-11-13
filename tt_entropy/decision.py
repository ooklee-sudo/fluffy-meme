"""EXPLORATORY decision simulation (not preregistered): if a firm can personalize only k of its N tenants,
how much of the total personalization gain does each selection rule capture?

Rules (all use only information available before any adapter is trained):
  oracle             the true gains (upper bound; not available in practice)
  entropy            gradient entropy, high first (needs the gradient probe for every tenant)
  ttr / distinct /   one simple trait each; the direction (high or low first) is learned on the OTHER sample
  resp_len / nll_none
  traits model       linear regression of the outcome on the four traits, fit on the OTHER sample
  traits + entropy   the same with gradient entropy added, fit on the OTHER sample
  random             expected share = k / N
Each rule is built on one sample and scored on another, so nothing is fit on the tenants it ranks.

Outcomes: relative gain (H1' outcome) and best gain (absolute NLL reduction).

Cost: training one adapter (one bond dimension, one seed, 300 steps) costs 1 unit; one gradient probe costs
--probe-cost units. Default 0.25: on an RTX 5070 Laptop a probe took about 0.2-0.3 min and one adapter run
about 1 min (10 runs per brand took about 10 min). Rules that need the probe pay N x probe-cost on top of the
k adapters; trait rules need no probe.

Usage: python decision.py [--probe-cost 0.25] [results/phase1_value results/phase1_confirm]
"""
import argparse
import os
import warnings

import numpy as np
from scipy.stats import spearmanr

from explore import load

warnings.filterwarnings("ignore", message=".*constant.*")
TRAITS = ["ttr", "distinct", "resp_len", "nll_none"]
SHARES = [0.1, 0.2, 1 / 3, 0.5]


def zfit(train, feats, y):
    x = np.array([[r[f] for f in feats] for r in train], float)
    mu, sd = x.mean(0), x.std(0) + 1e-12
    xa = np.column_stack([np.ones(len(train)), (x - mu) / sd])
    beta = np.linalg.lstsq(xa, np.array([r[y] for r in train]), rcond=None)[0]
    return lambda rows: np.column_stack([np.ones(len(rows)), (np.array([[r[f] for f in feats] for r in rows], float) - mu) / sd]) @ beta


def rules(train, y):
    out = {"oracle": lambda rows: np.array([r[y] for r in rows])}
    for f in ["entropy"] + TRAITS:
        sign = np.sign(spearmanr([r[f] for r in train], [r[y] for r in train])[0]) or 1.0
        out[f] = (lambda f_, s_: lambda rows: s_ * np.array([r[f_] for r in rows]))(f, sign)
    out["traits model"] = zfit(train, TRAITS, y)
    out["traits + entropy"] = zfit(train, TRAITS + ["entropy"], y)
    return out


def captured(rows, score, y, k):
    order = np.argsort(-score(rows), kind="stable")[:k]
    total = sum(r[y] for r in rows)
    return sum(rows[i][y] for i in order) / total


def evaluate(train_name, train, test_name, test, y, probe_cost):
    n = len(test)
    print(f"\n--- outcome: {y}; rules built on {train_name}, scored on {test_name} (N = {n}) ---")
    ks = sorted({max(1, round(s * n)) for s in SHARES})
    print(f"{'rule':<18}" + "".join(f"{'top ' + str(k):>9}" for k in ks) + f"{'k for 50%':>11}{'k for 80%':>11}")
    rs = rules(train, y)
    rows_out = {}
    for name, score in list(rs.items()) + [("random", None)]:
        if score is None:
            caps = [k / n for k in ks]
            k50, k80 = int(np.ceil(0.5 * n)), int(np.ceil(0.8 * n))
        else:
            caps = [captured(test, score, y, k) for k in ks]
            full = [captured(test, score, y, k) for k in range(1, n + 1)]
            k50 = next(k for k, c in enumerate(full, 1) if c >= 0.5)
            k80 = next(k for k, c in enumerate(full, 1) if c >= 0.8)
        rows_out[name] = (caps, k50, k80)
        print(f"{name:<18}" + "".join(f"{c:>9.1%}" for c in caps) + f"{k50:>11}{k80:>11}")
    # cost to capture 50% of the gain, in adapter-training units
    print(f"  cost to capture 50% of total gain (adapter = 1, probe = {probe_cost}):")
    for name in ["entropy", "traits model", "traits + entropy", "random"]:
        k50 = rows_out[name][1]
        cost = k50 + (n * probe_cost if "entropy" in name else 0)
        print(f"    {name:<18}{cost:>7.1f}   (personalize {k50} of {n})")
    return rows_out


def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("dirs", nargs="*", default=["results/phase1_value", "results/phase1_confirm"])
    a.add_argument("--probe-cost", type=float, default=0.25)
    args = a.parse_args()
    dirs = [d for d in args.dirs if os.path.isdir(d)]
    if len(dirs) < 2:
        raise SystemExit("need two result folders (rules are built on one and scored on the other)")
    samples = {d: [r for r in load(d) if r["best_gain"] > 0] for d in dirs[:2]}
    (na, ra), (nb, rb) = samples.items()
    print("EXPLORATORY decision simulation; share of the sample's total gain captured by personalizing the top k.")
    for y in ["rel_gain", "best_gain"]:
        evaluate(nb, rb, na, ra, y, args.probe_cost)
        evaluate(na, ra, nb, rb, y, args.probe_cost)
    print("\nWith 30 tenants per sample, differences of a few points are noise. The question is whether entropy-based"
          "\nrules beat the trait rules consistently, in both directions and for both outcomes.")


if __name__ == "__main__":
    main()
