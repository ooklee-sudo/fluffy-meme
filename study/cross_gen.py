"""Within-generator vs cross-generator detection, by feature family (rates / dispersion / both)."""
import json, numpy as np
from sklearn.linear_model import LogisticRegression
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
def run(train, test, fam):
    ys, ss = [], []
    for k in range(5):
        tr = [(sel[fam](f), 0) for g, f in H if fold[g] != k] + [(sel[fam](f), 1) for g, f in G[train] if fold.get(g, -1) != k]
        X = np.array([x for x, _ in tr]); y = np.array([c for _, c in tr]); mu, sd = X.mean(0), X.std(0) + 1e-9
        clf = LogisticRegression(max_iter=3000).fit((X - mu) / sd, y)
        te = [(sel[fam](f), 0) for g, f in H if fold[g] == k] + [(sel[fam](f), 1) for g, f in G[test] if fold.get(g, -1) == k]
        Xt = np.array([x for x, _ in te]); ys += [c for _, c in te]; ss += list(clf.predict_proba((Xt - mu) / sd)[:, 1])
    return np.array(ys), np.array(ss)
def ci(y, sc, B=1000):
    r = np.random.RandomState(1); a = []
    for _ in range(B):
        idx = r.randint(0, len(y), len(y))
        if y[idx].min() != y[idx].max(): a.append(roc_auc_score(y[idx], sc[idx]))
    return np.percentile(a, [2.5, 97.5])
print(f"human={len(H)}  gpt4o={len(G['gpt4o'])}  claude={len(G['claude'])}   (AUC [95% bootstrap CI])\n")
print(f"{'train -> test':18s}" + "".join(f"{f:>26s}" for f in sel))
rows = []
for tr, te in [("gpt4o", "gpt4o"), ("claude", "claude"), ("gpt4o", "claude"), ("claude", "gpt4o")]:
    line = f"{tr+' -> '+te:18s}"
    for f in sel:
        y, sc = run(tr, te, f); a = roc_auc_score(y, sc); lo, hi = ci(y, sc)
        line += f"{a:12.3f} [{lo:.2f},{hi:.2f}]"
    print(line)
