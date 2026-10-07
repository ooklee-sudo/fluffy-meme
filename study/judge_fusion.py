"""PRE-SPECIFIED fusion of the cheap Poisson screen with LLM-judge scores (no weights are fitted; label-free rank fusion).
 Components per target generator G, on the documents that BOTH judges answered (same set as Table 7):
   P  = Poisson NEW detector trained on human + the other two generators (never G)
   Gm = Gemini 2.5 Pro p_ai ;  Gp = GPT-4o p_ai
 Scores are rank-normalised within the evaluated pool (human subset + G subset), which uses no labels.
 PRIMARY F1 = mean rank of (P, Gm).  Secondary F2 = max rank of (P, Gm);  F3 = mean rank of (P, Gm, Gp).
 Reported: AUC [95% CI]; paired bootstrap of fusion minus each component; TPR at 5% false-positive rate (descriptive)."""
import sys, io, contextlib, runpy, numpy as np
from scipy.stats import rankdata
from sklearn.metrics import roc_auc_score
sys.argv = ["judge_eval.py", "gpt4o", "gemini"]
with contextlib.redirect_stdout(io.StringIO()):
    ns = runpy.run_path("judge_eval.py", run_name="lib")
key, J, GENS, poisson_scores = ns["key"], ns["J"], ns["GENS"], ns["poisson_scores"]
rk = lambda x: (rankdata(x) - 1) / (len(x) - 1)
def ci(y, s, B=2000):
    r = np.random.RandomState(3); a = []
    for _ in range(B):
        i = r.randint(0, len(y), len(y))
        if y[i].min() != y[i].max(): a.append(roc_auc_score(y[i], s[i]))
    return np.percentile(a, [2.5, 97.5])
def pdiff(y, a, b, B=3000):
    r = np.random.RandomState(5); d = []
    for _ in range(B):
        i = r.randint(0, len(y), len(y))
        if y[i].min() != y[i].max(): d.append(roc_auc_score(y[i], a[i]) - roc_auc_score(y[i], b[i]))
    return roc_auc_score(y, a) - roc_auc_score(y, b), np.percentile(d, [2.5, 97.5])
def tpr_at_fpr(y, s, fpr=0.05):
    thr = np.quantile(s[y == 0], 1 - fpr); return float((s[y == 1] > thr).mean())

print(f"{'target':8s}{'n(h/s)':>9s}{'method':>22s}{'AUC [95% CI]':>22s}{'TPR@5%FPR':>12s}")
summary = []
for g in GENS:
    ps = poisson_scores(g, [t for t in GENS if t != g], "NEW: rates+(a,b)")
    keep = [i for i, k in key.items() if k["source"] in ("human", g) and (k["source"], k["source_id"]) in ps
            and all(i in J[j] and J[j][i]["p_ai"] is not None for j in ("gpt4o", "gemini"))]
    y = np.array([0 if key[i]["source"] == "human" else 1 for i in keep])
    P = np.array([ps[(key[i]["source"], key[i]["source_id"])] for i in keep])
    Gm = np.array([J["gemini"][i]["p_ai"] for i in keep]); Gp = np.array([J["gpt4o"][i]["p_ai"] for i in keep])
    rP, rGm, rGp = rk(P), rk(Gm), rk(Gp)
    M = {"Poisson new": P, "Gemini judge": Gm, "GPT-4o judge": Gp,
         "F1 mean(P,Gemini)": (rP + rGm) / 2, "F2 max(P,Gemini)": np.maximum(rP, rGm), "F3 mean(P,Gem,GPT)": (rP + rGm + rGp) / 3}
    for name, s in M.items():
        a = roc_auc_score(y, s); lo, hi = ci(y, s)
        print(f"{g:8s}{f'{(y==0).sum()}/{(y==1).sum()}':>9s}{name:>22s}{a:12.3f} [{lo:.2f},{hi:.2f}]{tpr_at_fpr(y, s):12.2f}")
    for f in ("F1 mean(P,Gemini)", "F2 max(P,Gemini)", "F3 mean(P,Gem,GPT)"):
        for c in ("Poisson new", "Gemini judge"):
            d, (lo, hi) = pdiff(y, M[f], M[c]); summary.append((g, f, c, d, lo, hi))
    print()
print("== Paired AUC differences: fusion minus component ==")
for g, f, c, d, lo, hi in summary:
    print(f"  {g:7s} {f:20s} - {c:13s}: {d:+.3f} [{lo:+.3f},{hi:+.3f}]")
