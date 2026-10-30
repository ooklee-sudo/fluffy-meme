"""Dose-response around eight model releases. Exposure = tag-level accuracy of a reference model on pre-2022 questions (level, not delta).
Outcome per tag and release: change in mean ln(1+weekly new questions) between the 7 weeks before and the 7 weeks after the release week,
minus the same change averaged over the 3 prior years (calendar-aligned). Covariate: the tag's change over the 7 weeks before the pre window.
Sources: HF dump (weeks before 2023-01-23) and the Stack Exchange API (weeks from 2023-01-23)."""
import csv, json, math, statistics as st, datetime as dt, collections, sys
import numpy as np
D = dt.date
hf = collections.defaultdict(dict); api = collections.defaultdict(dict)
for r in csv.DictReader(open("panel_tag_week.csv")): hf[r["tag"]][D.fromisoformat(r["week"])] = int(r["n"])
for l in open("panel_api_tag_week.jsonl"):
    x = json.loads(l); api[x["tag"]][D.fromisoformat(x["week"])] = x["n"]
SPLIT = D(2023, 1, 23)
def lnq(t, w): return math.log(1 + (api[t].get(w, 0) if w >= SPLIT else hf[t].get(w, 0)))
def avg(t, start, k=7): return st.mean(lnq(t, start + dt.timedelta(7 * j)) for j in range(k))
REL = [("ChatGPT", D(2022, 11, 30), "free"), ("GPT-4", D(2023, 3, 14), "paid"), ("Claude 2", D(2023, 7, 11), "free"),
       ("GPT-4 Turbo", D(2023, 11, 6), "paid"), ("Claude 3", D(2024, 3, 4), "partial"), ("GPT-4o", D(2024, 5, 13), "free"),
       ("Claude 3.5 Sonnet", D(2024, 6, 20), "free"), ("o1-preview", D(2024, 9, 12), "paid")]
def monday(d): return d - dt.timedelta(d.weekday())
def change(t, rel, shift=0):
    rw = monday(rel) - dt.timedelta(shift)
    return avg(t, rw + dt.timedelta(7)) - avg(t, rw - dt.timedelta(49))        # post 7 wks minus pre 7 wks (release week excluded)
def pretrend(t, rel, shift=0):
    rw = monday(rel) - dt.timedelta(shift)
    return avg(t, rw - dt.timedelta(49)) - avg(t, rw - dt.timedelta(98))
def yoy(t, rel, shift=0):
    rw = monday(rel) - dt.timedelta(shift); w = rw - dt.timedelta(49)
    return avg(t, w) - avg(t, w - dt.timedelta(364))
rows = {}
for l in open("results_v2.jsonl"):
    x = json.loads(l); rows.setdefault((x["qid"], x["tag"], x["model"]), x)
def acc(model):
    d = collections.defaultdict(list)
    for (q, t, m), x in rows.items():
        if m == model and x["correct"] is not None: d[t].append(x["correct"])
    return {t: st.mean(v) for t, v in d.items() if len(v) >= 15}
A = acc(sys.argv[1] if len(sys.argv) > 1 else "gpt-3.5")
tags = [t for t in A if t in hf and t in api]
print("exposure model:", sys.argv[1] if len(sys.argv) > 1 else "gpt-3.5", "| tags:", len(tags))
a = np.array([A[t] for t in tags]); a = (a - a.mean()) / a.std()
def ols_cluster(y, X, g):
    X1 = np.column_stack([np.ones(len(y)), X]); XtXi = np.linalg.inv(X1.T @ X1); b = XtXi @ X1.T @ y; e = y - X1 @ b
    meat = sum(np.outer(X1[g == c].T @ e[g == c], X1[g == c].T @ e[g == c]) for c in np.unique(g))
    V = XtXi @ meat @ XtXi * len(np.unique(g)) / (len(np.unique(g)) - 1); return b, np.sqrt(np.diag(V))
print("\n%-18s %-8s %9s %8s %7s | placebo(-1y) %7s" % ("release", "access", "beta/SD", "se", "t", "beta"))
Y, X, G, R, F = [], [], [], [], []
for ri, (name, d, acc_) in enumerate(REL):
    sh = (364, 728, 1092)
    y = np.array([change(t, d) - st.mean(change(t, d, s) for s in sh) for t in tags])
    pt = np.array([pretrend(t, d) - st.mean(pretrend(t, d, s) for s in sh) for t in tags])
    yy = np.array([yoy(t, d) for t in tags]); yy = (yy - yy.mean()) / yy.std()
    b, se = ols_cluster(y, np.column_stack([a, pt, yy]), np.arange(len(tags)))
    yp = np.array([change(t, d, 364) - st.mean(change(t, d, s) for s in (728, 1092, 1456)) for t in tags])
    ptp = np.array([pretrend(t, d, 364) for t in tags]); yyp = np.array([yoy(t, d, 364) for t in tags]); yyp = (yyp - yyp.mean()) / yyp.std()
    bp, sp = ols_cluster(yp, np.column_stack([a, ptp, yyp]), np.arange(len(tags)))
    print("%-18s %-8s %+9.3f %8.3f %7.2f | placebo %+7.3f (t %.2f)" % (name, acc_, b[1], se[1], b[1] / se[1], bp[1], bp[1] / sp[1]), "  mean change %+.3f" % y.mean())
    for i in range(len(tags)): Y.append(y[i]); X.append([a[i], pt[i], yy[i]]); G.append(i); R.append(ri); F.append(1.0 if acc_ == "free" else (0.0 if acc_ == "paid" else np.nan))
Y, X, G, R, F = map(np.array, (Y, X, G, R, F))
ok = ~np.isnan(F)
Xs = np.column_stack([X[ok], X[ok, 0] * F[ok]] + [(R[ok] == r).astype(float) for r in sorted(set(R[ok]))[1:]])
b, se = ols_cluster(Y[ok], Xs, G[ok])
print("\nStacked (release fixed effects, clustered by tag; partial-access release excluded):")
print("  accuracy x paid release (beta/SD):  %+.3f (se %.3f)" % (b[1], se[1]))
print("  accuracy x free-vs-paid difference: %+.3f (se %.3f, t %.2f)   [H2 predicts a more negative effect for free releases]" % (b[4], se[4], b[4] / se[4]))
