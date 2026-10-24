"""Count models: Poisson -> NB2 comparison, dispersion tests, IRR tables, CV deviance for RQ2 feature-set comparison."""
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from patsy import dmatrices
from patsy import build_design_matrices, dmatrix
from sklearn.model_selection import GroupKFold

LLM_TERMS = ["sentiment_c", "I(sentiment_c**2)", "emotional_intensity", "specificity", "informativeness",
             "argument_balance", "narrative", "explicit_recommendation", "comparison", "C(dominant_emotion)"]
CONTROLS = ["stars", "np.log(text_len)", "np.log(author_reviews)"]


def rare_level_map(series, min_share=0.05):
    """Map levels with share < min_share (in the main LLM-coded sample) to 'other'. Compute ONCE on the full
    LLM-coded data and pass the same map to every frame (including human labels) so designs stay aligned."""
    share = series.value_counts(normalize=True)
    keep = set(share[share >= min_share].index)
    return {lv: (lv if lv in keep else "other") for lv in share.index}


def prepare(df, emotion_map=None):
    d = df[df.get("valid", True) == True].copy()  # noqa: E712
    if emotion_map is not None:  # levels unseen in the main sample (e.g. only in human labels) -> 'other'
        d["dominant_emotion"] = d["dominant_emotion"].map(lambda v: emotion_map.get(v, "other"))
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


ALPHA_GRID = np.logspace(-5, 1, 9)  # if the chosen alpha sits at the upper end, widen the grid


def _design(formula, train, test=None):
    X = dmatrix(formula, train, return_type="dataframe")
    Xt = None if test is None else build_design_matrices([X.design_info], test, return_type="dataframe")[0]
    return X, Xt


def _ridge_fit(X, y, off, pen_mask, alpha):
    """Poisson ridge: L2 penalty (L1_wt=0) on columns flagged in pen_mask only; intercept and controls free."""
    pen = np.where(pen_mask, alpha, 0.0)
    mod = sm.GLM(y, X, family=sm.families.Poisson(), offset=off)
    return mod.fit_regularized(alpha=pen, L1_wt=0.0, maxiter=300)


def ridge_cv_alpha(d, rhs, penalized, k=3, group_col="group_id", grid=ALPHA_GRID):
    """Choose the ridge strength by group K-fold held-out Poisson deviance on `d` (inner loop)."""
    X, _ = _design(" + ".join(rhs), d)
    mask = np.array([any(c == p or c.startswith(p) for p in penalized) for c in X.columns])
    y, off = d["count"].to_numpy(float), np.log(d["exposure"].to_numpy(float))
    Xv = X.to_numpy(float)
    scores = np.zeros(len(grid))
    for tr, te in GroupKFold(n_splits=k).split(Xv, groups=d[group_col]):
        for j, al in enumerate(grid):
            b = _ridge_fit(Xv[tr], y[tr], off[tr], mask, al).params
            scores[j] += poisson_deviance(y[te], np.exp(Xv[te] @ np.asarray(b) + off[te]))
    return float(grid[int(np.argmin(scores))])


def cv_compare(d, feature_sets: dict, k=5, group_col="group_id"):
    """Held-out Poisson deviance by group-wise K-fold (RQ2).
    feature_sets: name -> list of RHS terms, or (rhs, penalized_cols) for a ridge-regularized fit whose penalty
    is re-chosen by inner CV inside every outer training fold (no peeking at held-out groups)."""
    gkf = GroupKFold(n_splits=k)
    rows = []
    for name, spec in feature_sets.items():
        rhs, penalized = (spec, None) if isinstance(spec, list) else spec
        devs, alphas = [], []
        for tr, te in gkf.split(d, groups=d[group_col]):
            tr_d, te_d = d.iloc[tr], d.iloc[te]
            if penalized:
                al = ridge_cv_alpha(tr_d, rhs, penalized)
                Xtr, Xte = _design(" + ".join(rhs), tr_d, te_d)
                mask = np.array([any(c.startswith(p) for p in penalized) for c in Xtr.columns])
                b = np.asarray(_ridge_fit(Xtr.to_numpy(float), tr_d["count"].to_numpy(float),
                                          np.log(tr_d["exposure"].to_numpy(float)), mask, al).params)
                mu = np.exp(Xte.to_numpy(float) @ b + np.log(te_d["exposure"].to_numpy(float)))
                devs.append(poisson_deviance(te_d["count"], mu)); alphas.append(al)
                continue
            res = smf.glm("count ~ " + " + ".join(rhs), data=tr_d, family=sm.families.Poisson(),
                          offset=np.log(tr_d["exposure"])).fit()
            mu = res.predict(te_d, offset=np.log(te_d["exposure"]))
            devs.append(poisson_deviance(te_d["count"], mu))
        if penalized:  # AIC is not comparable for penalized fits
            rows.append({"model": name, "cv_deviance": np.mean(devs), "cv_sd": np.std(devs), "aic_poisson": np.nan,
                         "ridge_alpha_median": float(np.median(alphas))})
            continue
        full = smf.glm("count ~ " + " + ".join(rhs), data=d, family=sm.families.Poisson(),
                       offset=np.log(d["exposure"])).fit()
        rows.append({"model": name, "cv_deviance": np.mean(devs), "cv_sd": np.std(devs), "aic_poisson": full.aic})
    return pd.DataFrame(rows)


def heterogeneity(d, rhs, interact="specificity", by="category"):
    """H3: interaction of a text feature with product-type category (NB2)."""
    r = [t for t in rhs] + [f"C({by})", f"{interact}:C({by})"]
    return fit_glm(d, r, "nb")


def zero_inflation_check(d, rhs="gap * experience + z_loglen + C(star_f) + has_image"):
    """Compare NB2 with ZINB (logit inflation: const + experience), same count-part covariates and log-age exposure.
    Needs columns: count, gap, experience, len_chars, star_f, has_image, exposure. Returns a dict.
    If the inflation intercept diverges to -inf, ZINB collapses to NB2 (no excess zeros): the Hessian is then
    singular, which is a boundary solution rather than a convergence bug."""
    from statsmodels.discrete.count_model import ZeroInflatedNegativeBinomialP
    from statsmodels.discrete.discrete_model import NegativeBinomialP
    d = d.copy()
    ll = np.log(d["len_chars"])
    d["z_loglen"] = (ll - ll.mean()) / ll.std()
    y, X = dmatrices("count ~ " + rhs, d, return_type="dataframe")
    nb = NegativeBinomialP(y.iloc[:, 0], X, exposure=d["exposure"], p=2).fit(method="bfgs", maxiter=3000, disp=0)
    zi = ZeroInflatedNegativeBinomialP(y.iloc[:, 0], X, exog_infl=X[["Intercept", "experience"]],
                                       exposure=d["exposure"], inflation="logit", p=2).fit(method="bfgs", maxiter=3000, disp=0)
    p0 = float(1 / (1 + np.exp(-zi.params["inflate_Intercept"])))
    return {"nb_llf": float(nb.llf), "zinb_llf": float(zi.llf), "nb_aic": float(nb.aic), "zinb_aic": float(zi.aic),
            "p_structural_zero": p0, "collapsed_to_nb": bool(abs(nb.llf - zi.llf) < 0.5 or p0 < 1e-6),
            "nb_gap_irr": float(np.exp(nb.params["gap"])), "nb_gap_x_exp_irr": float(np.exp(nb.params["gap:experience"])),
            "zinb_gap_irr": float(np.exp(zi.params["gap"]))}
