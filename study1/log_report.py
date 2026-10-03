"""Row counts of a results file by model, system variant, stance set and channel, with failed-call rows, duplicate queries and parse failures.
usage: python log_report.py results\\study1b.jsonl   (expected: 240 rows per model for the registered run; 120 for the aligned channel)"""
import json, sys
from collections import Counter, defaultdict
rows = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.strip().startswith("{")]
key = lambda r: (r["model_key"], r.get("system_variant", 0), r.get("social_set", "A"), r["channel"])
n, err, pf = Counter(), Counter(), Counter(); seen = Counter()
for r in rows:
    k = key(r); n[k] += 1; seen[(k, r["stem_id"])] += 1
    if str(r.get("finish_reason", "")).startswith("error:"): err[k] += 1
    elif r.get("parse_fail"): pf[k] += 1
dup = Counter(); [dup.update([k]) for (k, s), c in seen.items() if c > 1]
print(f"{len(rows)} rows; {sum(err.values())} failed-call rows; {sum(dup.values())} (model, variant, set, channel) cells with duplicated stems")
print(f"{'model':16s} {'variant':>7s} {'set':>3s} {'channel':10s} {'rows':>5s} {'failed':>6s} {'dupl':>5s} {'parse_fail':>10s}")
for k in sorted(n):
    flag = "" if (n[k] - err[k] - dup[k]) in (120, 240) else "   <-- incomplete or duplicated"
    print(f"{k[0]:16s} {k[1]:>7} {k[2]:>3} {k[3]:10s} {n[k]:5d} {err[k]:6d} {dup[k]:5d} {pf[k]:10d}{flag}")
