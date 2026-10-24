"""Count-model analysis for per-task defect counts (RQ1).

Given y (defect count per task, optionally with covariates X and exposure),
test for overdispersion and compare Poisson / NegBin / ZIP / ZINB fits.
"""
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.discrete.count_model import (
    ZeroInflatedNegativeBinomialP,
    ZeroInflatedPoisson,
)


def _design(y, X):
    n = len(y)
    return np.ones((n, 1)) if X is None else sm.add_constant(np.asarray(X, float), has_constant="add")


def dispersion_tests(y, X=None, exposure=None):
    """Pearson dispersion ratio and Cameron-Trivedi (1990) auxiliary test.

    Both are run on a Poisson fit. A ratio well above 1 / small p-value
    indicates overdispersion relative to Poisson.
    """
    y = np.asarray(y, float)
    Xd = _design(y, X)
    res = sm.GLM(y, Xd, family=sm.families.Poisson(), exposure=exposure).fit()
    mu = res.mu
    pearson = float(np.sum((y - mu) ** 2 / mu) / res.df_resid)
    aux = ((y - mu) ** 2 - y) / mu
    ct = sm.OLS(aux, mu).fit()  # no constant: H0 alpha = 0 (NB2 alternative)
    return {
        "pearson_ratio": pearson,
        "ct_alpha": float(ct.params[0]),
        "ct_t": float(ct.tvalues[0]),
        "ct_p_one_sided": float(stats.t.sf(ct.tvalues[0], ct.df_resid)),
    }


def fit_models(y, X=None, exposure=None):
    """Fit Poisson, NB2, ZIP, ZINB; return a table sorted by AIC."""
    y = np.asarray(y, float)
    Xd = _design(y, X)
    kw = {} if exposure is None else {"exposure": exposure}
    specs = {
        "Poisson": lambda: sm.Poisson(y, Xd, **kw).fit(disp=0, maxiter=200),
        "NegBin": lambda: sm.NegativeBinomial(y, Xd, **kw).fit(disp=0, maxiter=200),
        "ZIP": lambda: ZeroInflatedPoisson(y, Xd, exog_infl=np.ones((len(y), 1)), **kw).fit(
            disp=0, maxiter=200, method="bfgs"),
        "ZINB": lambda: ZeroInflatedNegativeBinomialP(y, Xd, exog_infl=np.ones((len(y), 1)), **kw).fit(
            disp=0, maxiter=200, method="bfgs"),
    }
    rows = []
    for name, fit in specs.items():
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                r = fit()
            if not np.isfinite(r.llf):
                raise ValueError("non-finite llf")
            rows.append({"model": name, "k": len(r.params), "llf": r.llf, "aic": r.aic, "bic": r.bic,
                         "converged": bool(r.mle_retvals.get("converged", True))})
        except Exception as e:  # keep the table complete even if one fit fails
            rows.append({"model": name, "k": np.nan, "llf": np.nan, "aic": np.nan, "bic": np.nan,
                         "converged": False, "error": str(e)[:60]})
    df = pd.DataFrame(rows).sort_values("aic").reset_index(drop=True)
    df["d_aic"] = df["aic"] - df["aic"].min()
    return df


def analyze(y, X=None, exposure=None):
    return {"dispersion": dispersion_tests(y, X, exposure), "models": fit_models(y, X, exposure)}


if __name__ == "__main__":
    import sys
    y = pd.read_csv(sys.argv[1])[sys.argv[2] if len(sys.argv) > 2 else "n_defects"].values
    out = analyze(y)
    print(out["dispersion"])
    print(out["models"].to_string(index=False))
