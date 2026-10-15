"""Latent-class (Hui-Walter) estimation for binary outcomes coded by K classifiers across cells (ANALYSIS_PLAN_LATENT.md).
fit(X, cell): X is an n x K 0/1 array (NaN = missing for that classifier), cell an integer array (0..C-1).
Model: y ~ Bernoulli(p_cell); X_k | y independent Bernoulli with Se_k (y=1) or 1-Sp_k (y=0); Se, Sp common across cells
unless vary_k is given (then classifier vary_k has cell-specific Se, Sp)."""
import numpy as np

def fit(X, cell, C=None, vary_k=None, iters=5000, tol=1e-10, seed=0, wt=None):
    X = np.asarray(X, float); cell = np.asarray(cell, int); n, K = X.shape; C = C or cell.max() + 1
    wt = np.ones(n) if wt is None else np.asarray(wt, float)   # frequency weights (rows may be collapsed patterns)
    obs = ~np.isnan(X); Xz = np.nan_to_num(X)
    rng = np.random.default_rng(seed)
    p = np.full(C, 0.3); G = C if vary_k is not None else 1
    Se = np.full((G, K), 0.85) + rng.uniform(-.02, .02, (G, K)); Sp = np.full((G, K), 0.9) + rng.uniform(-.02, .02, (G, K))
    gi = cell if vary_k is not None else np.zeros(n, int)
    def rowpar(A):   # per-row parameter matrix n x K (classifier vary_k uses its cell row, others row 0)
        M = np.repeat(A[[0]], n, 0)
        if vary_k is not None: M[:, vary_k] = A[gi, vary_k]
        return M
    ll_old = -np.inf
    for it in range(iters):
        se, sp = rowpar(Se), rowpar(Sp)
        l1 = np.where(obs, np.where(Xz == 1, se, 1 - se), 1).prod(1)
        l0 = np.where(obs, np.where(Xz == 1, 1 - sp, sp), 1).prod(1)
        a = p[cell] * l1; b = (1 - p[cell]) * l0; tot = a + b; w = a / tot
        ll = (wt * np.log(tot)).sum()
        p = np.bincount(cell, wt * w, C) / np.bincount(cell, wt, C)
        for g in range(G):
            for k in range(K):
                if g > 0 and k != vary_k: continue
                m = obs[:, k] & ((gi == g) if (vary_k is not None and k == vary_k) else True)
                ww = wt[m] * w[m]; vv = wt[m] * (1 - w[m])
                Se[g, k] = (ww * Xz[m, k]).sum() / ww.sum()
                Sp[g, k] = (vv * (1 - Xz[m, k])).sum() / vv.sum()
        if vary_k is not None:   # rows for classifiers that do not vary stay equal to row 0
            for k in range(K):
                if k != vary_k: Se[:, k] = Se[0, k]; Sp[:, k] = Sp[0, k]
        if abs(ll - ll_old) < tol: break
        ll_old = ll
    if (Se[0] + Sp[0] - 1).mean() < 0:   # label switching: flip so that classifiers are informative on average
        p = 1 - p; Se, Sp = 1 - Sp, 1 - Se
    npar = C + 2 * K + (2 * K * 0 if vary_k is None else 2 * (C - 1))
    return dict(p=p, Se=Se, Sp=Sp, J=Se + Sp - 1, ll=ll, npar=npar, iters=it + 1)

def did(p):   # cells ordered (control,pre)=0, (control,post)=1, (treated,pre)=2, (treated,post)=3
    return (p[3] - p[2]) - (p[1] - p[0])

def collapse(X, cell):
    """Collapse rows to unique (cell, pattern) with counts; NaN kept as missing."""
    import pandas as pd
    D = pd.DataFrame(np.column_stack([cell, np.nan_to_num(X, nan=-1)])).value_counts().reset_index()
    A = D.iloc[:, :-1].to_numpy(); Xc = A[:, 1:].astype(float); Xc[Xc < 0] = np.nan
    return Xc, A[:, 0].astype(int), D.iloc[:, -1].to_numpy(float)

def fit_pair_dependent(X, cell, pair, C=4, iters=5000, tol=1e-10):
    """Complete-data model in which the two classifiers in `pair` have a free joint distribution given y (4 levels),
    the others independent. Returns log-likelihood and parameters."""
    X = np.asarray(X, int); cell = np.asarray(cell, int); n, K = X.shape
    a, b = pair; joint = 2 * X[:, a] + X[:, b]; others = [k for k in range(K) if k not in pair]
    p = np.full(C, .3); th1 = np.array([.05, .1, .1, .75]); th0 = np.array([.8, .1, .07, .03])
    Se = np.full(len(others), .8); Sp = np.full(len(others), .9); ll_old = -np.inf
    for it in range(iters):
        l1 = th1[joint] * np.prod(np.where(X[:, others] == 1, Se, 1 - Se), 1)
        l0 = th0[joint] * np.prod(np.where(X[:, others] == 1, 1 - Sp, Sp), 1)
        A_ = p[cell] * l1; B_ = (1 - p[cell]) * l0; tot = A_ + B_; w = A_ / tot; ll = np.log(tot).sum()
        p = np.bincount(cell, w, C) / np.bincount(cell, minlength=C)
        th1 = np.bincount(joint, w, 4) / w.sum(); th0 = np.bincount(joint, 1 - w, 4) / (1 - w).sum()
        Se = (w[:, None] * X[:, others]).sum(0) / w.sum(); Sp = ((1 - w)[:, None] * (1 - X[:, others])).sum(0) / (1 - w).sum()
        if abs(ll - ll_old) < tol: break
        ll_old = ll
    return dict(ll=ll, p=p, th1=th1, th0=th0, Se=Se, Sp=Sp, npar=C + 6 + 2 * len(others))
