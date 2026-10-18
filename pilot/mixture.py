"""Group-level estimate of the LLM-assisted share (distributional mixture).

Documents are represented as binary word-occurrence vectors over a fixed
vocabulary. Reference corpora give per-word occurrence probabilities p (human)
and q (LLM). For a group of documents the share alpha maximizes
    sum_d log((1 - alpha) * P(d) + alpha * Q(d)).
"""
import numpy as np
from scipy.optimize import minimize_scalar

EPS = 1e-6


def fit_reference(X, smooth=1.0):
    """Per-word occurrence probabilities from a binary doc-by-word matrix."""
    n = X.shape[0]
    p = (X.sum(axis=0) + smooth) / (n + 2 * smooth)
    return np.clip(p, EPS, 1 - EPS)


def doc_loglik(X, p):
    """log P(d) under independent Bernoulli word occurrence."""
    return X @ np.log(p) + (1 - X) @ np.log1p(-p)


def estimate_alpha(X, p, q):
    """MLE of alpha in [0, 1] for a group; returns (alpha, ll_p, ll_q)."""
    lp, lq = doc_loglik(X, p), doc_loglik(X, q)

    def nll(a):
        return -np.logaddexp(np.log1p(-a + EPS) + lp, np.log(a + EPS) + lq).sum()

    res = minimize_scalar(nll, bounds=(0.0, 1.0), method="bounded", options={"xatol": 1e-4})
    return float(res.x)


def bootstrap_ci(X, p, q, n_boot=200, level=0.95, seed=0):
    rng = np.random.default_rng(seed)
    n = X.shape[0]
    est = [estimate_alpha(X[rng.integers(0, n, n)], p, q) for _ in range(n_boot)]
    lo, hi = np.quantile(est, [(1 - level) / 2, 1 - (1 - level) / 2])
    return float(lo), float(hi)


def null_threshold(X_human_holdout, p, q, n_docs, n_perm=500, quantile=0.99, seed=0):
    """Threshold on alpha for a unit with n_docs documents, calibrated on the
    human holdout so units with few and many filings share one false-positive
    rate (the 'document-count-conditional' calibration in the proposal)."""
    rng = np.random.default_rng(seed)
    m = X_human_holdout.shape[0]
    null = [estimate_alpha(X_human_holdout[rng.integers(0, m, n_docs)], p, q) for _ in range(n_perm)]
    return float(np.quantile(null, quantile))


def alpha_from_ll(lp, lq):
    """Same MLE as estimate_alpha, from precomputed per-document log-likelihoods
    under the human (lp) and LLM (lq) word-occurrence models."""
    def nll(a):
        return -np.logaddexp(np.log1p(-a + EPS) + lp, np.log(a + EPS) + lq).sum()
    return float(minimize_scalar(nll, bounds=(0.0, 1.0), method="bounded", options={"xatol": 1e-4}).x)
