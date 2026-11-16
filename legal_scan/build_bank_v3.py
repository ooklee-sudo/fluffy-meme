import json, re, random, sys, collections
sys.path.insert(0, ".")
import scan
RP = "/tmp/claude-0/-home-user-fluffy-meme/6d046680-2797-598c-a7db-54c51fe25fec/scratchpad/zen/x/replication_package/real_law/"
v2 = json.load(open(RP + "real_fact_bank_v2.json"))
rows = json.load(open("cands_clean.json"))
def loc_of(i):
    m = re.fullmatch(r"section-(.+)", i)
    if m: return f"section {m.group(1)}", m.group(1)
    m = re.fullmatch(r"schedule-(\w+)-paragraph-(.+)", i)
    return f"Schedule {m.group(1)}, paragraph {m.group(2)}", f"Sch{m.group(1)}-{m.group(2)}"
def clean(v): return v.strip().strip(".,;:").strip()
def nm(v): return re.sub(r"[\s,£%]", "", v.lower())
UNIT = {"million", "billion", "thousand"}
have = {(f["act_name"], str(f["section"]), f["old"].strip(), f["new"].strip()) for f in v2 if f["kind"] == "changed"}
new_changed, dropped = [], collections.Counter()
seen = set()
for r in rows:
    o, n = clean(r["old"]), clean(r["new"])
    post = r["post"].split()
    if post and post[0].strip(".,;") in UNIT: o += " " + post[0].strip(".,;"); n += " " + post[0].strip(".,;")
    if "per cent" in r["post"][:12] and ("%" not in o): dropped["percent-format"] += 1; continue
    loc, sec = loc_of(r["id"])
    if (r["act_name"], sec, o, n) in have or (r["act_name"], sec.replace("section ", ""), o, n) in have: dropped["already in v2"] += 1; continue
    if r["act_name"] == "Employment Rights Act 1996" and sec.isdigit() and int(sec) <= 235 and ("three", "six") == (o, n): dropped["ERA 3->6 in v2"] += 1; continue
    ctx = r["ctx"]
    if nm(o) in nm(ctx) or nm(n) in nm(ctx): dropped["value in own context"] += 1; continue
    if len(ctx.split()) < 8: dropped["short ctx"] += 1; continue
    if o.startswith("£70,000"): dropped["odd"] += 1; continue
    key = (r["act_name"], sec, ctx[-60:])
    if key in seen: dropped["dup ctx"] += 1; continue
    seen.add(key)
    new_changed.append({"act": r["act"], "act_name": r["act_name"], "loc": loc, "section": sec, "title": re.sub(r"\s+", " ", r["title"]).strip(), "ctx": " ".join(ctx.split()[-16:]), "old": " " + o, "new": " " + n})
print("new changed", len(new_changed), dict(dropped))
# clusters: A = amended provision (siblings share wording / value), C = documented numeric relation (dependents)
CAT = collections.Counter((f["act_name"][:25]) for f in new_changed); print(CAT)
json.dump(new_changed, open("new_changed_pre.json", "w"), indent=1)

# ---- dependents with a numeric relation that holds before and after: UEL = personal allowance + basic rate limit (12,500+37,500=50,000; 12,570+37,700=50,270)
def is_dep(f):
    return (f["act_name"].startswith(("Social Security", "Pensions Act 2008")) and f["old"].strip() == "£50,000" and f["new"].strip() == "£50,270") or \
           (f["act_name"].startswith("Pensions Act 2008") and f["new"].strip() == "£50,270")
def is_base(f):
    return (f["act_name"] == "Income Tax Act 2007" and f["section"] == "35" and f["new"].strip() == "£12,570") or \
           (f["act_name"] == "Income Tax Act 2007" and f["section"] == "10" and f["new"].strip() == "£37,700")
facts = list(v2)
k = collections.Counter()
for f in new_changed:
    cl, role = "A", "base"
    if is_dep(f): cl, role = "C", "dependent"
    elif is_base(f): cl, role = "C", "base"
    f2 = dict(f); f2.update(kind="changed", cluster=cl, role=role, id=f"N-{len(facts)}", source_url=f"https://www.legislation.gov.uk/{f['act']}")
    facts.append(f2); k[(cl, role)] += 1
print("new changed by cluster/role", dict(k))
# ---- controls: numeric period phrases unchanged between 2021-01-01 and the current text, in sections without any change
NUMS = r"(one|two|three|four|five|six|seven|eight|nine|ten|twelve|fourteen|twenty-eight|\d+)"
PAT = re.compile(r"\b" + NUMS + r"\s+(days?|weeks?|months?|years?)\b")
changed_secs = {(f["act_name"], f["section"]) for f in facts if f["kind"] == "changed"}
v2_ctl_ctx = {f["ctx"][-50:] for f in v2 if f["kind"] == "control"}
pool = []
for act, name in scan.ACTS.items():
    fc, fo = scan.get(act, ""), scan.get(act, scan.D0)
    if not fc or not fo: continue
    A, B = scan.sections(fo), scan.sections(fc)
    for i, (t, b) in B.items():
        if i not in A or A[i][1] != b: continue
        loc, sec = loc_of(i)
        if (name, sec) in changed_secs: continue
        for mm in PAT.finditer(b):
            pre = b[:mm.start()].split()
            if len(pre) < 10: continue
            ctx = " ".join(pre[-16:])
            if ctx.count("“") != ctx.count("”") or ctx.count("(") != ctx.count(")") and ctx.rstrip().endswith("("): continue
            if mm.group(1).lower() in ctx.lower().split(): continue
            if ctx[-50:] in v2_ctl_ctx: continue
            pool.append({"act": act, "act_name": name, "loc": loc, "section": sec, "title": re.sub(r"\s+", " ", t).strip(), "ctx": ctx, "old": " " + mm.group(1), "unit": mm.group(2)})
random.Random(0).shuffle(pool)
per = collections.Counter(); seen = set(); ctl = []
for p in pool:
    if per[p["act_name"]] >= 14: continue
    key = (p["act_name"], p["section"]); 
    if key in seen: continue
    seen.add(key); per[p["act_name"]] += 1; ctl.append(p)
    if len(ctl) >= 100: break
for j, p in enumerate(ctl):
    p.update(kind="control", cluster="K", role="control", id=f"NK-{j}", new=p["old"])
    facts.append(p)
print("controls added", len(ctl), dict(per), "total facts", len(facts), collections.Counter((f["kind"], f["cluster"], f["role"]) for f in facts))
json.dump(facts, open("real_fact_bank_v3_draft.json", "w"), indent=1)
for p in ctl: print("K", p["act_name"][:10], p["loc"], "|", p["ctx"][-80:], "||", p["old"], p["unit"])
