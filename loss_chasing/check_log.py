"""Sanity check of a first-choice log: parse failures, refusals and action counts per turns-left condition.
usage: python check_log.py results\\w16_fable_t3.jsonl"""
import json, sys, collections
c = collections.defaultdict(collections.Counter)
for line in open(sys.argv[1]):
    try:
        r = json.loads(line)
    except json.JSONDecodeError:
        continue
    k = 12 - int(r["t"])
    c[k]["rows"] += 1
    c[k]["parse_fail"] += bool(r["parse_fail"])
    c[k]["refusal"] += r.get("reason") == "REFUSAL"
    c[k]["action:" + r["action"]] += 1
for k in sorted(c, reverse=True):
    print(k, "turns left:", dict(c[k]))
