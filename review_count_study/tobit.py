"""Left-censored (at 0) Tobit model with cluster-robust standard errors (used to mirror the original specification)."""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from patsy import dmatrices
from scipy import stats
from statsmodels.base.model import GenericLikelihoodModel


class Tobit(GenericLikelihoodModel):
    """y* = Xb + e, e ~ N(0, s^2); y = max(y*, 0). Last parameter is log(sigma)."""

    def loglikeobs(self, params):
        b, s = params[:-1], np.exp(params[-1])
        xb, y = self.exog @ b, self.endog
        return np.where(y <= 0, stats.norm.logcdf(-xb / s), stats.norm.logpdf((y - xb) / s) - np.log(s))

    def fit(self, start_params=None, maxiter=2000, **kw):
        if start_params is None:
            ols = sm.OLS(self.endog, self.exog).fit()
            start_params = np.append(ols.params, np.log(np.sqrt(ols.scale)))
        return super().fit(start_params=start_params, maxiter=maxiter, method="bfgs", disp=0, **kw)


def fit_tobit(formula, d, group):
    y, X = dmatrices(formula, d, return_type="dataframe")
    r = Tobit(y.iloc[:, 0].to_numpy(float), X.to_numpy(float)).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d[group])[0]})
    return pd.DataFrame({"coef": r.params, "se": r.bse, "p": r.pvalues}, index=list(X.columns) + ["log_sigma"])
