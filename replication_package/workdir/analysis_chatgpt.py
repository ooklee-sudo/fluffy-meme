"""ChatGPT-release dose-response: does tag-level GPT-3.5 accuracy predict the seasonally adjusted post-release drop in new questions?
Outcome per tag: [mean ln(1+n) over 7 post weeks - same over 7 pre weeks] in 2022 minus the same change averaged over the 3 prior years
(same calendar-aligned weeks). Treatment: Acc(gpt-3.5); instrument: Acc(llama-3.1-8b) for errors-in-variables."""
import csv, json, math, statistics as st, datetime as dt, collections, sys
import numpy as np
D = dt.date
panel = collections.defaultdict(dict)
for r in csv.DictReader(open("panel_tag_week.csv")): panel[r["tag"]][D.fromisoformat(r["week"])] = int(r["n"])
def lnq(t, w): return math.log(1 + panel[t].get(w, 0))
pre0, post0 = D(2022, 10, 10), D(2022, 12, 5)   # 7 pre weeks to 2022-11-21; 7 post weeks to 2023-01-16 (release week excluded)
def change(t, shift_days):
    pre = [lnq(t, pre0 + dt.timedelta(7 * k) - dt.timedelta(shift_days)) for k in range(7)]
    post = [lnq(t, post0 + dt.timedelta(7 * k) - dt.timedelta(shift_days)) for k in range(7)]
    return st.mean(post) - st.mean(pre)
rows = {}
for l in open("results_v2.jsonl"):
    x = json.loads(l); rows.setdefault((x["qid"], x["tag"], x["model"]), x)
def acc(model):
    d = collections.defaultdict(list)
    for (q, t, m), x in rows.items():
        if m == model and x["correct"] is not None: d[t].append(x["correct"])
    return {t: (st.mean(v), len(v)) for t, v in d.items() if len(v) >= 15}
A, Z = acc("gpt-3.5"), acc("llama-3.1-8b")
tags = [t for t in panel if t in A and t in Z]
print("tags with >=15 judged questions for both models:", len(tags))
shifts = (364, 728, 1092)
y22 = {t: change(t, 0) for t in tags}
plc = {k: {t: change(t, k) for t in tags} for k in shifts}
y = np.array([y22[t] - st.mean(plc[k][t] for k in shifts) for t in tags])
a = np.array([A[t][0] for t in tags]); z = np.array([Z[t][0] for t in tags])
print("mean seasonal-adjusted change in ln(1+n): %.3f  (SD across tags %.3f)" % (y.mean(), y.std()))
print("Acc gpt-3.5: mean %.3f SD %.3f | Acc llama-3.1-8b: mean %.3f SD %.3f | corr(A,Z) = %.2f" % (a.mean(), a.std(), z.mean(), z.std(), np.corrcoef(a, z)[0, 1]))
def ols(y, X):
    X1 = np.column_stack([np.ones(len(y)), X]); b = np.linalg.lstsq(X1, y, rcond=None)[0]; e = y - X1 @ b
    V = np.linalg.inv(X1.T @ X1) @ (X1.T * e**2) @ X1 @ np.linalg.inv(X1.T @ X1) * len(y) / (len(y) - X1.shape[1])   # HC1
    return b, np.sqrt(np.diag(V)), 1 - e.var() / y.var()
sd = a.std()
b, se, r2 = ols(y, (a - a.mean()) / sd)
print("\nOLS  y ~ std(Acc_gpt3.5):  beta = %+.3f  (se %.3f, t %.2f, R2 %.2f)  -> per +1 SD of accuracy" % (b[1], se[1], b[1] / se[1], r2))
c = np.cov(y, z)[0, 1] / np.cov(a, z)[0, 1] * sd
print("IV   (instrument: Acc_llama-3.1-8b): beta = %+.3f per +1 SD of accuracy  (first-stage corr %.2f)" % (c, np.corrcoef(a, z)[0, 1]))
rng = np.random.default_rng(0); bs = []
for _ in range(2000):
    i = rng.integers(0, len(y), len(y)); aa, zz, yy = a[i], z[i], y[i]
    d = np.cov(aa, zz)[0, 1]
    if abs(d) > 1e-9: bs.append(np.cov(yy, zz)[0, 1] / d * aa.std())
print("IV bootstrap 95%% interval: [%+.3f, %+.3f]" % tuple(np.percentile(bs, [2.5, 97.5])))
print("\nPlacebo: same regression on prior-year changes (seasonal pattern should not depend on AI accuracy)")
for k in shifts:
    yp = np.array([plc[k][t] - st.mean(plc[j][t] for j in shifts if j != k) for t in tags])
    bp, sp, _ = ols(yp, (a - a.mean()) / sd); print("  year -%d: beta %+.3f (se %.3f, t %.2f)" % (k // 364, bp[1], sp[1], bp[1] / sp[1]))
json.dump({t: dict(y=float(v), acc35=A[t][0], accllama=Z[t][0]) for t, v in zip(tags, y)}, open("chatgpt_tag_table.json", "w"))
