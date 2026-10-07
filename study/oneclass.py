"""Human-only (one-class) detectors: trained on human papers, no generator data at all.
Primary method fixed in advance: Mahalanobis distance (Ledoit-Wolf covariance). Secondary: One-Class SVM, Isolation Forest.
Anomaly score is evaluated as AUC for 'synthetic' vs held-out human (grouped 5-fold on human papers)."""
import json, numpy as np
from sklearn.covariance import LedoitWolf
from sklearn.svm import OneClassSVM
from sklearn.ensemble import IsolationForest
from sklearn.metrics import roc_auc_score
import features as F

load = lambda p: [json.loads(l) for l in open(p, encoding="utf-8")]
human = load("data/human.jsonl")
gens = {g: list({r["human_id"]: r for r in load(f"data/synthetic/{g}.jsonl")}.values()) for g in ("gpt4o", "claude")}
def feats(t):
    C = F.counts(t)
    if C.shape[0] < F.MAXWIN: return None
    m, di, _, _ = F.doc_stats(C)
    return np.log1p(m), np.log(np.clip(np.nan_to_num(di, nan=1.0), .05, None))
def build(rows, key):
    o = [(r[key], feats(r["text"])) for r in rows]; return [(g, f) for g, f in o if f is not None]
H = build(human, "id"); G = {g: build(r, "human_id") for g, r in gens.items()}
groups = sorted({g for g, _ in H}); rng = np.random.RandomState(0); rng.shuffle(groups); fold = {g: i % 5 for i, g in enumerate(groups)}
sel = {"rates": lambda f: f[0], "dispersion": lambda f: f[1], "both": lambda f: np.concatenate(f)}

def fit_score(method, Xtr, Xte):
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9; A, B = (Xtr - mu) / sd, (Xte - mu) / sd
    if method == "mahalanobis":
        lw = LedoitWolf().fit(A); return lw.mahalanobis(B)
    if method == "ocsvm":
        return -OneClassSVM(gamma="scale", nu=0.05).fit(A).score_samples(B)
    if method == "iforest":
        return -IsolationForest(n_estimators=300, random_state=0).fit(A).score_samples(B)

def ci(y, s, B=1000):
    r = np.random.RandomState(1); a = []
    for _ in range(B):
        i = r.randint(0, len(y), len(y))
        if y[i].min() != y[i].max(): a.append(roc_auc_score(y[i], s[i]))
    return np.percentile(a, [2.5, 97.5])

print(f"human={len(H)} gpt4o={len(G['gpt4o'])} claude={len(G['claude'])}  (AUC [95% CI]; trained on human papers only)\n")
out = []
for method in ("mahalanobis", "ocsvm", "iforest"):
    print(f"== {method} ==" + ("   [primary, fixed in advance]" if method == "mahalanobis" else ""))
    print(f"{'test generator':16s}" + "".join(f"{f:>26s}" for f in sel))
    for gname in G:
        line = f"{gname:16s}"
        for fam in sel:
            ys, ss = [], []
            for k in range(5):
                tr = np.array([sel[fam](f) for g, f in H if fold[g] != k])
                te_h = [sel[fam](f) for g, f in H if fold[g] == k]
                te_s = [sel[fam](f) for g, f in G[gname] if fold.get(g, -1) == k]
                s = fit_score(method, tr, np.array(te_h + te_s)); ys += [0] * len(te_h) + [1] * len(te_s); ss += list(s)
            y, s = np.array(ys), np.array(ss); a = roc_auc_score(y, s); lo, hi = ci(y, s)
            line += f"{a:12.3f} [{lo:.2f},{hi:.2f}]"
        print(line)
    print()
