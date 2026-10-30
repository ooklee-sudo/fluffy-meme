import json, statistics as st, collections
r = json.load(open("results.json"))
models = list(dict.fromkeys(x["model"] for x in r)); tags = list(dict.fromkeys(x["tag"] for x in r))
acc = {(t, m): st.mean(x["correct"] for x in r if x["tag"] == t and x["model"] == m) for t in tags for m in models}
print("%-8s" % "tag", *["%-26s" % m for m in models], sep="")
for t in tags: print("%-8s" % t, *["%-26.2f" % acc[t, m] for m in models], sep="")
print("%-8s" % "mean", *["%-26.2f" % st.mean(acc[t, m] for t in tags) for m in models], sep="")
print("\nΔAcc (tag-level change between generations), cross-tag SD vs binomial noise SD (n=15)")
for a, b in zip(models, models[1:]):
    d = [acc[t, b] - acc[t, a] for t in tags]
    p = (st.mean(acc[t, a] for t in tags) + st.mean(acc[t, b] for t in tags)) / 2
    noise = (2 * p * (1 - p) / 15) ** .5
    print(f"{a[:14]:15s}->{b[:14]:15s} mean {st.mean(d):+.2f}  SD {st.stdev(d):.2f}  noise SD {noise:.2f}  range [{min(d):+.2f},{max(d):+.2f}]")
