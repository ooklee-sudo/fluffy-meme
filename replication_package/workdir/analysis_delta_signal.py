"""Section 4.3 (supporting numbers): tag-level signal in model differences, from stored grades in results_v2.jsonl.
Between-tag variance of the per-tag difference vs the sampling-noise variance implied by per-question paired variance."""
import json, collections, statistics as st, math
rows = {}
for l in open("results_v2.jsonl"):
    x = json.loads(l); rows.setdefault((x["qid"], x["tag"], x["model"]), x)
cost = collections.defaultdict(list)
for x in rows.values(): cost[x["model"]].append(x["cost"])
print("measured cost per question (answer + judge), USD:")
for m, v in cost.items(): print("  %-14s %.4f (n=%d)" % (m, st.mean(v), len(v)))
byq = collections.defaultdict(dict)
for (q, t, m), x in rows.items():
    if x["correct"] is not None: byq[(q, t)][m] = x["correct"]
def paired(m1, m2):
    d = collections.defaultdict(list)
    for (q, t), r in byq.items():
        if m1 in r and m2 in r: d[t].append(r[m1] - r[m2])
    return {t: v for t, v in d.items() if len(v) >= 8}
for m1, m2 in (("gpt-4o", "gpt-3.5"), ("gpt-4", "gpt-3.5"), ("gpt-4o", "gpt-4")):
    d = paired(m1, m2)
    if len(d) < 5: print(m1, m2, "too few tags"); continue
    n = st.mean(len(v) for v in d.values()); means = [st.mean(v) for v in d.values()]
    within = st.mean(st.pvariance(v) for v in d.values()); obs = st.pvariance(means); noise = within / n; sig = max(0, obs - noise)
    print("\n%s - %s: %d tags, ~%.0f q/tag, mean difference %+.3f" % (m1, m2, len(d), n, st.mean(means)))
    print("  between-tag variance %.4f; sampling-noise variance %.4f; signal variance %.4f; reliability %.2f" % (obs, noise, sig, sig / obs if obs else 0))
