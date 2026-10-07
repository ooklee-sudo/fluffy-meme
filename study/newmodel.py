"""Scale-dependent clustering (Cox-process) model.
Counts of each event arise from a Poisson process whose rate varies along the document (doubly stochastic).
The Fano factor F(w)=var/mean of counts in windows of w tokens then depends on w; we summarize each event by
  rate (per 500 tokens), a = log F at the smallest scale, b = slope of log F on log w  (moment-based estimates).
PRE-SPECIFIED comparison (fixed before running): baseline = rates + dispersion at 500 tokens (as in the paper),
new = rates + (a, b). Primary outcomes: cross-generator AUC (both directions) and one-class AUC (Mahalanobis).
Only the first 2000 tokens of each document are used (length matched)."""
import json, numpy as np, re, sys
from sklearn.linear_model import LogisticRegression
from sklearn.covariance import LedoitWolf
from sklearn.metrics import roc_auc_score
import features as F

SCALES = (50, 100, 200, 400); TOTAL = 2000
load = lambda p: [json.loads(l) for l in open(p, encoding="utf-8")]
human = load("data/human.jsonl")
gens = {g: list({r["human_id"]: r for r in load(f"data/synthetic/{g}.jsonl")}.values()) for g in ("gpt4o", "claude")}

def doc_feats(text):
    toks = F.TOK.findall(text)
    if len(toks) < TOTAL: return None
    toks = toks[:TOTAL]
    counts = {w: np.array([[f(" ".join(toks[i:i + w])) for f in F.FEATURES.values()] for i in range(0, TOTAL, w)], float) for w in SCALES}
    rate = np.log1p(counts[100].sum(0) / (TOTAL / 500))                      # mean count per 500 tokens (log1p)
    logF = []
    for w in SCALES:
        C = counts[w]; m = C.mean(0); v = C.var(0, ddof=1)
        logF.append(np.log(np.clip(np.where(m > 0, v / np.maximum(m, 1e-9), 1.0), .05, 20)))
    logF = np.array(logF)                                                   # (scales, events)
    x = np.log(np.array(SCALES, float)); x = x - x.mean()
    b = (x[:, None] * (logF - logF.mean(0))).sum(0) / (x ** 2).sum()        # slope: clustering growth with scale
    a = logF.mean(0) - b * 0                                                # mean level of clustering across scales
    # baseline feature: dispersion at 500 tokens (4 windows), exactly as in the paper
    C5 = F.counts(text); m5, di5, _, _ = F.doc_stats(C5); base_disp = np.log(np.clip(np.nan_to_num(di5, nan=1.0), .05, None))
    return dict(rate=rate, a=a, b=b, base=base_disp)

def build(rows, key):
    out = []
    for r in rows:
        f = doc_feats(r["text"])
        if f is not None: out.append((r[key], f))
    return out
H = build(human, "id"); G = {g: build(r, "human_id") for g, r in gens.items()}
print(f"docs: human={len(H)} gpt4o={len(G['gpt4o'])} claude={len(G['claude'])}", flush=True)

FAM = {
    "baseline: rates+disp500": lambda f: np.concatenate([f["rate"], f["base"]]),
    "baseline: disp500 only":  lambda f: f["base"],
    "NEW: rates+(a,b)":        lambda f: np.concatenate([f["rate"], f["a"], f["b"]]),
    "NEW: (a,b) only":         lambda f: np.concatenate([f["a"], f["b"]]),
    "NEW: slope b only":       lambda f: f["b"],
}
groups = sorted({g for g, _ in H}); rng = np.random.RandomState(0); rng.shuffle(groups); fold = {g: i % 5 for i, g in enumerate(groups)}

def sup(train, test, fam):
    ys, ss = [], []
    for k in range(5):
        tr = [(FAM[fam](f), 0) for g, f in H if fold[g] != k] + [(FAM[fam](f), 1) for g, f in G[train] if fold.get(g, -1) != k]
        X = np.array([x for x, _ in tr]); y = np.array([c for _, c in tr]); mu, sd = X.mean(0), X.std(0) + 1e-9
        clf = LogisticRegression(max_iter=4000).fit((X - mu) / sd, y)
        te = [(FAM[fam](f), 0) for g, f in H if fold[g] == k] + [(FAM[fam](f), 1) for g, f in G[test] if fold.get(g, -1) == k]
        Xt = np.array([x for x, _ in te]); ys += [c for _, c in te]; ss += list(clf.predict_proba((Xt - mu) / sd)[:, 1])
    return np.array(ys), np.array(ss)
def oneclass(test, fam):
    ys, ss = [], []
    for k in range(5):
        A = np.array([FAM[fam](f) for g, f in H if fold[g] != k]); mu, sd = A.mean(0), A.std(0) + 1e-9
        lw = LedoitWolf().fit((A - mu) / sd)
        te_h = [FAM[fam](f) for g, f in H if fold[g] == k]; te_s = [FAM[fam](f) for g, f in G[test] if fold.get(g, -1) == k]
        Xt = (np.array(te_h + te_s) - mu) / sd; ys += [0] * len(te_h) + [1] * len(te_s); ss += list(lw.mahalanobis(Xt))
    return np.array(ys), np.array(ss)
def ci(y, s, B=500):
    r = np.random.RandomState(1); a = []
    for _ in range(B):
        i = r.randint(0, len(y), len(y))
        if y[i].min() != y[i].max(): a.append(roc_auc_score(y[i], s[i]))
    return np.percentile(a, [2.5, 97.5])
def cell(y, s): a = roc_auc_score(y, s); lo, hi = ci(y, s); return f"{a:.3f} [{lo:.2f},{hi:.2f}]"

print("\n== Supervised (human + one generator) ==")
tests = [("gpt4o", "gpt4o"), ("claude", "claude"), ("gpt4o", "claude"), ("claude", "gpt4o")]
print(f"{'feature set':26s}" + "".join(f"{a+'->'+b:>22s}" for a, b in tests))
for fam in FAM:
    print(f"{fam:26s}" + "".join(f"{cell(*sup(a, b, fam)):>22s}" for a, b in tests), flush=True)
print("\n== One-class (human papers only; Mahalanobis) ==")
print(f"{'feature set':26s}{'gpt4o':>22s}{'claude':>22s}")
for fam in FAM:
    print(f"{fam:26s}" + "".join(f"{cell(*oneclass(g, fam)):>22s}" for g in G), flush=True)
