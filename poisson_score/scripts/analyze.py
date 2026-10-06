"""Study-1 analysis: logistic regression (H1a), incremental AUC with DeLong test (H1b).

  python scripts/analyze.py pilot.csv --baselines base_feats.csv

pilot.csv comes from `python -m poisson_score.cli pilot ... -o pilot.csv` (columns: file,label,n_tokens,
n_windows,poisson_score,...). Optional --meta joins extra control columns (generator, field, level) on `file` stem.
--baselines: CSV with `file` plus numeric baseline detector columns (e.g. mauve, judge_prob, loglik).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline


def delong_test(y, s1, s2):
    """Two-sided DeLong test for two correlated ROC AUCs (DeLong et al. 1988). Returns auc1, auc2, p."""
    y = np.asarray(y).astype(bool)
    def comps(s):
        s = np.asarray(s, float)
        pos, neg = s[y], s[~y]
        m, n = len(pos), len(neg)
        psi = (pos[:, None] > neg[None, :]) + 0.5 * (pos[:, None] == neg[None, :])
        return psi.mean(), psi.mean(1), psi.mean(0), m, n
    a1, v10_1, v01_1, m, n = comps(s1)
    a2, v10_2, v01_2, _, _ = comps(s2)
    s10 = np.cov(np.vstack([v10_1, v10_2]))
    s01 = np.cov(np.vstack([v01_1, v01_2]))
    S = s10 / m + s01 / n
    var = S[0, 0] + S[1, 1] - 2 * S[0, 1]
    z = (a1 - a2) / np.sqrt(var) if var > 0 else np.nan
    return a1, a2, float(2 * stats.norm.sf(abs(z)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--meta", help="CSV with `file` + control columns")
    ap.add_argument("--baselines")
    ap.add_argument("--cluster", help="column to cluster SEs on (e.g. topic id)")
    a = ap.parse_args()

    d = pd.read_csv(a.csv)
    d["y"] = (d["label"] == "synthetic").astype(int)
    d["log_windows"] = np.log(d["n_windows"].clip(lower=1))
    d["stem"] = d["file"].map(lambda p: Path(p).stem)
    if a.meta:
        d = d.merge(pd.read_csv(a.meta).rename(columns={"file": "stem"}), on="stem", how="left")
    d = d.dropna(subset=["poisson_score"])

    controls = [c for c in ("generator", "field", "level") if c in d.columns]
    formula = "y ~ poisson_score + log_windows" + "".join(f" + C({c})" for c in controls)
    kw = {}
    if a.cluster and a.cluster in d.columns:
        kw = dict(cov_type="cluster", cov_kwds={"groups": pd.factorize(d[a.cluster])[0]})
    m = smf.logit(formula, d).fit(disp=0, **kw)
    b = m.params["poisson_score"]; ci = m.conf_int().loc["poisson_score"]
    print(f"H1a: beta(Poisson-Score)={b:.3f}  95% CI [{ci[0]:.3f}, {ci[1]:.3f}]  p={m.pvalues['poisson_score']:.4f}  "
          f"OR per +0.1={np.exp(.1 * b):.2f}  -> {'SUPPORTED' if b > 0 and ci[0] > 0 else 'not supported'}")

    if a.baselines:
        bl = pd.read_csv(a.baselines); bl["stem"] = bl["file"].map(lambda p: Path(p).stem)
        d = d.merge(bl.drop(columns="file"), on="stem")
        cols = [c for c in bl.columns if c not in ("file", "stem")]
        y = d["y"].values
        cv = StratifiedKFold(5, shuffle=True, random_state=0)
        mk = lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
        s_base = cross_val_predict(mk(), d[cols], y, cv=cv, method="decision_function")
        s_aug = cross_val_predict(mk(), d[cols + ["poisson_score", "log_windows"]], y, cv=cv, method="decision_function")
        a_aug, a_base, p = delong_test(y, s_aug, s_base)
        print(f"H1b: AUC baselines={a_base:.3f}  +Poisson-Score={a_aug:.3f}  DeLong p={p:.4f}")
    else:
        print("H1b skipped (no --baselines).")


if __name__ == "__main__":
    main()
