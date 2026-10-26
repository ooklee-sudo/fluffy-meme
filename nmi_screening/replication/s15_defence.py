"""Step 15: defences against adaptive authors, evaluated on every attack, per target (each target has its own supervised models).
Components (higher = more machine-like), standardized with the calibration humans of the same target (median, robust SD):
 fd Fast-DetectGPT, rb fine-tuned RoBERTa, tf TF-IDF, sc count screen (clustering), dl two-sided log-likelihood |loglik - median_cal|, de two-sided entropy.
Ensembles (no learned weights): mean3/max3 over fd, rb, sc; mean4/max4/top2 over fd, rb, sc, dl.
Operating point: threshold = 95th percentile of the calibration humans; the false-positive rate is then measured on the evaluation humans.
python3 s15_defence.py"""
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
from common import *
rng = np.random.default_rng(0)
S = pd.read_csv(os.path.join(DATA, "defence_scores.csv"))
METHODS = ["ll", "bi", "fd", "rb", "tf", "sc", "dl", "de", "mean3", "max3", "mean4", "max4", "top2"]
def ci_auc(neg, pos, B=400):
    y = np.r_[np.zeros(len(neg)), np.ones(len(pos))]; a = roc_auc_score(y, np.r_[neg, pos]); bs = []
    for _ in range(B):
        i = rng.integers(0, len(neg), len(neg)); j = rng.integers(0, len(pos), len(pos)); bs.append(roc_auc_score(y, np.r_[neg[i], pos[j]]))
    return a, np.percentile(bs, 2.5), np.percentile(bs, 97.5)
rows = []
for t, T in S.groupby("target"):
    cal = T[T.group == "cal"]
    def z(x, c):
        med = np.median(c); sd = 1.4826 * np.median(np.abs(c - med)); return (x - med) / (sd if sd > 0 else 1.0)
    Z = pd.DataFrame(index=T.index)
    for m in ("fd", "rb", "tf", "sc"): Z[m] = z(T[m], cal[m])
    Z["ll"] = z(T["loglik"], cal["loglik"]); Z["bi"] = z(T["binoculars"], cal["binoculars"])
    for m, src in (("dl", "loglik"), ("de", "entropy")):
        med = cal[src].median(); Z[m] = z((T[src] - med).abs(), (cal[src] - med).abs())
    Z["mean3"] = Z[["fd", "rb", "sc"]].mean(axis=1); Z["max3"] = Z[["fd", "rb", "sc"]].max(axis=1)
    Z["mean4"] = Z[["fd", "rb", "sc", "dl"]].mean(axis=1); Z["max4"] = Z[["fd", "rb", "sc", "dl"]].max(axis=1)
    Z["top2"] = np.sort(Z[["fd", "rb", "sc", "dl"]].values, axis=1)[:, -2:].mean(axis=1)
    thr = {m: np.percentile(Z.loc[cal.index, m], 95) for m in METHODS}
    neg = Z.loc[T[T.group == "eval_neg"].index]
    for (g, cond), P in T[T.group == "attacked"].groupby(["generator", "cond"]):
        pos = Z.loc[P.index]
        for m in METHODS:
            a, lo, hi = ci_auc(neg[m].values, pos[m].values)
            rows.append(dict(target=t, generator=g, cond=cond, method=m, auc=a, lo=lo, hi=hi, tpr=(pos[m] > thr[m]).mean(), fpr=(neg[m] > thr[m]).mean(), n=len(P)))
R = pd.DataFrame(rows); R.to_csv(os.path.join(DATA, "defence_results.csv"), index=False)
pd.set_option("display.width", 250)
main = R[R.target != "econ"]
print("AUC, mean over generators:"); print(main.pivot_table(index="method", columns="cond", values="auc").round(2).to_string())
print("\nWorst case over generators and attacks (AUC):"); print(main[main.cond != "orig"].groupby("method").auc.min().round(2).to_string())
print("\nTPR at the calibrated 5% threshold, mean over generators:"); print(main.pivot_table(index="method", columns="cond", values="tpr").round(2).to_string())
print("\nFPR on evaluation humans:", R.groupby("method").fpr.mean().round(3).to_dict())
print("\nEconomics field (AUC):"); print(R[R.target == "econ"].pivot_table(index="method", columns=["generator", "cond"], values="auc").round(2).to_string())
