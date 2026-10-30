"""Table 6 and the half-year break (Section 4.4). Inputs: checks_v3.json (30 tags, annual counts), volume_v3.json (8 tags, half-year counts)."""
import json, math, statistics as st
def corr(a, b):
    ma, mb = st.mean(a), st.mean(b); return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / len(a) / (st.pstdev(a) * st.pstdev(b))
r = json.load(open("checks_v3.json")); T = list(r)
L = lambda x: math.log(max(x, 1))
rel = [1 - r[t]["v2025"] / r[t]["v2022"] for t in T]
lc = [math.log(r[t]["v2025"] / r[t]["v2022"]) for t in T]
pre = [math.log(r[t]["v2022"] / r[t]["v2020"]) for t in T]
pre_rel = [1 - r[t]["v2022"] / r[t]["v2020"] for t in T]   # relative decline 2020 -> 2022
pop = [L(r[t]["v2022"]) for t in T]; labs = [L(r[t]["v2022"] - r[t]["v2025"]) for t in T]
print("30 tags, annual counts 2022 (Jan-Nov) vs 2025")
print("relative decline: mean %.3f SD %.3f range [%.3f, %.3f]" % (st.mean(rel), st.pstdev(rel), min(rel), max(rel)))
print("log change: mean %.2f SD %.2f range [%.2f, %.2f]" % (st.mean(lc), st.pstdev(lc), min(lc), max(lc)))
print("log change 2020->2022: mean %.2f SD %.2f" % (st.mean(pre), st.pstdev(pre)))
print("corr(relative decline, log popularity) = %.3f" % corr(rel, pop))
print("corr(relative decline 2022->2025, relative decline 2020->2022) = %.3f" % corr(rel, pre_rel))
print("corr(log absolute decline, log popularity) = %.3f" % corr(labs, pop))
v = json.load(open("volume_v3.json"))
tags = sorted({k.split("|")[0] for k in v})
print("\nhalf-year log changes, 8 tags: average 2020H2-2022H2 (pre) vs 2022H2-2024H2 (post)")
for t in tags:
    g = lambda a, b: math.log(v[f"{t}|{b}"] / v[f"{t}|{a}"])
    pre_ = st.mean(g(a, b) for a, b in [("2020H2", "2021H1"), ("2021H1", "2021H2"), ("2021H2", "2022H1"), ("2022H1", "2022H2")])
    post = st.mean(g(a, b) for a, b in [("2022H2", "2023H1"), ("2023H1", "2023H2"), ("2023H2", "2024H1"), ("2024H1", "2024H2")])
    print("  %-11s pre %+.2f  post %+.2f" % (t, pre_, post))
