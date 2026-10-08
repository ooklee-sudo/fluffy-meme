"""PRE-SPECIFIED: Gemini judge and screen+judge fusion on attacked machine papers.
For each condition (clean, p2 = LLM rewrite, h1 = rewrite+edit, p = edit only) and target generator, on the judged pool
(196 clean human papers + the target's ~100 machine papers): AUC and share detected at 5% FPR for the screen alone, the Gemini judge
alone, and the rank-average fusion F1 (label-free, as in the main analysis). Screen = clustering detector never trained on the target
nor on Llama (the rewriter), cross-validated by source paper; every text is scored from the 2,000-token excerpt the judge saw.
Usage: python3 judge_attack_fusion.py clean p2 h1 p"""
import sys, json, io, contextlib, runpy, numpy as np
from scipy.stats import rankdata
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
with contextlib.redirect_stdout(io.StringIO()):
    ns = runpy.run_path("newmodel.py", run_name="lib")
doc_feats, FAM, H, fold, build = ns["doc_feats"], ns["FAM"], ns["H"], ns["fold"], ns["build"]
load = lambda p: [json.loads(l) for l in open(p, encoding="utf-8")]
key = {k["id"]: k for k in load("data/judge_key.jsonl")}
CL = {g: dict(build(list({r["human_id"]: r for r in load(f"data/synthetic/{g}.jsonl")}.values()), "human_id")) for g in ("gpt4o", "claude", "llama")}
INP = {r["id"]: r["text"] for r in load("data/judge_input.jsonl")}
GEM = {"clean": {r["id"]: r["p_ai"] for r in load("data/judge/gemini.jsonl")}}
fam = FAM["NEW: rates+(a,b)"]
hum_ids = [i for i, k in key.items() if k["source"] == "human" and GEM["clean"].get(i) is not None and i in INP]
def texts(level):
    if level == "clean": return {i: INP[i] for i, k in key.items() if k["source"] != "human"}
    return {r["id"]: r["text"] for r in load(f"data/attack/{level}_judge.jsonl")}
def gem(level):
    if level not in GEM: GEM[level] = {r["id"]: r["p_ai"] for r in load(f"data/judge/gemini_{level}.jsonl")}
    return GEM[level]
HF = {i: doc_feats(INP[i]) for i in hum_ids}
def screen_scores(g, mach):                    # mach: {id: features}; returns {id: score} for judged humans (CV) and the target's machine docs
    excl = ("llama",) if g != "llama" else ()
    others = [t for t in CL if t != g and t not in excl]; out = {}
    for k in range(5):
        tr = [(fam(f), 0) for gid, f in H if fold[gid] != k]
        for t in others: tr += [(fam(f), 1) for gid, f in CL[t].items() if fold.get(gid, -1) != k]
        X = np.array([x for x, _ in tr]); y = np.array([c for _, c in tr]); mu, sd = X.mean(0), X.std(0) + 1e-9
        w = np.array([1.0 if c == 0 else len(H) / max(1, sum(len(CL[t]) for t in others)) for c in y])
        clf = LogisticRegression(max_iter=4000).fit((X - mu) / sd, y, sample_weight=w)
        ids_k = [i for i in hum_ids if HF[i] is not None and fold.get(key[i]["source_id"], -1) == k] + [i for i, f in mach.items() if f is not None and fold.get(key[i]["source_id"], -1) == k]
        P = clf.predict_proba((np.array([fam(HF[i] if i in HF else mach[i]) for i in ids_k]) - mu) / sd)[:, 1]
        out.update(dict(zip(ids_k, P)))
    return out
def ci(y, s, B=1000):
    r = np.random.RandomState(3); a = []
    for _ in range(B):
        i = r.randint(0, len(y), len(y))
        if y[i].min() != y[i].max(): a.append(roc_auc_score(y[i], s[i]))
    return np.percentile(a, [2.5, 97.5])
def det(y, s): return float((s[y == 1] > np.quantile(s[y == 0], 0.95)).mean())
rk = lambda x: (rankdata(x) - 1) / (len(x) - 1)
def cell(y, s): a = roc_auc_score(y, s); lo, hi = ci(y, s); return f"{a:.3f} [{lo:.2f},{hi:.2f}] / {det(y, s):.2f}"
for level in sys.argv[1:]:
    T, G = texts(level), gem(level)
    print(f"\n== condition {level}: AUC [95% CI] / share detected at 5% FPR ==\n{'target':8s}{'n(h/m)':>9s}{'screen':>28s}{'Gemini judge':>28s}{'fusion F1':>28s}")
    for g in ("gpt4o", "claude", "llama"):
        mach = {i: doc_feats(t) for i, t in T.items() if key[i]["source"] == g}; S = screen_scores(g, mach)
        ids_m = [i for i in mach if mach[i] is not None and i in S and G.get(i) is not None]
        ids_h = [i for i in hum_ids if i in S]
        ids = ids_h + ids_m; y = np.array([0] * len(ids_h) + [1] * len(ids_m))
        sc = np.array([S[i] for i in ids]); jd = np.array([GEM["clean"][i] if i in set(ids_h) else G[i] for i in ids], float)
        fu = (rk(sc) + rk(jd)) / 2
        print(f"{g:8s}{f'{len(ids_h)}/{len(ids_m)}':>9s}{cell(y, sc):>28s}{cell(y, jd):>28s}{cell(y, fu):>28s}", flush=True)
