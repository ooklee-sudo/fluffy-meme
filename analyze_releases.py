"""Estimate the release rate mu and the dispersion of release intervals from open-model release dates.

Input: results/release_events.csv (first Hugging Face repository creation date of each release, collected
2026-11-21 from the Hugging Face API; `strict` = new version number of the main line, otherwise a new size or
variant).  The observation window of each family runs from its first release to the collection date, so the last
interval is right-censored.  Usage:  python analyze_releases.py
"""
import csv
import json
from datetime import date

import numpy as np
from scipy import stats
from scipy.optimize import minimize_scalar

import real_options as ro

END = date(2026, 11, 21)


def load(strict_only):
    fam = {}
    for r in csv.DictReader(open("results/release_events.csv")):
        if strict_only and r["strict"] != "1":
            continue
        fam.setdefault(r["family"], []).append(date.fromisoformat(r["date"]))
    return {f: sorted(v) for f, v in fam.items()}


def rate_ci(k, T, a=0.05):
    """Exact Poisson interval for k events in exposure T (years)."""
    lo = stats.chi2.ppf(a / 2, 2 * k) / (2 * T) if k > 0 else 0.0
    hi = stats.chi2.ppf(1 - a / 2, 2 * k + 2) / (2 * T)
    return lo, hi


def gamma_shape(x, censored):
    """MLE of the gamma shape for intervals scaled to unit mean within family, with right-censored last intervals."""
    def nll(logk):
        k = np.exp(logk)
        return -(stats.gamma.logpdf(x, k, scale=1 / k).sum() + stats.gamma.logsf(censored, k, scale=1 / k).sum())
    r = minimize_scalar(nll, bounds=(-3, 3), method="bounded")
    return np.exp(r.x), r.fun, nll(0.0)


def main():
    out = {}
    p = ro.Params()
    for spec, strict in (("strict", True), ("broad", False)):
        fam = load(strict)
        print(f"\n== {spec}: release = {'new version number' if strict else 'any new size or variant'} ==")
        print(f"{'family':8s} {'n':>3s} {'years':>6s} {'mu':>5s} {'95% CI':>13s} {'mean gap (mo)':>13s} {'CV':>5s}")
        rows, xs, cens = [], [], []
        for f, d in fam.items():
            gaps = np.array([(b - a).days / 365.25 for a, b in zip(d, d[1:])])
            T = (END - d[0]).days / 365.25
            k = len(gaps)
            mu = k / T
            lo, hi = rate_ci(k, T)
            cv = gaps.std(ddof=1) / gaps.mean()
            tail = (END - d[-1]).days / 365.25
            rows.append({"family": f, "releases": len(d), "years": T, "mu": mu, "ci": [lo, hi],
                         "mean_gap_months": 12 * gaps.mean(), "cv": cv, "open_gap_months": 12 * tail})
            print(f"{f:8s} {len(d):3d} {T:6.2f} {mu:5.2f} [{lo:4.2f}, {hi:4.2f}] {12 * gaps.mean():13.1f} {cv:5.2f}"
                  f"   (open gap {12 * tail:.1f} mo)")
            xs += list(gaps / mu ** -1)       # scale by the family's estimated mean interval 1/mu
            cens.append(tail * mu)
        k_all = sum(len(d) - 1 for d in fam.values())
        T_all = sum((END - d[0]).days / 365.25 for d in fam.values())
        lo, hi = rate_ci(k_all, T_all)
        shape, nll_k, nll_1 = gamma_shape(np.array(xs), np.array(cens))
        lr = 2 * (nll_1 - nll_k)
        print(f"pooled mu = {k_all / T_all:.2f} [{lo:.2f}, {hi:.2f}] per year; gamma shape of scaled intervals = {shape:.2f} "
              f"(CV {1 / np.sqrt(shape):.2f}); LR test of exponential (shape 1): chi2 = {lr:.2f}, p = {stats.chi2.sf(lr, 1):.3f}")
        # implied thresholds
        print("retraining threshold v*/C_N at each family's mu:  R_C = 0.914 (Pythia-1B +70k)   R_C = 0.147 (SmolLM2 instruct)")
        for r in rows:
            q = ro.Params(mu=r["mu"])
            r["v_star_0914"], r["v_star_0147"] = ro.v_star(0.914, q), ro.v_star(0.147, q)
            print(f"  {r['family']:8s} mu={r['mu']:.2f}: {r['v_star_0914']:6.1f}   {r['v_star_0147']:5.2f}")
        out[spec] = {"families": rows, "pooled_mu": k_all / T_all, "pooled_ci": [lo, hi], "gamma_shape": shape,
                     "lr_exponential": lr, "p_exponential": float(stats.chi2.sf(lr, 1))}
    json.dump(out, open("results/release_rates.json", "w"), indent=2, default=float)
    print("\nsaved results/release_rates.json")


if __name__ == "__main__":
    main()
