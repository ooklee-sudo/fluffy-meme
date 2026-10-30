"""Section 4.2 (last paragraph): Llama 2 7B/13B chat results (results_llama2.jsonl); tag-level signal and 13B-7B correlation."""
import json, collections, statistics as st, math, random
d = {}
for l in open("results_llama2.jsonl"):
    x = json.loads(l); d.setdefault((x["qid"], x["model"]), x)
R = list(d.values())
tags = list(dict.fromkeys(q["tag"] for q in json.load(open("questions_v2.json"))))
acc = {}
for m in ("llama2-13b", "llama2-7b"):
    s = [x["correct"] for x in R if x["model"] == m and x["correct"] is not None]
    print("%s: %d graded, accuracy %.3f" % (m, len(s), st.mean(s)))
    acc[m] = {}
    for t in tags:
        v = [x["correct"] for x in R if x["model"] == m and x["tag"] == t and x["correct"] is not None]
        if len(v) >= 15: acc[m][t] = (st.mean(v), len(v))
    a = [v[0] for v in acc[m].values()]; n = st.mean(v[1] for v in acc[m].values()); p = st.mean(a); noise = (p * (1 - p) / n) ** .5
    print("  tag-level SD %.3f, noise SD %.3f, signal SD %.3f, min %.2f, max %.2f" % (st.pstdev(a), noise, math.sqrt(max(0, st.pvariance(a) - noise ** 2)), min(a), max(a)))
def corr(a, b):
    ma, mb = st.mean(a), st.mean(b); return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / len(a) / (st.pstdev(a) * st.pstdev(b))
ts = [t for t in tags if t in acc["llama2-13b"] and t in acc["llama2-7b"]]
a, b = [acc["llama2-13b"][t][0] for t in ts], [acc["llama2-7b"][t][0] for t in ts]
obs = corr(a, b); random.seed(0); null = []
for _ in range(2000):
    s = b[:]; random.shuffle(s); null.append(corr(a, s))
print("corr of tag accuracy 13B vs 7B: %.2f over %d tags; permutation p (one-sided) %.3f" % (obs, len(ts), sum(c >= obs for c in null) / 2000))
