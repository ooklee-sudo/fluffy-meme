"""Agreement statistics for LLM-vs-human (or LLM-vs-LLM) coding."""
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import cohen_kappa_score

import prompts


def krippendorff_alpha_ordinal(a, b):
    """Krippendorff's alpha (ordinal metric) for two coders, no missing values."""
    a, b = np.asarray(a), np.asarray(b)
    vals = np.unique(np.concatenate([a, b]))
    idx = {v: i for i, v in enumerate(vals)}
    k = len(vals)
    o = np.zeros((k, k))
    for x, y in zip(a, b):
        o[idx[x], idx[y]] += 1
        o[idx[y], idx[x]] += 1
    n_c = o.sum(1)
    n = n_c.sum()
    cum = np.cumsum(n_c)
    delta = np.zeros((k, k))
    for i in range(k):
        for j in range(k):
            lo, hi = min(i, j), max(i, j)
            delta[i, j] = (cum[hi] - n_c[hi] / 2 - (cum[lo] - n_c[lo] / 2)) ** 2
    d_o = (o * delta).sum() / n
    d_e = (np.outer(n_c, n_c) * delta).sum() / (n * (n - 1))
    return 1.0 if d_e == 0 else 1 - d_o / d_e


def agreement_table(coder_a: pd.DataFrame, coder_b: pd.DataFrame) -> pd.DataFrame:
    """Rows aligned by index. Ordinal -> quadratic-weighted kappa, alpha, Spearman; others -> Cohen's kappa."""
    rows = []
    for f in prompts.CODED_FIELDS:
        a, b = coder_a[f], coder_b[f]
        r = {"field": f, "n": len(a)}
        if f in prompts.SCORE_FIELDS:
            r["kappa"] = cohen_kappa_score(a, b, weights="quadratic")
            r["alpha_ordinal"] = krippendorff_alpha_ordinal(a, b)
            r["spearman"] = spearmanr(a, b)[0]
        else:
            r["kappa"] = cohen_kappa_score(a, b)
        rows.append(r)
    return pd.DataFrame(rows)
