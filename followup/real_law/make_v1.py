"""Step 3: replace the 'enacted' text by the text in force immediately BEFORE each amendment.
Input : real_amendments_raw.json (output of build_dataset.py) ; Output: real_amendments_v1.json
Before-dates are one day before the commencement dates given in the site's amendment notes."""
import sys, json, re, difflib
import lawlib
recs = json.load(open("real_amendments_raw.json"))
BEFORE = {"ERA_time_limit_3_to_6_months": "2026-09-30", "ERA_money_limits_2026": "2026-04-05", "CA2006_size_thresholds_2025": "2025-04-05"}
by = {}
for r in recs: by.setdefault((r["act"], r["section"], r["cluster"]), []).append(r)
out = []
for (act, n, cl), lst in by.items():
    d = BEFORE[cl]; a = lawlib.section(act, n, d); b = lawlib.section(act, n, "current")
    if not a or not b: continue
    wa, wb = a.split(), b.split(); sm = difflib.SequenceMatcher(None, wa, wb, autojunk=False); diffs = []
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op == "replace":
            o, nw = " ".join(wa[i1:i2]), " ".join(wb[j1:j2])
            if len(o.split()) <= 4 and len(nw.split()) <= 4 and re.search(r"\d|three|six|one", o + nw, re.I):
                diffs.append((o, nw, " ".join(wa[max(0, i1 - 16):i2 + 6]), " ".join(wb[max(0, j1 - 16):j2 + 6])))
    for r in lst:
        m = [x for x in diffs if x[1].strip(" .").startswith(r["new"])]
        if m:
            o, nw, ca, cb = m[0]; r2 = dict(r); r2["old_enacted"] = r["old"]; r2["old"] = o.strip(" ."); r2["before_date"] = d
            r2["text_before"] = ca; r2["text_after"] = cb; out.append(r2)
json.dump(out, open("real_amendments_v1.json", "w"), indent=1)
