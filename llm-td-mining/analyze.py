"""Paired within-author comparison of AI-labeled vs. other commits.

Usage: python analyze.py out/*.jsonl
Non-AI commits count only if made on or after the author's first AI-labeled commit.
"""
import json, sys, statistics as st
from collections import defaultdict
from scipy.stats import wilcoxon

MIN_EACH = 5
MAX_ADD = 5000

def load(path):
    rows = [json.loads(l) for l in open(path)]
    return [r for r in rows if r["add"] <= MAX_ADD]

def author_metrics(rows):
    s = dict(n=len(rows), add=sum(r["add"] for r in rows), dele=sum(r["dele"] for r in rows),
             satd=sum(r["satd"] for r in rows), elig=sum(r["elig"] for r in rows), dup=sum(r["dup"] for r in rows))
    return dict(
        n=s["n"],
        net=s["add"] / max(1, s["add"] + s["dele"]),          # share of changed lines that are additions
        satd=1000 * s["satd"] / max(1, s["add"]),              # SATD markers per 1,000 added lines
        dup=100 * s["dup"] / max(1, s["elig"]),                # % of non-trivial added lines duplicated in-commit
        size=st.median(r["add"] + r["dele"] for r in rows),
    )

def pairs(rows, band=None):
    by = defaultdict(list)
    for r in rows:
        by[r["author"]].append(r)
    out = []
    for a, rs in by.items():
        ai = [r for r in rs if r["ai"]]
        if not ai:
            continue
        t0 = min(r["ts"] for r in ai)
        hu = [r for r in rs if not r["ai"] and r["ts"] >= t0]
        if band:
            ai = [r for r in ai if band[0] <= r["add"] <= band[1]]
            hu = [r for r in hu if band[0] <= r["add"] <= band[1]]
        if len(ai) >= MIN_EACH and len(hu) >= MIN_EACH:
            out.append((a, author_metrics(ai), author_metrics(hu)))
    return out

def summarize(label, ps):
    res = {"label": label, "authors": len(ps),
           "ai_commits": sum(p[1]["n"] for p in ps), "other_commits": sum(p[2]["n"] for p in ps)}
    for k in ["net", "satd", "dup", "size"]:
        a = [p[1][k] for p in ps]; h = [p[2][k] for p in ps]
        d = [x - y for x, y in zip(a, h)]
        p = wilcoxon(a, h).pvalue if len(ps) >= 6 and any(d) else float("nan")
        res[k] = dict(ai_median=round(st.median(a), 3), other_median=round(st.median(h), 3),
                      median_diff=round(st.median(d), 3), share_ai_higher=round(sum(x > 0 for x in d) / len(d), 3),
                      p=float(f"{p:.3g}"))
    return res

if __name__ == "__main__":
    allp, allb, results = [], [], []
    for path in sys.argv[1:]:
        name = path.split("/")[-1].replace(".jsonl", "").replace("_", "/", 1)
        rows = load(path)
        ps = pairs(rows)
        allp += ps
        allb += pairs(rows, band=(10, 300))
        if len(ps) >= 6:
            results.append(summarize(name, ps))
        else:
            results.append({"label": name, "authors": len(ps)})
    results.append(summarize("POOLED", allp))
    results.append(summarize("POOLED, commits with 10-300 added lines", allb))
    print(json.dumps(results, indent=1))
