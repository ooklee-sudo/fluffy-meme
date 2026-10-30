"""Section 5.3: language-level AI use in the Stack Overflow Developer Survey, 2023-2026, and its correlation with the decline in questions.
Usage: analysis_so_survey.py <dir with r2023.csv, r2024.csv, r2025.csv, r2026.csv>  (see README for download instructions; files are not redistributed)."""
import csv, json, math, collections, statistics as st, sys
csv.field_size_limit(10 ** 9); D = sys.argv[1]
dec = json.load(open("checks_v3.json")); logdec = {t: math.log(v["v2025"] / v["v2022"]) for t, v in dec.items()}
MAP = {"python": "Python", "javascript": "JavaScript", "java": "Java", "c++": "C++", "sql": "SQL", "php": "PHP", "c#": "C#", "r": "R", "typescript": "TypeScript", "swift": "Swift", "ruby": "Ruby"}
def split(x): return [s for s in (x or "").split(";") if s]
def load(y): return list(csv.DictReader(open(f"{D}/r{y}.csv", encoding="utf-8", errors="ignore")))
def share(rows, col, is_ai, min_n=300):
    tot = collections.Counter(); ai = collections.Counter()
    for x in rows:
        a = is_ai(x)
        if a is None: continue
        for l in split(x[col]): tot[l] += 1; ai[l] += a
    return {l: (ai[l] / tot[l], tot[l]) for l in tot if tot[l] >= min_n}
res = {2023: share(load(2023), "LanguageHaveWorkedWith", lambda x: None if x["AISelect"] == "NA" else int(x["AISelect"] == "Yes")),
       2024: share(load(2024), "LanguageHaveWorkedWith", lambda x: None if x["AISelect"] == "NA" else int(x["AISelect"] == "Yes")),
       2025: share(load(2025), "LanguageHaveWorkedWith", lambda x: None if x["AISelect"] == "NA" else int(x["AISelect"].startswith("Yes")))}
tot = collections.Counter(); ai = collections.Counter()
for x in load(2026):
    if x["LanguagesUsedAI"] in ("", "NA"): continue
    used = set(split(x["LanguagesUsedAI"]))
    for l in split(x["LanguagesHaveWorkedWith"]): tot[l] += 1; ai[l] += l in used
res[2026] = {l: (ai[l] / tot[l], tot[l]) for l in tot if tot[l] >= 300}
print("%-12s" % "language", *["%7d" % y for y in res], "  log decline 2022->2025")
rows = []
for t, l in MAP.items():
    if t in logdec:
        v = [res[y].get(l, (None,))[0] for y in res]; rows.append((t, v)); print("%-12s" % l, *["%6.1f%%" % (100 * x) if x is not None else "   n/a" for x in v], "   %.2f" % logdec[t])
def corr(a, b):
    ma, mb = st.mean(a), st.mean(b); return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / len(a) / (st.pstdev(a) * st.pstdev(b))
for i, y in enumerate(res):
    pts = [(v[i], logdec[t]) for t, v in rows if v[i] is not None]
    print(y, "corr(AI share, log decline), %d matched tags: %.2f" % (len(pts), corr([p[0] for p in pts], [p[1] for p in pts])))
json.dump({y: {l: list(v) for l, v in res[y].items()} for y in res}, open("ai_share_by_language.json", "w"))
