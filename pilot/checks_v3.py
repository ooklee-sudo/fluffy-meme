"""Two checks for the retraining-loop design, top-30 tags.
(1) # of post-2025 questions with accepted answers per tag (API 'total').
(2) treatment variation: absolute vs relative decline across tags, and correlation with popularity."""
import json, time, urllib.parse, urllib.request, gzip, datetime as dt, math, statistics as st

def get(path, **p):
    p["site"] = "stackoverflow"
    url = "https://api.stackexchange.com/2.3/" + path + "?" + urllib.parse.urlencode(p)
    for i in range(5):
        try:
            data = urllib.request.urlopen(url, timeout=60).read()
            try: data = gzip.decompress(data)
            except OSError: pass
            d = json.loads(data)
            if "backoff" in d: time.sleep(d["backoff"])
            return d
        except Exception as e:
            err = e; time.sleep(2 ** i)
    raise SystemExit(f"API failed: {err}")

ts = lambda y, m=1: int(dt.datetime(y, m, 1, tzinfo=dt.timezone.utc).timestamp())
tags = [t["name"] for t in get("tags", sort="popular", order="desc", pagesize=30)["items"]]
rows = {}
for tag in tags:
    c = lambda a, b, **k: get("search/advanced", tagged=tag, fromdate=a, todate=b, filter="total", **k)["total"]
    rows[tag] = dict(v2020=c(ts(2020), ts(2021)), v2022=c(ts(2022), ts(2022, 12)), v2025=c(ts(2025), ts(2026)),
                     acc_post2025=c(ts(2025), ts(2026, 11), accepted="True"))
    print(tag, rows[tag], flush=True)
json.dump(rows, open("checks_v3.json", "w"))

print("\n(1) post-2025 accepted-answer questions per tag")
a = sorted(r["acc_post2025"] for r in rows.values())
print("min %d  median %d  max %d | tags >=100: %d/30, >=300: %d/30, >=1000: %d/30" %
      (a[0], st.median(a), a[-1], sum(x >= 100 for x in a), sum(x >= 300 for x in a), sum(x >= 1000 for x in a)))

print("\n(2) treatment variation, 2022 -> 2025 (annual counts)")
L = lambda x: math.log(max(x, 1))
rel = {t: 1 - r["v2025"] / r["v2022"] for t, r in rows.items()}
absd = {t: r["v2022"] - r["v2025"] for t, r in rows.items()}
pre = {t: 1 - r["v2022"] / r["v2020"] for t, r in rows.items()}
def corr(x, y):
    mx, my = st.mean(x), st.mean(y); sx, sy = st.pstdev(x), st.pstdev(y)
    return sum((a - mx) * (b - my) for a, b in zip(x, y)) / len(x) / (sx * sy)
T = list(rows)
pop = [L(rows[t]["v2022"]) for t in T]
print("relative decline: mean %.3f  SD %.3f  range [%.3f, %.3f]" % (st.mean(rel.values()), st.pstdev(rel.values()), min(rel.values()), max(rel.values())))
print("log(absolute decline): SD %.2f" % st.pstdev([L(absd[t]) for t in T]))
print("corr(log abs decline, log popularity 2022)  = %.3f" % corr([L(absd[t]) for t in T], pop))
print("corr(relative decline, log popularity 2022) = %.3f" % corr([rel[t] for t in T], pop))
print("corr(relative decline, pre-ChatGPT decline 2020->2022) = %.3f" % corr([rel[t] for t in T], [pre[t] for t in T]))
# variation left in log abs decline after removing popularity (OLS residual SD)
y = [L(absd[t]) for t in T]; mx, my = st.mean(pop), st.mean(y)
b = sum((p - mx) * (v - my) for p, v in zip(pop, y)) / sum((p - mx) ** 2 for p in pop)
res = [v - (my + b * (p - mx)) for p, v in zip(pop, y)]
print("log abs decline: slope on log popularity %.2f, residual SD %.2f (vs raw SD %.2f)" % (b, st.pstdev(res), st.pstdev(y)))
