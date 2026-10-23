"""Measurement-error correction for LLM-coded covariates with a small, randomly sampled human-labelled subset.

Design-based / prediction-powered estimating equation (cf. Egami et al. 2023 DSL; Angelopoulos et al. 2023 PPI):
    psi_tilde_i(b) = psi(y_i, xhat_i; b) + (R_i / pi) * [ psi(y_i, x_i; b) - psi(y_i, xhat_i; b) ],
where xhat = design built from LLM codes (all N rows), x = design built from human codes (rows with R_i=1),
pi = n_human / N is the known (random) labelling probability, and psi is the Poisson score
(y - exp(x'b + offset)) x. Solving sum psi_tilde = 0 is unbiased for the coefficients of the *human-coded*
regression regardless of LLM error; LLM codes only reduce the variance. Cluster-robust sandwich variance.

REQUIREMENT: the human subset must be a simple random sample of the analysis rows (known pi).
Not valid for convenience samples. Stratified sampling needs per-stratum pi_i (pass `pi` as an array).
"""
import numpy as np
import pandas as pd
from patsy import build_design_matrices, dmatrix
from scipy import stats


def dsl_poisson(llm_df, human_df, rhs, group_col="group_id", pi=None, max_iter=100, tol=1e-9):
    """llm_df: all rows (N) with LLM codes; human_df: subset with human codes (same columns, index aligned
    to llm_df). Returns DataFrame with coef, IRR, se, ci, p for the human-coded Poisson regression."""
    formula = " + ".join(rhs)
    hum = human_df.loc[human_df.index.intersection(llm_df.index)]
    # factor levels = union over LLM and human codes, so a category seen only in human labels is not lost
    info = dmatrix(formula, pd.concat([llm_df[hum.columns.intersection(llm_df.columns)], hum]),
                   return_type="dataframe").design_info
    Xh_all = build_design_matrices([info], llm_df, return_type="dataframe")[0]
    X_lab = np.asarray(build_design_matrices([info], hum, return_type="dataframe")[0])
    n, p = Xh_all.shape
    R = llm_df.index.isin(hum.index)
    pi_i = np.full(n, R.mean()) if pi is None else np.asarray(pi, float)
    w = np.where(R, 1.0 / pi_i, 0.0)
    y = llm_df["count"].to_numpy(float)
    off = np.log(llm_df["exposure"].to_numpy(float))
    Xa = Xh_all.to_numpy(float)
    Xt = np.zeros((n, p))                                                # human design, aligned rows
    pos = llm_df.index.get_indexer(hum.index)
    Xt[pos] = X_lab

    def score(b):
        mu_a, mu_t = np.exp(Xa @ b + off), np.exp(Xt @ b + off)
        psi = (y - mu_a)[:, None] * Xa + w[:, None] * ((y - mu_t)[:, None] * Xt - (y - mu_a)[:, None] * Xa)
        J = -(mu_a[:, None, None] * Xa[:, :, None] * Xa[:, None, :]
              + w[:, None, None] * (mu_t[:, None, None] * Xt[:, :, None] * Xt[:, None, :]
                                    - mu_a[:, None, None] * Xa[:, :, None] * Xa[:, None, :]))
        return psi, J.sum(0)

    b = np.zeros(p)
    b[0] = np.log(max(y.sum(), 1) / np.exp(off).sum())
    for _ in range(max_iter):
        psi, A = score(b)
        step = np.linalg.solve(A, -psi.sum(0))
        # damped Newton step to avoid overflow in exp
        t = 1.0
        while np.abs(t * step).max() > 5:
            t /= 2
        b = b + t * step
        if np.abs(t * step).max() < tol:
            break
    psi, A = score(b)
    g = pd.factorize(llm_df[group_col])[0]
    G = np.zeros((g.max() + 1, p))
    np.add.at(G, g, psi)
    B = G.T @ G
    Ainv = np.linalg.inv(A)
    V = Ainv @ B @ Ainv.T
    se = np.sqrt(np.diag(V))
    z = b / se
    out = pd.DataFrame({"coef": b, "se": se, "IRR": np.exp(b), "ci_low": np.exp(b - 1.96 * se),
                        "ci_high": np.exp(b + 1.96 * se), "p": 2 * stats.norm.sf(np.abs(z))}, index=Xh_all.columns)
    return out.drop(index="Intercept")
