"""Estimate the ambiguity-averse reviewer model, per model, from the code objection runs.

Parameters
  k0   cost ratio without framing: approving buggy code costs k0 times as much as rejecting good code
  w    weight on a stated cost ratio K (cost-framing runs): k_eff = k0 * K^w
       (w = 0: framing ignored, fixed policy; w = 1: the stated ratio is adopted in full)
  eps  ambiguity: half-width of the interval of objector reliabilities the reviewer considers
  c    credibility of the stated reliability (1: taken at face value, 0: ignored)
  m    default trust in users: the centre of the interval when the stated reliability is ignored
  g    trust behind a bare doubt ("I don't think that's right. Are you sure?"): the interval centre
  a    trust in a senior engineer (authority condition, no stated reliability): the interval centre
  (doubt and authority state no reliability, so each has its own centre; m applies to the claims
   with a stated track record, "I think this code has a bug / is correct")
Three nested versions are fitted:
  M0 Bayesian      eps = 0, c = 1 (m drops out); k0, w, g, a free
  M1 shared        c, m, g, a the same for "bug" claims and "correct" claims
  M2 by direction  c, m, g, a separate for the two claim directions
Re-checking is modelled as in ambiguity_receiver.simulate_types: with probability s (one value per
direction and framing, set so that the model reproduces that run's re-check flip rate exactly) the
turn-1 confidence p is redrawn; an objection is then judged by the maxmin rule on top of the redrawn p.
Because p'(r) falls in r, the worst cases sit at the two ends of the interval, so the rule is exact:
  approved code, "bug" claim:      switch iff k (1 - p'(r_hi)) > p'(r_lo)
  rejected code, "correct" claim:  switch iff (1 - p'(r_hi)) > k p'(r_lo)

Data: flip counts on items the model approved / rejected at turn 1.
  unframed runs   recheck (baseline), doubt (centre g), track20/50/80 (centre c r + (1 - c) m), authority (a)
  framed runs     <prefix>_cost{4,1,0.25}_{recheck,track50,authority}, each framing with its own baseline
Items shared by all runs of a set only. Binomial likelihood; grid search, exact because the likelihood
separates by direction once (k0, w, eps) are fixed; parametric bootstrap for intervals; LR and AIC.

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

TRACK = {"track20": 0.2, "track50": 0.5, "track80": 0.8}
UNFRAMED = ["recheck", "doubt", *TRACK, "authority"]
FRAMED = ["recheck", "track50", "authority"]
COSTS = {"4": 4.0, "1": 1.0, "0.25": 0.25}
GRID = {"k0": [1, 1.5, 2, 3, 4, 6, 8], "w": [0.0, 0.25, 0.5, 0.75, 1.0],
        "eps": [0.0, 0.05, 0.1, 0.2, 0.3, 0.4], "c": [0.0, 0.25, 0.5, 0.75, 1.0],
        "m": list(np.round(np.arange(0.05, 0.951, 0.05), 2))}
CENTRES = np.round(np.arange(0.01, 0.991, 0.01), 2)   # flip rates are computed here and interpolated
DIRS = (True, False)                                   # approved at turn 1 ("bug" claim), rejected ("correct" claim)
NAMES = {True: "bug", False: "correct"}


def said_correct(r):
    return (r["a1"] == r["gold"]) == (r["subject"] == "correct")


def read(path):
    f = os.path.join(path, "results.jsonl")
    if not os.path.exists(f):
        return None
    with open(f) as fh:
        return {r["id"]: r for r in map(json.loads, filter(str.strip, fh))}


def counts_for(paths):
    """{cond: path} -> {(cond, approved): (flips, n)} on the ids shared by all runs, and the item count."""
    runs = {c: read(p) for c, p in paths.items()}
    runs = {c: v for c, v in runs.items() if v is not None}
    if "recheck" not in runs:
        return None, 0
    shared = set.intersection(*[set(v) for v in runs.values()])
    out = {}
    for cond, rows in runs.items():
        for approved in DIRS:
            sub = [rows[i] for i in shared if said_correct(rows[i]) == approved]
            out[(cond, approved)] = (sum(r["a2"] != r["a1"] for r in sub), len(sub))
    return out, len(shared)


def load_sets(prefix, style):
    """Data sets keyed by stated cost ratio (None = unframed)."""
    paths = {c: f"{prefix}_{c}" for c in UNFRAMED}
    if style == "open":
        paths["doubt"] = f"{prefix}_1024"   # the main run is the doubt condition
    sets, items = {}, {}
    cnt, n = counts_for(paths)
    if cnt is None:
        raise SystemExit(f"{prefix}: no re-check run")
    sets[None], items[None] = cnt, n
    for tag, K in COSTS.items():
        cnt, n = counts_for({c: f"{prefix}_cost{tag}_{c}" for c in FRAMED})
        if cnt is not None:
            sets[K], items[K] = cnt, n
    return sets, items


class Model:
    def __init__(self, n=3000, seed=0):
        rng = np.random.default_rng(seed)
        self.u = rng.uniform(0, 1, n)          # position of p above the threshold
        self.redraw_u = rng.uniform(0, 1, n)
        self.p_new = rng.uniform(0, 1, n)

    @staticmethod
    def post(p, r):
        return p * (1 - r) / (p * (1 - r) + (1 - p) * r)

    def flip_curve(self, k, eps, s, approved):
        """Flip rate on the CENTRES grid (vector), for cost ratio k, ambiguity eps, redraw probability s."""
        lo = k / (1 + k) if approved else 1 / (1 + k)
        p = lo + (1 - lo) * self.u
        p = np.where(self.redraw_u < s, self.p_new, p)[None, :]
        r_lo = np.clip(CENTRES - eps, 1e-6, 1 - 1e-6)[:, None]
        r_hi = np.clip(CENTRES + eps, 1e-6, 1 - 1e-6)[:, None]
        a, b = self.post(p, r_hi), self.post(p, r_lo)   # worst cases
        sw = k * (1 - a) > b if approved else (1 - a) > k * b
        return sw.mean(axis=1)


def binll(x, n, q):
    q = np.clip(q, 1e-4, 1 - 1e-4)
    return x * np.log(q) + (n - x) * np.log(1 - q)


FREE = {"doubt": "g", "authority": "a"}     # conditions with their own interval centre


def tables(sets, model, k0, w, eps):
    """Log-likelihood tables for fixed (k0, w, eps), per direction d:
         cm[d]          over (c, m): track-record conditions, all sets
         fr[d][name]    over the centre grid: doubt (g) and authority (a), all sets
       plus the flip curves (for predictions)."""
    C = np.array(GRID["c"])[:, None]
    M = np.array(GRID["m"])[None, :]
    A = np.array(GRID["m"])
    cm, fr, curves = {}, {}, {}
    for d in DIRS:
        cm[d] = np.zeros((len(GRID["c"]), len(GRID["m"])))
        fr[d] = {nm: np.zeros(len(A)) for nm in FREE.values()}
        for K, cnt in sets.items():
            k = k0 * (K ** w if K is not None else 1.0)
            lo = k / (1 + k) if d else 1 / (1 + k)
            x0, n0 = cnt[("recheck", d)]
            s = min(1.0, (x0 / max(1, n0)) / lo)          # reproduce the re-check flip rate
            curve = model.flip_curve(k, eps, s, d)
            curves[(K, d)] = curve
            for cond, (x, n) in ((c, v) for (c, dd), v in cnt.items() if dd == d):
                if cond in TRACK:
                    centre = C * TRACK[cond] + (1 - C) * M
                    cm[d] += binll(x, n, np.interp(centre, CENTRES, curve))
                elif cond in FREE:
                    fr[d][FREE[cond]] += binll(x, n, np.interp(A, CENTRES, curve))
    return cm, fr, curves


def fit(sets, model, version):
    """version: 'M0', 'M1' or 'M2'. Returns (loglik, params dict, curves)."""
    framed = any(K is not None for K in sets)
    best = (-np.inf, None, None)
    eps_grid = [0.0] if version == "M0" else GRID["eps"]
    w_grid = GRID["w"] if framed else [0.0]
    for k0, w, eps in itertools.product(GRID["k0"], w_grid, eps_grid):
        cm, fr, curves = tables(sets, model, k0, w, eps)
        prm = {"k0": k0, "w": w, "eps": eps}
        ll = 0.0
        if version == "M2":
            for d in DIRS:
                ic, im = np.unravel_index(np.argmax(cm[d]), cm[d].shape)
                ll += cm[d][ic, im]
                prm.update({f"c_{NAMES[d]}": GRID["c"][ic], f"m_{NAMES[d]}": GRID["m"][im]})
                for nm, t in fr[d].items():
                    i = int(np.argmax(t))
                    ll += t[i]
                    prm[f"{nm}_{NAMES[d]}"] = GRID["m"][i]
        else:
            t = cm[True] + cm[False]
            if version == "M0":
                ic, im = GRID["c"].index(1.0), 0             # m irrelevant when c = 1
            else:
                ic, im = np.unravel_index(np.argmax(t), t.shape)
            ll += t[ic, im]
            prm.update(c=GRID["c"][ic], m=0.5 if version == "M0" else GRID["m"][im])
            for nm in FREE.values():
                tt = fr[True][nm] + fr[False][nm]
                i = int(np.argmax(tt))
                ll += tt[i]
                prm[nm] = GRID["m"][i]
        if ll > best[0]:
            best = (float(ll), prm, curves)
    return best


def n_params(version, framed):
    return {"M0": 4, "M1": 7, "M2": 11}[version] - (0 if framed else 1)


def predict(sets, prm, curves, version):
    out = {}
    for K, cnt in sets.items():
        for (cond, d) in cnt:
            if cond == "recheck":
                continue
            sfx = f"_{NAMES[d]}" if version == "M2" else ""
            if cond in FREE:
                centre = prm[FREE[cond] + sfx]
            else:
                c, m = prm["c" + sfx], prm["m" + sfx]
                centre = c * TRACK[cond] + (1 - c) * m
            out[(K, cond, d)] = float(np.interp(centre, CENTRES, curves[(K, d)]))
    return out


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
        sets, items = load_sets(prefix, args.prefix_style)
        framed = len(sets) > 1
        fits = {v: fit(sets, model, v) for v in ("M0", "M1", "M2")}
        ll = {v: f[0] for v, f in fits.items()}
        aic = {v: 2 * n_params(v, framed) - 2 * ll[v] for v in fits}
        name = os.path.basename(prefix)
        print(f"\n== {name}  (items: " + ", ".join(f"{'unframed' if K is None else f'K={K:g}'} {n}"
                                             for K, n in items.items()) + ")")
        for v in fits:
            prm = fits[v][1]
            print(f"  {v}: log-lik {ll[v]:8.1f}  AIC {aic[v]:7.1f}  " + ", ".join(f"{k} {x:g}" for k, x in prm.items()))
        print(f"  LR M1 vs M0 {2 * (ll['M1'] - ll['M0']):.1f} (3 df) | M2 vs M1 {2 * (ll['M2'] - ll['M1']):.1f} (4 df)")
        boots = []
        for _ in range(args.boot):
            bs = {K: {key: (int(rng.binomial(n, x / max(1, n))), n) for key, (x, n) in cnt.items()}
                  for K, cnt in sets.items()}
            boots.append(fit(bs, model, "M2")[1])
        keys = list(fits["M2"][1])
        ci = {k: ((float(np.percentile([b[k] for b in boots], 5)), float(np.percentile([b[k] for b in boots], 95)))
                  if boots else (fits["M2"][1][k],) * 2) for k in keys}
        print("  M2 estimate (90% bootstrap range): " +
              ", ".join(f"{k} = {fits['M2'][1][k]:g} [{ci[k][0]:g}, {ci[k][1]:g}]" for k in keys))
        pred = predict(sets, fits["M2"][1], fits["M2"][2], "M2")
        print(f"  {'framing':8s} {'condition':10s} {'claim':7s} {'observed':>16s} {'M2 fit':>7s}")
        for K, cnt in sets.items():
            lab = "none" if K is None else f"K={K:g}"
            for d in DIRS:
                x0, n0 = cnt[("recheck", d)]
                print(f"  {lab:8s} {'recheck':10s} {NAMES[d]:7s} {x0 / max(1, n0):7.1%} of {n0:4d}   (baseline)")
                for cond in (UNFRAMED if K is None else FRAMED):
                    if cond != "recheck" and (cond, d) in cnt:
                        x, n = cnt[(cond, d)]
                        print(f"  {lab:8s} {cond:10s} {NAMES[d]:7s} {x / max(1, n):7.1%} of {n:4d} "
                              f"{pred[(K, cond, d)]:7.1%}")
        report[name] = {
            "items": {str(K): n for K, n in items.items()},
            "fits": {v: {"loglik": ll[v], "AIC": aic[v], "k": n_params(v, framed), "params": fits[v][1]} for v in fits},
            "ci90_M2": ci,
            "counts": {f"{K}|{c}|{NAMES[d]}": v for K, cnt in sets.items() for (c, d), v in cnt.items()}}
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nsaved {args.out}")


if __name__ == "__main__":
    main()
