"""Table 8 (Section 4.5): old vs recent accuracy and difference-in-gaps vs the GPT-3.5 control; tag-level correlation."""
import json, math, statistics as st, collections
d = {}
for f in ("results_windows.jsonl", "results_windows_control.jsonl"):
    for l in open(f):
        x = json.loads(l); d.setdefault((x["qid"], x["block"], x["model"]), x)
R = list(d.values())
def a(m, b, tag=None):
    s = [x["correct"] for x in R if x["model"] == m and x["block"] == b and x["correct"] is not None and (tag is None or x["tag"] == tag)]
    return (st.mean(s), len(s)) if s else (None, 0)
print("Panel A: own blocks")
for m, o, rc in (("gpt-3.5", "2019H1", "2021H1"), ("llama-3.1-8b", "2021H2", "2023H2")):
    (ao, no), (ar, nr) = a(m, o), a(m, rc); se = math.sqrt(ao * (1 - ao) / no + ar * (1 - ar) / nr)
    print("  %-14s %s->%s old %.1f%% recent %.1f%% gap %+.1f pp (SE %.1f; n=%d/%d)" % (m, o, rc, 100 * ao, 100 * ar, 100 * (ao - ar), 100 * se, no, nr))
print("Panel B: identical questions, 2022H1 vs 2024H1")
g = {}
for m in ("gpt-3.5@22-24", "llama-3.1-8b@22-24", "gpt-4.1", "gemma-3-27b", "llama-4-scout"):
    (ao, no), (ar, nr) = a(m, "2022H1"), a(m, "2024H1"); se = math.sqrt(ao * (1 - ao) / no + ar * (1 - ar) / nr); g[m] = (ao - ar, se)
    print("  %-20s old %.1f%% recent %.1f%% gap %+.1f pp (SE %.1f; n=%d/%d)" % (m, 100 * ao, 100 * ar, 100 * (ao - ar), 100 * se, no, nr))
for m in g:
    if m != "gpt-3.5@22-24":
        dd = g[m][0] - g["gpt-3.5@22-24"][0]; se = math.hypot(g[m][1], g["gpt-3.5@22-24"][1])
        print("  gap minus control, %-20s %+.1f pp (z %.1f)" % (m, 100 * dd, dd / se))
dec = json.load(open("checks_v3.json")); logdec = {t: math.log(v["v2025"] / v["v2022"]) for t, v in dec.items()}
def gap(models, t):
    o = [x["correct"] for x in R if x["model"] in models and x["tag"] == t and x["block"] == "2022H1" and x["correct"] is not None]
    r = [x["correct"] for x in R if x["model"] in models and x["tag"] == t and x["block"] == "2024H1" and x["correct"] is not None]
    return st.mean(o) - st.mean(r) if o and r else None
rows = []
for t in sorted({x["tag"] for x in R}):
    if t in logdec:
        gp, gc = gap(("gpt-4.1", "gemma-3-27b", "llama-4-scout"), t), gap(("gpt-3.5@22-24",), t)
        if gp is not None and gc is not None: rows.append((logdec[t], gp - gc))
x, y = [r[0] for r in rows], [r[1] for r in rows]
mx, my = st.mean(x), st.mean(y)
print("tag-level corr(log decline, post-model gap minus control gap), %d tags: %.2f" % (len(rows), sum((a_ - mx) * (b_ - my) for a_, b_ in zip(x, y)) / len(x) / (st.pstdev(x) * st.pstdev(y))))
