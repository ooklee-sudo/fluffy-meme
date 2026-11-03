import sys, re, json
sys.path.insert(0, ".")
import lawlib, xml.etree.ElementTree as ET
ACTS = {"ukpga/1996/18": "Employment Rights Act 1996", "ukpga/2006/46": "Companies Act 2006"}
def raw(act, n): return lawlib.get(f"https://www.legislation.gov.uk/{act}/section/{n}/data.xml")
def title_of(xml, n):
    m = re.search(r"<Title>(.*?)</Title>", xml, re.S); return re.sub(r"<[^>]+>|\s+", " ", m.group(1)).strip() if m else ""
def comments(xml):
    out = []
    for m in re.finditer(r'<Commentary [^>]*Type="([FCIEMXP])"[^>]*>(.*?)</Commentary>', xml, re.S):
        t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(2))).strip(); out.append((m.group(1), t))
    return out
rows = json.load(open("period_changes.json"))
keep = []
for r in rows:
    a, n = r["act"], r["section"]; o, nw = r["old"].strip("."), r["new"].strip(" .")
    if a == "ukpga/1996/18" and n in (11, 23, 34, 48, 51, 54, 57, 60, 63, 70, 111, 188) and (o, nw) == ("three", "six"): kind, cl = "time_limit", "ERA_time_limit_3_to_6_months"
    elif a == "ukpga/1996/18" and n in (31, 186, 227) and "£" in o: kind, cl = "amount", "ERA_money_limits_2026"
    elif a == "ukpga/2006/46" and "£" in o: kind, cl = "threshold", "CA2006_size_thresholds_2025"
    else: continue
    x = raw(a, n); cm = comments(x)
    want = [t for k, t in cm if k == "F" and re.search(r"\b(2025|2026)\b", t) and re.search(r"substitut|Sum", t, re.I)]
    keep.append({"act": a, "act_name": ACTS[a], "section": n, "title": title_of(x, n), "cluster": cl, "kind": kind,
                 "old": o, "new": nw, "text_before": r["ctx_old"], "text_after": r["ctx_new"],
                 "source_url": f"https://www.legislation.gov.uk/{a}/section/{n}", "amending_notes": want[:3]})
json.dump(keep, open("real_amendments_raw.json", "w"), indent=1)
print(len(keep), "records")
for k in keep: print(f"{k['act_name'][:10]} s.{k['section']:<4} [{k['cluster'][:14]}] '{k['old']}'->'{k['new']}' | {k['title'][:60]} | notes: {(k['amending_notes'][:1] or ['NONE'])[0][:110]}")
