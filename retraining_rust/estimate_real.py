"""Estimate the retraining-cost model on weekly GitHub data.

State = weeks since last release (deterministic drift clock, capped at CAP).
Error rate = exposure_t * (lam0 + gamma * state); exposure optional (--exposure all_issues).
Per-repo two-step estimates, plus a pooled RC (common RC, repo-specific gamma, lam0).
Release weeks are treated as retraining events (d=1).
"""
import argparse, glob, os, json
import numpy as np, csv
from scipy.optimize import minimize, minimize_scalar
import rust_retrain as rr

CAP = 40


def load(path, exposure=None):
    rows = list(csv.DictReader(open(path)))
    bugs = np.array([int(r["bugs"]) for r in rows])
    d = np.array([int(r["release"]) for r in rows])
    x = np.zeros(len(rows), int)
    cur = 0
    for t in range(len(rows)):
        x[t] = min(cur, CAP)
        cur = 1 if d[t] else cur + 1      # post-release week 1 (deterministic clock)
    e = np.ones(len(rows))
    if exposure:
        e = np.array([float(r[exposure]) for r in rows]); e = np.maximum(e, 0.5) / e.mean()
    return x, d, bugs, e


def fit_errors(x, d, n, e):
    xe = np.where(d == 1, 0, x).astype(float)   # post-decision state
    def nll(th):
        lam = np.maximum(e * (th[0] + th[1] * xe), 1e-9)
        return -np.sum(n * np.log(lam) - lam)
    r = minimize(nll, [max(n.mean(), 0.5), 0.0], method="Nelder-Mead")
    return r.x


GRID = np.geomspace(1, 300, 40)


def argmax_rc(f):
    """Maximise f(rc): coarse log-grid (the likelihood has flat plateaus), then refine."""
    vals = [f(g) for g in GRID]
    i = int(np.argmax(vals))
    lo, hi = GRID[max(i - 1, 0)], GRID[min(i + 1, len(GRID) - 1)]
    r = minimize_scalar(lambda rc: -f(rc), bounds=(lo, hi), method="bounded")
    return float(r.x), float(-r.fun)


def fit_rc(x, d, lam0, gamma, beta):
    return argmax_rc(lambda rc: rr.loglik_choice(rc, gamma, x, d, lam0, None, beta))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("data_dir"); ap.add_argument("--beta", type=float, default=0.95)
    ap.add_argument("--exposure", default=None); ap.add_argument("--boot", type=int, default=200)
    ap.add_argument("--min-releases", type=int, default=5)
    a = ap.parse_args()
    out, pooled = {}, []
    for p in sorted(glob.glob(os.path.join(a.data_dir, "*.csv"))):
        x, d, n, e = load(p, a.exposure)
        if d.sum() < a.min_releases:
            print("skip", p, "(too few releases)"); continue
        lam0, g = fit_errors(x, d, n, e)
        rc, ll = fit_rc(x, d, lam0, max(g, 0.0), a.beta)
        # block bootstrap over release cycles (re-sample whole cycles, re-estimate both steps)
        ends = np.r_[np.where(d == 1)[0], len(d) - 1]
        starts = np.r_[0, ends[:-1] + 1]
        rcs = []
        rng = np.random.default_rng(0)
        for _ in range(a.boot):
            k = rng.integers(0, len(ends), len(ends))
            idx = np.concatenate([np.arange(starts[i], ends[i] + 1) for i in k])
            xb, db, nb, eb = x[idx], d[idx], n[idx], e[idx]
            if db.sum() < 2: continue
            l0, gb = fit_errors(xb, db, nb, eb)
            rcs.append(fit_rc(xb, db, l0, max(gb, 0.0), a.beta)[0])
        name = os.path.basename(p)[:-4]
        out[name] = dict(weeks=len(d), releases=int(d.sum()), lam0=float(lam0), gamma=float(g),
                         RC=rc, RC_ci=[float(np.percentile(rcs, 5)), float(np.percentile(rcs, 95))],
                         threshold=rr.threshold(rr.solve(max(g, 0.0), rc, lam0, None, a.beta)[3]),
                         mean_cycle_weeks=float(len(d) / d.sum()))
        pooled.append((x, d, lam0, max(g, 0.0)))
        print(name, out[name])
    if len(pooled) > 1:
        f = lambda rc: sum(rr.loglik_choice(rc, g, x, d, l0, None, a.beta) for x, d, l0, g in pooled)
        out["_pooled_RC"] = argmax_rc(f)[0]
    json.dump(out, open("real_results.json", "w"), indent=1)


if __name__ == "__main__":
    main()
