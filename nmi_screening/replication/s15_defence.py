"""Step 15: defences against adaptive authors, evaluated on every attack.
Components (higher = more machine-like), each standardized with the 100 calibration human papers (median, robust SD):
 fd   : Fast-DetectGPT          rb : fine-tuned RoBERTa          sc : count screen (clustering)          dl : two-sided log-likelihood, |loglik - median_cal|
Ensembles (parameter-free): mean-z, max-z, top2-z. Operating point: threshold at the 95th percentile of the calibration humans; the false-positive rate is then measured on the 200 evaluation humans.
python3 s15_defence.py  (reads data/defence_scores.csv with columns id, cond, generator, field, fd, rb, sc, tf, loglik, entropy, label, group)"""
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
from common import *
rng = np.random.default_rng(0)
S = pd.read_csv(os.path.join(DATA, "defence_scores.csv"))
cal = S[S.group == "cal"]; ev_neg = S[S.group == "eval_neg"]
def rz(col, f=None):
    x = f(S[col]) if f else S[col]; c = f(cal[col]) if f else cal[col]; med = np.median(c); sd = 1.4826 * np.median(np.abs(c - med)) or 1.0
    return (x - med) / sd
med_l = cal.loglik.median(); med_e = cal.entropy.median()
Z = pd.DataFrame({"fd": rz("fd"), "rb": rz("rb"), "sc": rz("sc"), "tf": rz("tf"), "dl": rz("loglik", lambda s: (s - med_l).abs()), "de": rz("entropy", lambda s: (s - med_e).abs())})
Z["mean4"] = Z[["fd", "rb", "sc", "dl"]].mean(axis=1); Z["max4"] = Z[["fd", "rb", "sc", "dl"]].max(axis=1); Z["top2"] = Z[["fd", "rb", "sc", "dl"]].apply(lambda r: np.sort(r.values)[-2:].mean(), axis=1)
Z["max3"] = Z[["fd", "rb", "sc"]].max(axis=1); Z["mean3"] = Z[["fd", "rb", "sc"]].mean(axis=1)
D = S[["id", "cond", "generator", "field", "group"]].join(Z)
NAMES = ["fd", "rb", "sc", "tf", "dl", "mean3", "mean4", "max4", "top2"]
def ci_auc(neg, pos, col, B=500):
    y = np.r_[np.zeros(len(neg)), np.ones(len(pos))]; s = np.r_[neg[col].values, pos[col].values]; a = roc_auc_score(y, s); bs = []
    for _ in range(B):
        i = rng.integers(0, len(neg), len(neg)); j = rng.integers(0, len(pos), len(pos)); bs.append(roc_auc_score(np.r_[np.zeros(len(i)), np.ones(len(j))], np.r_[neg[col].values[i], pos[col].values[j]]))
    return a, np.percentile(bs, 2.5), np.percentile(bs, 97.5)
rows = []
for field in sorted(D.field.dropna().unique()):
    neg = D[(D.group == "eval_neg") & (D.field == field)]
    thr = {c: np.percentile(D[(D.group == "cal") & (D.field == "main")][c], 95) for c in NAMES}
    for (g, cond), pos in D[(D.group == "attacked") & (D.field == field)].groupby(["generator", "cond"]):
        for c in NAMES:
            a, lo, hi = ci_auc(neg, pos, c); rows.append(dict(field=field, generator=g, cond=cond, method=c, auc=a, lo=lo, hi=hi, tpr=(pos[c] > thr[c]).mean(), fpr=(neg[c] > thr[c]).mean(), n=len(pos)))
R = pd.DataFrame(rows); R.to_csv(os.path.join(DATA, "defence_results.csv"), index=False)
print(R[R.field == "main"].pivot_table(index=["method"], columns="cond", values="auc").round(2).to_string())
