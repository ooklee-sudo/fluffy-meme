"""RQ1/RQ2 analysis. Human data: data/human.jsonl. Synthetic data: data/synthetic/<model>.jsonl
with fields {human_id, text}. Optional judge scores: data/judge/<model>.jsonl {id, score, seconds, usd}."""
import json, glob, os, time, sys
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.metrics import roc_auc_score, f1_score
import features as F

load = lambda p: [json.loads(l) for l in open(p, encoding="utf-8")]
human = load("data/human.jsonl")
syn = {os.path.basename(p)[:-6]: load(p) for p in glob.glob("data/synthetic/*.jsonl")}

def prep(rows, label, model):
    out = []
    for r in rows:
        t0 = time.perf_counter(); C = F.counts(r["text"]); s = F.doc_stats(C); dt = time.perf_counter() - t0
        if C.shape[0] >= F.MAXWIN:
            out.append(dict(id=r.get("id", r.get("human_id")), group=r.get("human_id", r.get("id")), label=label, model=model,
                            field=r.get("field"), n_win=C.shape[0], stat=s, sec=dt, words=len(r["text"].split())))
    return out

H = prep(human, 0, "human")
S = [d for m, rows in syn.items() for d in prep(rows, 1, m)]
hf = {r["id"]: r["field"] for r in human}
for d in S: d["field"] = hf.get(d["group"])
print(f"human n={len(H)}; synthetic n={len(S)} models={list(syn)}")

# --- Stage 2: Poisson goodness-of-fit on human text -------------------------------------------
gof = []
for d in H:
    mean, di, p_over, p_under = d["stat"]
    for i, n in enumerate(F.NAMES):
        if mean[i] > 0: gof.append(dict(feature=n, model="human", di=di[i], rej_over=p_over[i] < .05, rej_under=p_under[i] < .05))
for d in S:
    mean, di, p_over, p_under = d["stat"]
    for i, n in enumerate(F.NAMES):
        if mean[i] > 0: gof.append(dict(feature=n, model=d["model"], di=di[i], rej_over=p_over[i] < .05, rej_under=p_under[i] < .05))
G = pd.DataFrame(gof)
tab = G.groupby(["model", "feature"]).agg(median_DI=("di", "median"), pct_overdisp=("rej_over", "mean"), pct_underdisp=("rej_under", "mean")).round(3)
tab.to_csv("results_gof.csv"); print(tab.to_string())

# --- Stage 1: detection (cross-validated, grouped by source paper) ----------------------------
if S:
    D = H + S
    groups = np.array([d["group"] for d in D]); y = np.array([d["label"] for d in D])
    p_score = np.zeros(len(D)); X = np.zeros((len(D), 2 * len(F.NAMES)))
    for tr, te in GroupKFold(5).split(X, y, groups):
        ps = F.PoissonScore().fit([D[i]["stat"] for i in tr if y[i] == 0])   # reference from human TRAIN only
        for i in te: p_score[i] = ps.score(D[i]["stat"]); X[i] = ps.components(D[i]["stat"])
    res = {"Poisson-Score (single index)": roc_auc_score(y, p_score)}
    clf = LogisticRegression(max_iter=2000, C=1.0)
    pr = cross_val_predict(clf, X, y, groups=groups, cv=GroupKFold(5), method="predict_proba")[:, 1]
    res["Poisson components (logistic)"] = roc_auc_score(y, pr)
    f1 = f1_score(y, pr > .5)
    print(pd.Series(res).round(3), "F1(logistic)=", round(f1, 3))
    for m in syn:
        idx = [i for i, d in enumerate(D) if d["model"] in ("human", m)]
        print(m, "AUC single:", round(roc_auc_score(y[idx], p_score[idx]), 3), "AUC logistic:", round(roc_auc_score(y[idx], pr[idx]), 3))
    # --- RQ2: cost / latency ---------------------------------------------------------------
    sec = np.mean([d["sec"] for d in D]); print(f"Poisson pipeline: {1/sec:.1f} docs/s on one CPU core, USD/doc = 0 (no API)")
    for p in glob.glob("data/judge/*.jsonl"):
        J = load(p); print(os.path.basename(p), "judge sec/doc", np.mean([j["seconds"] for j in J]), "USD/doc", np.mean([j["usd"] for j in J]))
