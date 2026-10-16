"""Metrics for comparing count-data distributions (real vs. LLM-synthetic customers)."""
import warnings

import numpy as np
import statsmodels.api as sm
from scipy import stats


def summary(y):
    y = np.asarray(y, dtype=float)
    m, v = y.mean(), y.var(ddof=1)
    k = max(1, int(np.ceil(0.1 * len(y))))
    top = np.sort(y)[::-1][:k].sum() / max(y.sum(), 1e-12)
    return {"mean": m, "var": v, "disp_ratio": v / m if m > 0 else np.nan,
            "zero_frac": float((y == 0).mean()), "top10_share": float(top)}


def pmf(y, cap=30):
    y = np.minimum(np.asarray(y, dtype=int), cap)
    return np.bincount(y, minlength=cap + 1) / len(y)


def distances(real, synth, cap=30):
    p, q = pmf(real, cap), pmf(synth, cap)
    js = float(np.sqrt(stats.entropy(p, (p + q) / 2) / 2 + stats.entropy(q, (p + q) / 2) / 2))
    return {"wasserstein": float(stats.wasserstein_distance(real, synth)),
            "ks": float(stats.ks_2samp(real, synth).statistic),
            "js": js}


def cameron_trivedi(y):
    """Intercept-only Poisson overdispersion test (alpha>0 => overdispersed).
    Regress ((y-mu)^2 - y)/mu on mu without a constant; returns (alpha, t, p)."""
    y = np.asarray(y, dtype=float)
    mu = y.mean()
    z = ((y - mu) ** 2 - y) / mu
    res = sm.OLS(z, np.full(len(y), mu)).fit()
    alpha, t = res.params[0], res.tvalues[0]
    return float(alpha), float(t), float(stats.norm.sf(t))


def fit_count_models(y):
    """AIC of Poisson / NB2 / ZIP (intercept only). Returns dict of AIC and best model."""
    y = np.asarray(y, dtype=int)
    X = np.ones((len(y), 1))
    out = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        out["poisson"] = sm.Poisson(y, X).fit(disp=0).aic
        try:
            out["nb"] = sm.NegativeBinomial(y, X).fit(disp=0, maxiter=200).aic
        except Exception:
            out["nb"] = np.inf
        try:
            out["zip"] = sm.ZeroInflatedPoisson(y, X, exog_infl=X).fit(disp=0, maxiter=200).aic
        except Exception:
            out["zip"] = np.inf
    out["best"] = min(("poisson", "nb", "zip"), key=lambda k: out[k])
    return out


def bootstrap_ci(y, stat, n_boot=500, seed=0, level=0.95):
    rng = np.random.default_rng(seed)
    y = np.asarray(y)
    vals = [stat(rng.choice(y, len(y))) for _ in range(n_boot)]
    a = (1 - level) / 2
    return float(np.quantile(vals, a)), float(np.quantile(vals, 1 - a))


def irr(y, treat):
    """Incidence-rate ratio of treatment from a Poisson GLM with robust SE; returns (irr, lo, hi)."""
    X = sm.add_constant(np.asarray(treat, dtype=float))
    r = sm.GLM(np.asarray(y), X, family=sm.families.Poisson()).fit(cov_type="HC0")
    lo, hi = np.exp(r.conf_int()[1])
    return float(np.exp(r.params[1])), float(lo), float(hi)
