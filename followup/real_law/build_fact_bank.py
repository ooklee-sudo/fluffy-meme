"""Build the fact bank used by lm_reallaw_gpu.py from real_amendments_v1.json plus unchanged control provisions.
Run from a directory where lawlib.py can reach legislation.gov.uk (or has a cache). Output: real_fact_bank.json"""
import json, re, random, sys
import lawlib
recs = json.load(open("real_amendments_v1.json"))
facts = []
def cut(text, old):
    w = text.split(); key = old.split()[0].strip(".,;")
    ks = [k for k, x in enumerate(w) if x.strip(".,;") == key]
    ks2 = [k for k in ks if k >= min(12, len(w) - 1)] or ks
    if not ks2: return None
    k = ks2[0]; nxt = w[k + 1].strip(".,;") if k + 1 < len(w) else ""
    return " ".join(w[max(0, k - 16):k]), k, nxt
for r in recs:
    c = cut(r["text_before"], r["old"]);
    if not c: continue
    ctx, k, nxt = c; unit = " million" if nxt == "million" else ""
    role = "dependent" if re.search(r"net \(or\s*$", ctx) else "base"
    cl = {"ERA_time_limit_3_to_6_months": "A", "ERA_money_limits_2026": "B", "CA2006_size_thresholds_2025": "C"}[r["cluster"]]
    facts.append({"id": f"{cl}-{r['act_name'][:3]}{r['section']}-{len(facts)}", "kind": "changed", "cluster": cl, "role": role,
                  "act_name": r["act_name"], "section": r["section"], "title": r["title"], "ctx": ctx,
                  "old": " " + r["old"].strip() + unit, "new": " " + r["new"].strip() + unit, "source_url": r["source_url"]})
# controls: provisions whose text is identical in the enacted and the current version
NUMS = r"(one|two|three|four|five|six|seven|eight|nine|ten|twelve|fourteen|twenty-eight|\d+)"
PAT = re.compile(r"\b" + NUMS + r"\s+(days?|weeks?|months?|years?)\b")
ACTS = {"ukpga/1996/18": ("Employment Rights Act 1996", range(1, 236)), "ukpga/2006/46": ("Companies Act 2006", range(380, 481))}
changed_secs = {(f["act_name"], f["section"]) for f in facts}
pool = []
def norm(t): return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9£\.\- ]", "", t.lower().replace("’", "").replace("'", ""))).strip()
for act, (name, rng) in ACTS.items():
    for n in rng:
        a, b = lawlib.section(act, n, "enacted"), lawlib.section(act, n, "current")
        if not a or not b or (name, n) in changed_secs: continue
        na = norm(a)
        xml = lawlib.get(f"https://www.legislation.gov.uk/{act}/section/{n}/data.xml") or ""
        m = re.search(r"<Title>(.*?)</Title>", xml, re.S); title = re.sub(r"<[^>]+>|\s+", " ", m.group(1)).strip() if m else ""
        for mm in PAT.finditer(b):
            pre = b[:mm.start()].split()
            if len(pre) < 10: continue
            key8 = norm(" ".join(pre[-8:]) + " " + mm.group(1) + " " + mm.group(2))   # same phrase, same number, in the enacted text
            if key8 not in na: continue
            pool.append({"act_name": name, "section": n, "title": title, "ctx": " ".join(pre[-16:]), "old": " " + mm.group(1), "unit": mm.group(2)})
random.Random(0).shuffle(pool)
seen = set(); k = 0
for p in pool:
    key = (p["act_name"], p["section"], p["ctx"])
    if key in seen: continue
    seen.add(key); k += 1
    facts.append({"id": f"K-{k}", "kind": "control", "cluster": "K", "role": "control", "act_name": p["act_name"], "section": p["section"], "title": p["title"],
                  "ctx": p["ctx"], "old": p["old"], "new": p["old"], "unit": p["unit"]})
    if k >= 90: break
json.dump(facts, open("real_fact_bank.json", "w"), indent=1)
import collections; print(collections.Counter((f["cluster"], f["role"]) for f in facts))
for f in facts[:3] + [x for x in facts if x["cluster"] == "C"][:2] + [x for x in facts if x["kind"] == "control"][:3]:
    print(f"[{f['id']}] {f['act_name']}, s.{f['section']} ({f['title']}): ...{f['ctx'][-70:]} || {f['old']!r} -> {f['new']!r}")
