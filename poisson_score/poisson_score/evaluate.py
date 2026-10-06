"""Detection metrics for the pilot analysis."""
from __future__ import annotations

import numpy as np
from scipy import stats


def auc(scores_pos: np.ndarray, scores_neg: np.ndarray) -> float:
    """P(score_pos > score_neg), ties count half (Mann-Whitney U)."""
    a = np.asarray(scores_pos, float); b = np.asarray(scores_neg, float)
    a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    u = stats.mannwhitneyu(a, b, alternative="two-sided").statistic
    return float(u / (len(a) * len(b)))


def bootstrap_auc_ci(pos, neg, n_boot=1000, seed=0):
    rng = np.random.default_rng(seed)
    pos = np.asarray(pos, float); neg = np.asarray(neg, float)
    pos, neg = pos[~np.isnan(pos)], neg[~np.isnan(neg)]
    vals = [auc(rng.choice(pos, len(pos)), rng.choice(neg, len(neg))) for _ in range(n_boot)]
    return tuple(np.percentile(vals, [2.5, 97.5]))


def tpr_at_fpr(pos, neg, fpr=0.05) -> float:
    neg = np.asarray(neg, float); neg = neg[~np.isnan(neg)]
    thr = np.quantile(neg, 1 - fpr)
    pos = np.asarray(pos, float); pos = pos[~np.isnan(pos)]
    return float(np.mean(pos > thr))
