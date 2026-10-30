import json, collections, statistics as st, math
import numpy as np
def load(f, key):
    d = {}
    for l in open(f):
        x = json.loads(l); d.setdefault(key(x), x)
    return d
V = load("results_v2.jsonl", lambda x: (x["qid"], x["tag"], x["model"]))
Fm = load("results_formats.jsonl", lambda x: (x["qid"], x["tag"], x["model"], x["fmt"]))
tags = list(dict.fromkeys(q["tag"] for q in json.load(open("questions_v2.json"))))[:30]
cells = collections.defaultdict(dict)   # (model, fmt) -> {(tag, qid): correct}
for (q, t, m), x in V.items():
    if t in tags and x["correct"] is not None: cells[(m, "F1")][(t, q)] = x["correct"]
for (q, t, m, f), x in Fm.items(): cells[(m, f)][(t, q)] = x["correct"]
def tagacc(cell, qids=None, minn=10):
    d = collections.defaultdict(list)
    for (t, q), c in cell.items():
        if qids is None or q in qids: d[t].append(c)
    return {t: st.mean(v) for t, v in d.items() if len(v) >= minn}
def corr(a, b): return float(np.corrcoef(a, b)[0, 1])
def rank(v): return np.argsort(np.argsort(v)).astype(float)
def split_rel(cell, qids):
    ev = {k: c for i, (k, c) in enumerate(sorted(cell.items())) if i % 2 == 0 and k[1] in qids}
    od = {k: c for i, (k, c) in enumerate(sorted(cell.items())) if i % 2 == 1 and k[1] in qids}
    a, b = tagacc(ev, minn=5), tagacc(od, minn=5); ts = [t for t in a if t in b]
    r = corr([a[t] for t in ts], [b[t] for t in ts]); return 2 * r / (1 + r)
for m in ("gpt-3.5", "llama-3.1-8b"):
    qids = set.intersection(*[{q for (t, q) in cells[(m, f)]} for f in ("F1", "F2", "F3")])
    A = {f: tagacc(cells[(m, f)], qids) for f in ("F1", "F2", "F3")}; ts = [t for t in A["F1"] if all(t in A[f] for f in A)]
    print(f"\n== {m}: {len(ts)} tags, {len(qids)} questions common to all formats")
    print("   level by format: " + ", ".join(f"{f} {100*np.mean([A[f][t] for t in ts]):.1f}%" for f in A))
    print("   tag-level SD:    " + ", ".join(f"{f} {np.std([A[f][t] for t in ts]):.3f}" for f in A))
    rel = {f: split_rel(cells[(m, f)], qids) for f in A}
    print("   split-half reliability of tag accuracy: " + ", ".join(f"{f} {rel[f]:.2f}" for f in A))
    for f1, f2 in (("F1", "F2"), ("F1", "F3"), ("F2", "F3")):
        x, y = [A[f1][t] for t in ts], [A[f2][t] for t in ts]
        ceil = math.sqrt(max(rel[f1], 0) * max(rel[f2], 0))
        print(f"   {f1} vs {f2}: Pearson {corr(x, y):.2f}, Spearman {corr(rank(x), rank(y)):.2f}  (ceiling from noise: {ceil:.2f})")
# GPT-4o vs GPT-3.5 delta, F1 and F2, on the questions GPT-4o has
q4 = {q for (t, q) in cells[("gpt-4o", "F2")]}
print(f"\n== GPT-4o minus GPT-3.5 (tag-level delta), {len(q4)} questions")
D = {}
for f in ("F1", "F2"):
    a4, a3 = tagacc(cells[("gpt-4o", f)], q4, 8), tagacc(cells[("gpt-3.5", f)], q4, 8); D[f] = {t: a4[t] - a3[t] for t in a4 if t in a3}
ts = [t for t in D["F1"] if t in D["F2"]]
print(f"   {len(ts)} tags; mean delta F1 {100*np.mean([D['F1'][t] for t in ts]):+.1f} pp, F2 {100*np.mean([D['F2'][t] for t in ts]):+.1f} pp")
x, y = [D["F1"][t] for t in ts], [D["F2"][t] for t in ts]
print(f"   corr(delta under F1, delta under F2): Pearson {corr(x, y):.2f}, Spearman {corr(rank(x), rank(y)):.2f}")
