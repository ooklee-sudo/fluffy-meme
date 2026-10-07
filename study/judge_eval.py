"""PRE-SPECIFIED comparison of zero-shot LLM judges with the Poisson-based detectors on the SAME 500 documents.
For every generator G: AUC of (judge p_ai) and of two Poisson detectors for human-vs-G on the judged subset.
 Poisson 'unseen' detector: trained on human + the OTHER two generators (never G)  -> comparable to a zero-shot judge
 Poisson 'same-gen' detector: trained on human + G (grouped CV)                    -> upper reference
Features: baseline (rates + 500-token dispersion) and NEW (rates + scale-dependent clustering). Paired bootstrap for differences.
Also: per-field (medicine only = clean XML text), cost and latency per document.   Usage: python3 judge_eval.py <judge1> [judge2 ...]"""
import sys, json, io, contextlib, glob, numpy as np, runpy
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, balanced_accuracy_score

judges = sys.argv[1:]
with contextlib.redirect_stdout(io.StringIO()):
    ns = runpy.run_path("newmodel.py", run_name="lib")
FAM, H, G, fold, build = ns["FAM"], ns["H"], dict(ns["G"]), ns["fold"], ns["build"]
load = lambda p: [json.loads(l) for l in open(p, encoding="utf-8")]
G["llama"] = build(list({r["human_id"]: r for r in load("data/synthetic/llama.jsonl")}.values()), "human_id")
key = {k["id"]: k for k in load("data/judge_key.jsonl")}
GENS = ["gpt4o", "claude", "llama"]

def poisson_scores(target, trains, fam):
    out = {}
    for k in range(5):
        tr = [(FAM[fam](f), 0) for g, f in H if fold[g] != k]
        for t in trains: tr += [(FAM[fam](f), 1) for g, f in G[t] if fold.get(g, -1) != k]
        X = np.array([x for x, _ in tr]); y = np.array([c for _, c in tr]); mu, sd = X.mean(0), X.std(0) + 1e-9
        w = np.array([1.0 if c == 0 else len(H) / max(1, sum(len(G[t]) for t in trains)) for c in y])
        clf = LogisticRegression(max_iter=4000).fit((X - mu) / sd, y, sample_weight=w)
        te = [(("human", g), f) for g, f in H if fold[g] == k] + [((target, g), f) for g, f in G[target] if fold.get(g, -1) == k]
        P = clf.predict_proba((np.array([FAM[fam](f) for _, f in te]) - mu) / sd)[:, 1]
        for (k2, _), p in zip(te, P): out[k2] = p
    return out

def auc_ci(y, s, B=2000, seed=3):
    r = np.random.RandomState(seed); a = []
    for _ in range(B):
        i = r.randint(0, len(y), len(y))
        if y[i].min() != y[i].max(): a.append(roc_auc_score(y[i], s[i]))
    return roc_auc_score(y, s), np.percentile(a, [2.5, 97.5])
def fmt(y, s): a, (lo, hi) = auc_ci(y, s); return f"{a:.3f} [{lo:.2f},{hi:.2f}]"

J = {}
for j in judges:
    rows = load(f"data/judge/{j}.jsonl"); J[j] = {r["id"]: r for r in rows}
    ok = [r for r in rows if r["p_ai"] is not None]
    print(f"judge {j}: {len(rows)} judged, {len(rows)-len(ok)} unparseable; mean {np.mean([r['seconds'] for r in rows]):.1f}s/doc, "
          f"mean cost ${np.mean([r['usage'].get('cost', 0) for r in rows]):.4f}/doc")
print()
for field_only in (None, "medicine"):
    print("== " + ("All documents" if field_only is None else "Medicine (PubMed XML) documents only") + " ==")
    print(f"{'target':8s}{'n(h/s)':>9s}" + "".join(f"{('judge:'+j):>24s}" for j in judges) + f"{'Poisson base (unseen)':>24s}{'Poisson NEW (unseen)':>24s}{'Poisson NEW (same-gen)':>24s}")
    for g in GENS:
        ids = [i for i, k in key.items() if k["source"] in ("human", g) and (field_only is None or k["field"] == field_only)]
        ps = {fam: poisson_scores(g, [t for t in GENS if t != g], fam) for fam in ("baseline: rates+disp500", "NEW: rates+(a,b)")}
        same = poisson_scores(g, [g], "NEW: rates+(a,b)")
        cols = []
        keep = [i for i in ids if (key[i]["source"], key[i]["source_id"]) in ps["NEW: rates+(a,b)"] and all(i in J[j] and J[j][i]["p_ai"] is not None for j in judges)]
        y = np.array([0 if key[i]["source"] == "human" else 1 for i in keep])
        line = f"{g:8s}{f'{(y==0).sum()}/{(y==1).sum()}':>9s}"
        for j in judges: line += f"{fmt(y, np.array([J[j][i]['p_ai'] for i in keep])):>24s}"
        for d in (ps["baseline: rates+disp500"], ps["NEW: rates+(a,b)"], same):
            line += f"{fmt(y, np.array([d[(key[i]['source'], key[i]['source_id'])] for i in keep])):>24s}"
        print(line, flush=True)
    print()
# judge calibration at the natural threshold (p_ai >= 50)
print("== Judge accuracy at threshold p_ai>=50 (balanced accuracy; human vs each generator) ==")
for j in judges:
    for g in GENS:
        ids = [i for i, k in key.items() if k["source"] in ("human", g) and i in J[j] and J[j][i]["p_ai"] is not None]
        y = np.array([0 if key[i]["source"] == "human" else 1 for i in ids]); p = np.array([J[j][i]["p_ai"] >= 50 for i in ids])
        print(f"  {j:12s} vs {g:7s} balanced acc = {balanced_accuracy_score(y, p):.3f}   flagged as AI: human {p[y==0].mean():.2f}, {g} {p[y==1].mean():.2f}")
