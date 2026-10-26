"""Step 4: screens within and across generators (Tables 1-4 of the manuscript).
5-fold cross-validation grouped by source paper; logistic regression on standardized features; AUC with 95% bootstrap intervals.
  rates / dispersion / both                      : 7 + 7 baseline features
  baseline (unseen protocol) / clustering        : rates + 500-token dispersion  vs  rates + scale-dependent clustering features (21)
python3 s4_screens.py
"""
import itertools, json, os
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.covariance import EmpiricalCovariance
from common import DATA

EV = ["paren", "bracket", "semicolon", "quote", "marker", "passive", "nominal"]
RATES = [f"rate_{e}" for e in EV]; DISP = [f"disp_{e}" for e in EV]
CLUST = RATES + [f"fano_mean_{e}" for e in EV] + [f"fano_slope_{e}" for e in EV]
SETS = {"rates": RATES, "dispersion": DISP, "both": RATES + DISP, "clustering": CLUST}
df = pd.read_csv(os.path.join(DATA, "features.csv")); gens = [g for g in ("gpt4o", "claude", "llama") if (df.generator == g).any()]
rng = np.random.default_rng(0)

def cv_scores(train_gens, test_gen, cols, human_only=False, folds=5):
    keep = df[(df.generator == "human") | df.generator.isin(set(train_gens) | {test_gen})].reset_index(drop=True)
    out = []
    for tri, tei in GroupKFold(n_splits=folds).split(keep, keep.label, groups=keep.source):
        tr = keep.iloc[tri]; te = keep.iloc[tei]
        tr = tr[(tr.generator == "human") | tr.generator.isin(train_gens)]
        te = te[(te.generator == "human") | (te.generator == test_gen)]
        if human_only:
            h = tr[tr.generator == "human"][cols].values; mu = h.mean(0); cov = EmpiricalCovariance().fit(h)
            s = cov.mahalanobis(te[cols].values - 0)  # squared distance from the human mean (fit centers on its own mean)
            out.append(pd.DataFrame(dict(id=te.id.values, label=te.label.values, score=s)))
        else:
            m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=1.0)).fit(tr[cols].values, tr.label.values)
            out.append(pd.DataFrame(dict(id=te.id.values, label=te.label.values, score=m.predict_proba(te[cols].values)[:, 1])))
    return pd.concat(out, ignore_index=True)

def auc_ci(r, n=1000):
    a = roc_auc_score(r.label, r.score); bs = []
    for _ in range(n):
        rr = r.iloc[rng.integers(0, len(r), len(r))]
        if rr.label.nunique() == 2: bs.append(roc_auc_score(rr.label, rr.score))
    return a, np.percentile(bs, 2.5), np.percentile(bs, 97.5)

def fmt(t): return f"{t[0]:.3f} [{t[1]:.2f}, {t[2]:.2f}]"
res = {}
print("== Table 1 analogue: within and across generators (train -> test), AUC [95% CI]")
for a_, b_ in itertools.product(gens, gens):
    row = {k: fmt(auc_ci(cv_scores([a_], b_, SETS[k]))) for k in ("rates", "dispersion", "both")}
    res[f"{a_}->{b_}"] = row; print(f"{a_:>6} -> {b_:<6}", row)
print("\n== Unseen-generator protocol: train on human + the other generators, test on the target")
for g in gens:
    others = [x for x in gens if x != g]
    base = cv_scores(others, g, RATES + DISP); clus = cv_scores(others, g, CLUST)
    m = base.merge(clus, on=["id", "label"], suffixes=("_b", "_c")); diffs = []
    for _ in range(1000):
        r = m.iloc[rng.integers(0, len(m), len(m))]
        if r.label.nunique() == 2: diffs.append(roc_auc_score(r.label, r.score_c) - roc_auc_score(r.label, r.score_b))
    d = roc_auc_score(m.label, m.score_c) - roc_auc_score(m.label, m.score_b)
    res[f"unseen:{g}"] = dict(baseline=fmt(auc_ci(base)), clustering=fmt(auc_ci(clus)), diff=f"{d:+.3f} [{np.percentile(diffs,2.5):+.3f}, {np.percentile(diffs,97.5):+.3f}]")
    print(f"{g:>6}: baseline {res['unseen:'+g]['baseline']}  clustering {res['unseen:'+g]['clustering']}  diff {res['unseen:'+g]['diff']}")
print("\n== Human-only (anomaly) screens, Mahalanobis distance")
for g in gens:
    res[f"human_only:{g}"] = {k: fmt(auc_ci(cv_scores([], g, SETS[k], human_only=True))) for k in ("rates", "dispersion", "both", "clustering")}
    print(g, res[f"human_only:{g}"])
json.dump(res, open(os.path.join(DATA, "screen_results.json"), "w"), indent=1)
