"""Score the paraphrase-attacked machine papers with the count-based screens and compare with the same papers unattacked.
Detectors: trained on clean human + the other two generators (never the target), 5-fold by source paper (as elsewhere).
Negative class = all clean human papers; positive = the attacked (or, for comparison, original) machine papers of the target.
Usage: python3 score_attacked.py <level> [<level> ...]   (reads data/attack/<level>_full.jsonl)"""
import sys, json, io, contextlib, runpy, numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
with contextlib.redirect_stdout(io.StringIO()):
    ns = runpy.run_path("newmodel.py", run_name="lib")
doc_feats, FAM, H, fold, clean_feats = ns["doc_feats"], ns["FAM"], ns["H"], ns["fold"], ns["G"]
load = lambda p: [json.loads(l) for l in open(p, encoding="utf-8")]
key = {k["id"]: k for k in load("data/judge_key.jsonl")}
from attack_paraphrase import clean
ORIG = {}
for g in ("gpt4o", "claude", "llama"):
    for r in load(f"data/synthetic/{g}.jsonl"): ORIG[(g, r["human_id"])] = r["text"]
CL = {g: dict(v) for g, v in {g: ns["build"](list({r["human_id"]: r for r in load(f"data/synthetic/{g}.jsonl")}.values()), "human_id") for g in ("gpt4o", "claude", "llama")}.items()}
fam = FAM["NEW: rates+(a,b)"]
def run(g, texts):                       # texts: {source_id: text}; returns clean-vs-attacked on the same papers
    others = [t for t in CL if t != g]; hs, ys_c, ys_a = [], [], []
    A = {sid: doc_feats(t) for sid, t in texts.items()}
    O = {sid: doc_feats(" ".join(clean(ORIG[(g, sid)]))) for sid in texts}      # original, cleaned like the attacked input
    for k in range(5):
        tr = [(fam(f), 0) for gid, f in H if fold[gid] != k]
        for t in others: tr += [(fam(f), 1) for gid, f in CL[t].items() if fold.get(gid, -1) != k]
        X = np.array([x for x, _ in tr]); y = np.array([c for _, c in tr]); mu, sd = X.mean(0), X.std(0) + 1e-9
        w = np.array([1.0 if c == 0 else len(H) / max(1, sum(len(CL[t]) for t in others)) for c in y])
        clf = LogisticRegression(max_iter=4000).fit((X - mu) / sd, y, sample_weight=w); P = lambda L: clf.predict_proba((np.array(L) - mu) / sd)[:, 1]
        hs += list(P([fam(f) for gid, f in H if fold[gid] == k]))
        ys_a += list(P([fam(f) for sid, f in A.items() if f is not None and fold.get(sid, -1) == k]))
        ys_c += list(P([fam(f) for sid, f in O.items() if f is not None and A[sid] is not None and fold.get(sid, -1) == k]))
    thr = np.quantile(hs, 0.95); out = []
    for ys in (ys_c, ys_a):
        y = np.r_[np.zeros(len(hs)), np.ones(len(ys))]; s = np.r_[hs, ys]; out.append((roc_auc_score(y, s), float((np.array(ys) > thr).mean()), len(ys)))
    return out
if __name__ == "__main__":
    for level in sys.argv[1:]:
        rows = {r["id"]: r for r in load(f"data/attack/{level}_full.jsonl")}
        print(f"\n== attack level {level}: {len(rows)} rewritten papers ==\n{'target':8s}{'n':>5s}   original AUC / det@5%FPR    attacked AUC / det@5%FPR")
        res = {}
        for g in ("gpt4o", "claude", "llama"):
            texts = {key[i]["source_id"]: r["text"] for i, r in rows.items() if key[i]["source"] == g}
            if not texts: continue
            (ac, dc, n), (aa, da, _) = run(g, texts); res[g] = (ac, dc, aa, da)
            print(f"{g:8s}{n:5d}        {ac:.3f} / {dc:.2f}                {aa:.3f} / {da:.2f}")
        if res: print(f"{'mixture':8s}{'':5s}        {np.mean([v[0] for v in res.values()]):.3f} / {np.mean([v[1] for v in res.values()]):.2f}                {np.mean([v[2] for v in res.values()]):.3f} / {np.mean([v[3] for v in res.values()]):.2f}")
