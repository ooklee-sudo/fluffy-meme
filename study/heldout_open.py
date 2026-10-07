"""PRE-SPECIFIED confirmatory test (written before the open-model data exist).
Held-out generator H is never used for training. The detector is trained on human papers plus ALL OTHER available
generators (pooled), with grouped 5-fold CV on source papers. PRIMARY comparison: baseline (rates + 500-token dispersion)
vs scale-dependent clustering model (rates + (a,b)), AUC on human-vs-H, with a paired bootstrap of the difference.
Secondary: each single training generator -> H. No settings are tuned on H.
Usage: python3 heldout_open.py <held_out_name>   (file data/synthetic/<name>.jsonl)"""
import sys, json, io, contextlib, numpy as np, runpy
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

held = sys.argv[1]
with contextlib.redirect_stdout(io.StringIO()):
    ns = runpy.run_path("newmodel.py", run_name="lib")
doc_feats, FAM, H, G, fold, build = ns["doc_feats"], ns["FAM"], ns["H"], dict(ns["G"]), ns["fold"], ns["build"]
load = lambda p: [json.loads(l) for l in open(p, encoding="utf-8")]
if held not in G:
    G[held] = build(list({r["human_id"]: r for r in load(f"data/synthetic/{held}.jsonl")}.values()), "human_id")
train_sets = [g for g in G if g != held]
print(f"held-out generator = {held} (n={len(G[held])}); trained on human + {train_sets}")

def run(fam, trains):
    ys, ss = [], []
    for k in range(5):
        tr = [(FAM[fam](f), 0) for g, f in H if fold[g] != k]
        for t in trains: tr += [(FAM[fam](f), 1) for g, f in G[t] if fold.get(g, -1) != k]
        X = np.array([x for x, _ in tr]); y = np.array([c for _, c in tr]); mu, sd = X.mean(0), X.std(0) + 1e-9
        w = np.array([1.0 if c == 0 else len(H) / max(1, sum(len(G[t]) for t in trains)) for c in y]) # balance classes
        clf = LogisticRegression(max_iter=4000).fit((X - mu) / sd, y, sample_weight=w)
        te = [(FAM[fam](f), 0) for g, f in H if fold[g] == k] + [(FAM[fam](f), 1) for g, f in G[held] if fold.get(g, -1) == k]
        Xt = np.array([x for x, _ in te]); ys += [c for _, c in te]; ss += list(clf.predict_proba((Xt - mu) / sd)[:, 1])
    return np.array(ys), np.array(ss)

def paired(trains, new="NEW: rates+(a,b)", base="baseline: rates+disp500", B=2000):
    y1, s1 = run(new, trains); y2, s2 = run(base, trains); assert (y1 == y2).all()
    r = np.random.RandomState(7); d = []; a1 = []; a2 = []
    for _ in range(B):
        i = r.randint(0, len(y1), len(y1))
        if y1[i].min() != y1[i].max():
            u, v = roc_auc_score(y1[i], s1[i]), roc_auc_score(y1[i], s2[i]); a1.append(u); a2.append(v); d.append(u - v)
    f = lambda a: np.percentile(a, [2.5, 97.5])
    return roc_auc_score(y1, s2), f(a2), roc_auc_score(y1, s1), f(a1), roc_auc_score(y1, s1) - roc_auc_score(y1, s2), f(d)

print(f"\n{'trained on':28s}{'baseline AUC':>22s}{'new AUC':>22s}{'diff [95% CI]':>26s}")
combos = [train_sets] + [[t] for t in train_sets] if len(train_sets) > 1 else [train_sets]
for trains in combos:
    b, bc, n, nc, d, dc = paired(trains)
    label = "PRIMARY: " + "+".join(trains) if trains == train_sets and len(train_sets) > 1 else "+".join(trains)
    print(f"{label:28s}{b:8.3f} [{bc[0]:.2f},{bc[1]:.2f}]{n:9.3f} [{nc[0]:.2f},{nc[1]:.2f}]{d:+9.3f} [{dc[0]:+.3f},{dc[1]:+.3f}]", flush=True)
