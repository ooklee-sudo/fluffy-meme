"""Small, dependency-light estimation helpers (numpy only).

twfe_ols        OLS with up to two sets of fixed effects (alternating projections),
                CR1 cluster-robust standard errors.
wild_cluster_p  Wild cluster *restricted* bootstrap p-value (WCR) with Webb six-point
                weights, as recommended for few clusters (Cameron, Gelbach & Miller 2008;
                Webb 2023). The null is imposed by re-estimating without the tested
                regressor; bootstrap outcomes are re-demeaned on every draw, so the
                procedure is exact for two non-nested fixed effects.
"""
import numpy as np

WEBB = np.array([-np.sqrt(1.5), -1.0, -np.sqrt(0.5), np.sqrt(0.5), 1.0, np.sqrt(1.5)])


def demean(M, fes, tol=1e-10, max_iter=1000):
    """Project columns of M off one or two sets of fixed effects."""
    M = np.array(M, dtype=float, copy=True)
    if M.ndim == 1:
        M = M[:, None]
    if not fes:
        return M
    codes = [np.unique(f, return_inverse=True)[1] for f in fes]
    counts = [np.bincount(c) for c in codes]
    for _ in range(max_iter):
        delta = 0.0
        for c, n in zip(codes, counts):
            means = np.vstack([np.bincount(c, weights=M[:, j]) / n for j in range(M.shape[1])]).T
            M -= means[c]
            delta = max(delta, np.abs(means).max())
        if len(fes) == 1 or delta < tol:
            break
    return M


def _cluster_vcov(Xd, e, cl, df_fe):
    n, k = Xd.shape
    XtX_inv = np.linalg.pinv(Xd.T @ Xd)
    g = np.unique(cl, return_inverse=True)[1]
    G = g.max() + 1
    S = np.zeros((G, k))
    np.add.at(S, g, Xd * e[:, None])
    meat = S.T @ S
    adj = G / (G - 1) * (n - 1) / max(n - k - df_fe, 1)
    return adj * XtX_inv @ meat @ XtX_inv


def twfe_ols(y, X, fes, cluster, names=None):
    """Return dict with coef, se, t, vcov, resid, and the demeaned design."""
    yd = demean(y, fes)[:, 0]
    Xd = demean(X, fes)
    beta, *_ = np.linalg.lstsq(Xd, yd, rcond=None)
    e = yd - Xd @ beta
    df_fe = sum(len(np.unique(f)) for f in fes) - (len(fes) > 1)
    V = _cluster_vcov(Xd, e, cluster, df_fe)
    se = np.sqrt(np.diag(V))
    names = names or [f"x{j}" for j in range(X.shape[1])]
    return dict(names=names, coef=beta, se=se, t=beta / se, vcov=V, resid=e,
                yd=yd, Xd=Xd, df_fe=df_fe)


def wild_cluster_p(y, X, fes, cluster, j, B=999, seed=12345):
    """WCR bootstrap p-value (two-sided) for H0: beta_j = 0."""
    rng = np.random.default_rng(seed)
    full = twfe_ols(y, X, fes, cluster)
    t_obs = full["t"][j]
    Xr = np.delete(np.asarray(X, float).reshape(len(y), -1), j, axis=1)
    if Xr.shape[1]:
        restr = twfe_ols(y, Xr, fes, cluster)
        e_r = restr["resid"]
    else:
        e_r = demean(y, fes)[:, 0]
    yd = full["yd"]
    fitted_r = yd - e_r                      # restricted fit in the demeaned space
    g = np.unique(cluster, return_inverse=True)[1]
    G = g.max() + 1
    Xd = full["Xd"]
    XtX_inv = np.linalg.pinv(Xd.T @ Xd)
    n, k = Xd.shape
    adj = G / (G - 1) * (n - 1) / max(n - k - full["df_fe"], 1)
    t_star = np.empty(B)
    for b in range(B):
        w = rng.choice(WEBB, size=G)[g]
        ystar = fitted_r + demean(w * e_r, fes)[:, 0]
        bstar = XtX_inv @ (Xd.T @ ystar)
        es = ystar - Xd @ bstar
        S = np.zeros((G, k))
        np.add.at(S, g, Xd * es[:, None])
        V = adj * XtX_inv @ (S.T @ S) @ XtX_inv
        t_star[b] = bstar[j] / np.sqrt(V[j, j])
    return float((np.sum(np.abs(t_star) >= abs(t_obs)) + 1) / (B + 1))
