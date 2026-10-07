"""Generalization: train on human + GPT-4o, test on human vs a generator the model never saw.
Usage: python3 heldout.py <train_generator> <heldout_generator>   (files in data/synthetic/<name>.jsonl)"""
import json, sys, numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score
import features as F

train_g, test_g = sys.argv[1], sys.argv[2]
load = lambda p: [json.loads(l) for l in open(p, encoding="utf-8")]
dedupe = lambda rows: list({r["human_id"]: r for r in rows}.values())
human = load("data/human.jsonl")
S = {g: dedupe(load(f"data/synthetic/{g}.jsonl")) for g in (train_g, test_g)}

def feats(text):
    C = F.counts(text)
    if C.shape[0] < F.MAXWIN: return None
    m, di, _, _ = F.doc_stats(C)
    return np.concatenate([np.log1p(m), np.log(np.clip(np.nan_to_num(di, nan=1.0), .05, None))])
def build(rows, y, key):
    out = []
    for r in rows:
        x = feats(r["text"])
        if x is not None: out.append((r[key], x, y))
    return out
H = build(human, 0, "id")
A = build(S[train_g], 1, "human_id"); B = build(S[test_g], 1, "human_id")
print(f"human={len(H)} train-gen={len(A)} heldout-gen={len(B)}")
groups = sorted({g for g, _, _ in H})
rng = np.random.RandomState(0); rng.shuffle(groups); fold = {g: i % 5 for i, g in enumerate(groups)}
res = {"in-gen": [], "held": []}; yh = []; ph = []; ps_in = []; yin = []
Ht, Bt = [], []
for k in range(5):
    tr = [(x, y) for g, x, y in H + A if fold.get(g, -1) != k]
    te_h = [x for g, x, y in H if fold.get(g, -1) == k]
    te_a = [x for g, x, y in A if fold.get(g, -1) == k]
    te_b = [x for g, x, y in B if fold.get(g, -1) == k]
    X = np.array([x for x, _ in tr]); yy = np.array([y for _, y in tr]); mu, sd = X.mean(0), X.std(0) + 1e-9
    clf = LogisticRegression(max_iter=3000).fit((X - mu) / sd, yy)
    sc = lambda L: clf.predict_proba((np.array(L) - mu) / sd)[:, 1] if len(L) else np.array([])
    Hs, As, Bs = sc(te_h), sc(te_a), sc(te_b)
    res["in-gen"] += [(0, s) for s in Hs] + [(1, s) for s in As]; res["held"] += [(0, s) for s in Hs] + [(1, s) for s in Bs]
for name, L in res.items():
    y, s = zip(*L); print(f"{name:7s} AUC = {roc_auc_score(y, s):.3f}  (n={len(y)})")
