"""Estimate the ambiguity-averse reviewer model, per model, from the code objection runs.

Parameters
  k    cost ratio: approving buggy code costs k times as much as rejecting good code
  eps  ambiguity: half-width of the interval of objector reliabilities the reviewer considers
  c    credibility of the stated reliability (1: taken at face value, 0: ignored)
  m    default trust in users: the centre of the interval when the stated reliability is ignored
Re-checking is modelled as in ambiguity_receiver.simulate_types: with probability s (one value per
direction, set so that the model reproduces the observed re-check flip rate exactly) the turn-1
confidence p is redrawn; an objection is then judged by the maxmin rule on top of the redrawn p.
Because p'(r) falls in r, the worst cases sit at the two ends of the interval, so the rule is exact:
  approved code, "bug" claim:      switch iff k (1 - p'(r_hi)) > p'(r_lo)
  rejected code, "correct" claim:  switch iff (1 - p'(r_hi)) > k p'(r_lo)

Data: flip counts on items the model approved / rejected at turn 1, under
  doubt (no stated reliability: centre m), track20, track50, track80 (centre c r + (1 - c) m),
with re-check as the baseline. Items shared by all runs only. Binomial likelihood, grid search,
parametric bootstrap for intervals. The Bayesian special case (eps = 0, c = 1) is fitted as well
and compared by a likelihood-ratio statistic and AIC.

Assumption to keep in mind: turn-1 confidence is uniform above the verdict threshold (API models give
no probabilities). The parameters therefore describe the pattern of responses; they are not a
calibrated measurement of beliefs.

Example:
  python fit_reviewer.py runs/api_haiku runs/api_luna runs/api_deepseek
  python fit_reviewer.py --prefix-style open runs/code_q4b   (laptop: code_q4b_1024 is the doubt run)
  python fit_reviewer.py runs/code_q8b                       (laptop, after run_code_conditions.bat 8b)
"""

import argparse
import itertools
import json
import os

import numpy as np

CONDS = {"doubt": None, "track20": 0.2, "track50": 0.5, "track80": 0.8}
GRID = {"k": [1, 1.5, 2, 3, 4, 6, 8], "eps": [0.0, 0.05, 0.1, 0.2, 0.3, 0.4],
        "c": [0.0, 0.25, 0.5, 0.75, 1.0], "m": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]}


def said_correct(r):
    return (r["a1"] == r["gold"]) == (r["subject"] == "correct")


def load_counts(prefix, style):
    names = {"recheck": "recheck", **{c: c for c in CONDS}}
    if style == "open":
        names["doubt"] = None   # the main run is the doubt condition
    runs = {}
    for cond, suffix in names.items():
        path = f"{prefix}_{suffix}" if suffix else f"{prefix}_1024"
        f = os.path.join(path, "results.jsonl")
        if os.path.exists(f):
            with open(f) as fh:
                runs[cond] = {r["id"]: r for r in map(json.loads, filter(str.strip, fh))}
    if "recheck" not in runs:
        raise SystemExit(f"{prefix}: no re-check run")
    shared = set.intersection(*[set(v) for v in runs.values()])
    counts = {}
    for cond, rows in runs.items():
        for approved in (True, False):
            sub = [rows[i] for i in shared if said_correct(rows[i]) == approved]
            counts[(cond, approved)] = (sum(r["a2"] != r["a1"] for r in sub), len(sub))
    return counts, len(shared)


class Model:
    def __init__(self, n=3000, seed=0):
        rng = np.random.default_rng(seed)
        self.u = rng.uniform(0, 1, n)       # position of p above the threshold
        self.redraw_u = rng.uniform(0, 1, n)
        self.p_new = rng.uniform(0, 1, n)

    def p_re(self, lo, s):
        p = lo + (1 - lo) * self.u
        return np.where(self.redraw_u < s, self.p_new, p)

    @staticmethod
    def post(p, r):
        return p * (1 - r) / (p * (1 - r) + (1 - p) * r)

    def flip_rate(self, k, eps, centre, s, approved):
        lo = k / (1 + k) if approved else 1 / (1 + k)
        p = self.p_re(lo, s)
        r_lo, r_hi = np.clip(centre - eps, 1e-6, 1 - 1e-6), np.clip(centre + eps, 1e-6, 1 - 1e-6)
        a, b = self.post(p, r_hi), self.post(p, r_lo)   # worst cases
        if approved:
            sw = k * (1 - a) > b
        else:
            sw = (1 - a) > k * b
        return float(sw.mean())


def loglik(counts, model, k, eps, c, m):
    ll = 0.0
    pred = {}
    for approved in (True, False):
        lo = k / (1 + k) if approved else 1 / (1 + k)
        x0, n0 = counts[("recheck", approved)]
        s = min(1.0, (x0 / max(1, n0)) / lo)          # reproduce the re-check flip rate
        for cond, r in CONDS.items():
            if (cond, approved) not in counts:
                continue
            centre = m if r is None else c * r + (1 - c) * m
            q = np.clip(model.flip_rate(k, eps, centre, s, approved), 1e-4, 1 - 1e-4)
            x, n = counts[(cond, approved)]
            ll += x * np.log(q) + (n - x) * np.log(1 - q)
            pred[(cond, approved)] = q
    return ll, pred


def fit(counts, model, bayes=False):
    best = (-np.inf, None, None)
    eps_grid = [0.0] if bayes else GRID["eps"]
    c_grid = [1.0] if bayes else GRID["c"]
    m_grid = [0.5] if bayes else GRID["m"]
    for k, eps, c, m in itertools.product(GRID["k"], eps_grid, c_grid, m_grid):
        ll, pred = loglik(counts, model, k, eps, c, m)
        if ll > best[0]:
            best = (ll, (k, eps, c, m), pred)
    return best


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("prefixes", nargs="+")
    p.add_argument("--prefix-style", choices=["api", "open"], default="api")
    p.add_argument("--boot", type=int, default=100)
    p.add_argument("--out", default="results/reviewer_fits.json")
    args = p.parse_args()
    model = Model()
    rng = np.random.default_rng(1)
    report = {}
    for prefix in args.prefixes:
        counts, n_items = load_counts(prefix, args.prefix_style)
        ll, prm, pred = fit(counts, model)
        llb, prmb, _ = fit(counts, model, bayes=True)
        lr = 2 * (ll - llb)
        aic, aicb = 2 * 4 - 2 * ll, 2 * 1 - 2 * llb
        boots = []
        for _ in range(args.boot):
            bc = {key: (int(rng.binomial(n, x / max(1, n))), n) for key, (x, n) in counts.items()}
            boots.append(fit(bc, model)[1])
        boots = np.array(boots)
        ci = {name: (float(np.percentile(boots[:, j], 5)), float(np.percentile(boots[:, j], 95)))
              for j, name in enumerate(["k", "eps", "c", "m"])}
        name = os.path.basename(prefix)
        print(f"\n== {name}  ({n_items} items shared by all runs)")
        print("  estimate: " + ", ".join(f"{nm} = {v:g} [{ci[nm][0]:g}, {ci[nm][1]:g}]"
                                         for nm, v in zip(["k", "eps", "c", "m"], prm))
              + "   (90% bootstrap range)")
        print(f"  log-lik {ll:.1f} vs Bayesian (eps=0, c=1, m=1/2; k free, k = {prmb[0]:g}) {llb:.1f} | "
              f"LR {lr:.1f} | AIC {aic:.1f} vs {aicb:.1f}")
        print(f"  {'condition':10s} {'direction':9s} {'observed':>17s} {'fitted':>7s}")
        for approved in (True, False):
            x0, n0 = counts[("recheck", approved)]
            print(f"  {'recheck':10s} {('bug' if approved else 'correct'):9s} {x0 / max(1, n0):8.1%} of {n0:4d}   (baseline)")
            for cond in CONDS:
                if (cond, approved) in counts:
                    x, n = counts[(cond, approved)]
                    print(f"  {cond:10s} {('bug' if approved else 'correct'):9s} {x / max(1, n):8.1%} of {n:4d} "
                          f"{pred[(cond, approved)]:7.1%}")
        report[name] = {"items": n_items, "k": prm[0], "eps": prm[1], "c": prm[2], "m": prm[3], "ci90": ci,
                        "loglik": ll, "loglik_bayes": llb, "k_bayes": prmb[0], "LR": lr, "AIC": aic, "AIC_bayes": aicb,
                        "counts": {f"{c}|{'approved' if a else 'rejected'}": v for (c, a), v in counts.items()}}
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nsaved {args.out}")


if __name__ == "__main__":
    main()
