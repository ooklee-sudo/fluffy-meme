"""Count models: Poisson -> NB2 comparison, dispersion tests, IRR tables, CV deviance for RQ2 feature-set comparison."""
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.model_selection import GroupKFold

LLM_TERMS = ["sentiment_c", "I(sentiment_c**2)", "emotional_intensity", "specificity", "informativeness",
             "argument_balance", "narrative", "explicit_recommendation", "comparison", "C(dominant_emotion)"]
CONTROLS = ["stars", "np.log(text_len)", "np.log(author_reviews)"]


def prepare(df):
    d = df[df.get("valid", True) == True].copy()  # noqa: E712
    d["sentiment_c"] = d["sentiment"] - 3
    d["text_len"] = d["text"].str.split().str.len().clip(lower=1)
    d["author_reviews"] = d["author_reviews"].clip(lower=1)
    d["exposure"] = d["days_since_post"].clip(lower=1)
    return d


def collinearity_check(d, rhs, warn_cond=30):
    """Condition number of the standardized design matrix; large values => near-collinear coded features."""
    X = smf.glm("count ~ " + " + ".join(rhs), data=d, family=sm.families.Poisson()).data.exog[:, 1:]
    X = (X - X.mean(0)) / np.where(X.std(0) == 0, 1, X.std(0))
    cond = float(np.linalg.cond(X))
    return {"condition_number": cond, "ok": cond < warn_cond}


def fit_glm(d, rhs, family="poisson", group_col="group_id"):
    formula = "count ~ " + " + ".join(rhs)
    fam = sm.families.Poisson() if family == "poisson" else sm.families.NegativeBinomial(alpha=_estimate_alpha(d, rhs))
    m = smf.glm(formula, data=d, family=fam, offset=np.log(d["exposure"]))
    return m.fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d[group_col])[0]})


def _estimate_alpha(d, rhs):
    """Moment/auxiliary-regression estimate of NB2 alpha (Cameron & Trivedi 1990 test regression)."""
    p = smf.glm("count ~ " + " + ".join(rhs), data=d, family=sm.families.Poisson(),
                offset=np.log(d["exposure"])).fit()
    mu = p.mu
    aux = ((d["count"] - mu) ** 2 - d["count"]) / mu
    a = sm.OLS(aux, mu).fit()  # regress on mu without intercept
    return float(max(a.params.iloc[0], 1e-4))


def dispersion_report(d, rhs):
    p = smf.glm("count ~ " + " + ".join(rhs), data=d, family=sm.families.Poisson(),
                offset=np.log(d["exposure"])).fit()
    return {"pearson_dispersion": p.pearson_chi2 / p.df_resid, "alpha_nb2": _estimate_alpha(d, rhs),
            "zero_share": float((d["count"] == 0).mean())}


def irr_table(res):
    ci = np.exp(res.conf_int())
    out = pd.DataFrame({"IRR": np.exp(res.params), "ci_low": ci[0], "ci_high": ci[1], "p": res.pvalues})
    return out.drop(index="Intercept", errors="ignore")


def poisson_deviance(y, mu):
    y, mu = np.asarray(y, float), np.maximum(np.asarray(mu, float), 1e-9)
    term = np.where(y > 0, y * np.log(np.where(y > 0, y, 1) / mu), 0.0)
    return 2 * np.mean(term - (y - mu))


def cv_compare(d, feature_sets: dict, k=5, group_col="group_id"):
    """Held-out Poisson deviance by group-wise K-fold (RQ2). feature_sets: name -> list of RHS terms."""
    gkf = GroupKFold(n_splits=k)
    rows = []
    for name, rhs in feature_sets.items():
        devs = []
        for tr, te in gkf.split(d, groups=d[group_col]):
            tr_d, te_d = d.iloc[tr], d.iloc[te]
            res = smf.glm("count ~ " + " + ".join(rhs), data=tr_d, family=sm.families.Poisson(),
                          offset=np.log(tr_d["exposure"])).fit()
            mu = res.predict(te_d, offset=np.log(te_d["exposure"]))
            devs.append(poisson_deviance(te_d["count"], mu))
        full = smf.glm("count ~ " + " + ".join(rhs), data=d, family=sm.families.Poisson(),
                       offset=np.log(d["exposure"])).fit()
        rows.append({"model": name, "cv_deviance": np.mean(devs), "cv_sd": np.std(devs), "aic_poisson": full.aic})
    return pd.DataFrame(rows)


def heterogeneity(d, rhs, interact="specificity", by="category"):
    """H3: interaction of a text feature with product-type category (NB2)."""
    r = [t for t in rhs] + [f"C({by})", f"{interact}:C({by})"]
    return fit_glm(d, r, "nb")
