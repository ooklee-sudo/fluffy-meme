"""Section 5.3: scan the Anthropic Economic Index release 2026-06-26 (CC-BY-4.0) for technology-level request topics. Streams two large CSV files from Hugging Face."""
import csv, sys, re, collections, urllib.request, io
kw = re.compile(r"\b(python|javascript|typescript|java|sql|c\+\+|rust|react|pandas|git|html|css|php|swift|kotlin|golang|bash|programming|coding|software|code|debug|api|database)\b", re.I)
for f in ("claude_ai", "1p_api"):
    print("===", f)
    url = f"https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/main/release_2026_06_26/data/aei_{f}_2026-06-26.csv"
    r = csv.DictReader(io.TextIOWrapper(urllib.request.urlopen(url), encoding="utf-8")); n = 0; nodes = {}
    for row in r:
        n += 1
        if row["category_name"] == "request" and row["geo_level"] == "global" and row["metric_id"] == "pct" and kw.search(row["node_name"]): nodes[(row["hierarchy_level"], row["node_name"])] = row["value"]
    print("rows", n)
    for (lv, nm), v in sorted(nodes.items(), key=lambda x: (x[0][0], -float(x[1])))[:45]: print(" ", lv, nm[:90], "->", v)
