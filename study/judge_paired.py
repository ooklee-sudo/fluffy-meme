"""Paired bootstrap of AUC differences: Poisson (unseen-generator detectors) minus zero-shot judge, same documents."""
import sys, io, contextlib, runpy, numpy as np
from sklearn.metrics import roc_auc_score
judges = sys.argv[1:]
buf = io.StringIO()
sys.argv = ["judge_eval.py"] + judges
with contextlib.redirect_stdout(buf):
    ns = runpy.run_path("judge_eval.py", run_name="lib")   # reuse its data/functions (prints suppressed)
key, J, GENS, poisson_scores = ns["key"], ns["J"], ns["GENS"], ns["poisson_scores"]
def diff(y, a, b, B=3000):
    r = np.random.RandomState(5); d = []
    for _ in range(B):
        i = r.randint(0, len(y), len(y))
        if y[i].min() != y[i].max(): d.append(roc_auc_score(y[i], a[i]) - roc_auc_score(y[i], b[i]))
    return roc_auc_score(y, a) - roc_auc_score(y, b), np.percentile(d, [2.5, 97.5])
for j in judges:
    print(f"== Poisson (unseen-generator detector) minus judge '{j}' ==")
    for fam, name in (("baseline: rates+disp500", "baseline"), ("NEW: rates+(a,b)", "NEW")):
        for g in GENS:
            ps = poisson_scores(g, [t for t in GENS if t != g], fam)
            keep = [i for i, k in key.items() if k["source"] in ("human", g) and (k["source"], k["source_id"]) in ps and i in J[j] and J[j][i]["p_ai"] is not None]
            y = np.array([0 if key[i]["source"] == "human" else 1 for i in keep])
            d, (lo, hi) = diff(y, np.array([ps[(key[i]["source"], key[i]["source_id"])] for i in keep]), np.array([J[j][i]["p_ai"] for i in keep]))
            print(f"  {name:9s} vs judge, {g:7s}: dAUC = {d:+.3f}  [{lo:+.3f}, {hi:+.3f}]")
