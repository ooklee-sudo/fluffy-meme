"""Which signal drives detection? rate-only vs dispersion-only vs both; per-feature AUC; within-field comparison."""
import json, numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.metrics import roc_auc_score
import features as F

load = lambda p: [json.loads(l) for l in open(p, encoding="utf-8")]
human = load("data/human.jsonl"); hf = {r["id"]: r["field"] for r in human}
syn = {}
for r in load("data/synthetic/gpt4o.jsonl"): syn[r["human_id"]] = r          # dedupe by source paper
rows = []
for r in human: rows.append((r["id"], r["id"], 0, r["field"], r["text"]))
for k, r in syn.items(): rows.append((k + "_s", k, 1, hf.get(k), r["text"]))
D = []
for i, g, y, fld, t in rows:
    C = F.counts(t)
    if C.shape[0] >= F.MAXWIN: D.append((g, y, fld, F.doc_stats(C)))
y = np.array([d[1] for d in D]); grp = np.array([d[0] for d in D]); fld = np.array([d[2] for d in D])
rate = np.array([np.log1p(d[3][0]) for d in D])
disp = np.array([np.log(np.clip(np.nan_to_num(d[3][1], nan=1.0), .05, None)) for d in D])
print(f"n human={int((y==0).sum())}, n gpt4o={int((y==1).sum())}")

def cv_auc(X, mask=None):
    m = np.ones(len(y), bool) if mask is None else mask
    X, yy, g = X[m], y[m], grp[m]
    p = cross_val_predict(LogisticRegression(max_iter=3000, C=1.0), (X - X.mean(0)) / (X.std(0) + 1e-9), yy, groups=g, cv=GroupKFold(5), method="predict_proba")[:, 1]
    return roc_auc_score(yy, p)

print("\n== Which signal? (5-fold, grouped by source paper) ==")
for name, X in [("rates only", rate), ("dispersion only", disp), ("rates + dispersion", np.hstack([rate, disp]))]:
    print(f"{name:22s} AUC={cv_auc(X):.3f}")
print("\n== Within field (human vs gpt4o in the SAME field) ==")
for f in ["medicine", "computer_science"]:
    m = fld == f
    print(f"{f:18s} rates={cv_auc(rate, m):.3f}  dispersion={cv_auc(disp, m):.3f}  both={cv_auc(np.hstack([rate, disp]), m):.3f}  (n={int(m.sum())})")
print("\n== Single-feature AUC (0.5 = no signal) ==")
tab = []
for j, n in enumerate(F.NAMES):
    tab.append((n, roc_auc_score(y, rate[:, j]), roc_auc_score(y, disp[:, j])))
print(pd.DataFrame(tab, columns=["feature", "AUC_rate", "AUC_dispersion"]).round(3).to_string(index=False))
