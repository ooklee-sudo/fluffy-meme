"""Instrument check: scripted honest and escalating agents (Section 4.5).

  python known_groups.py <scripted_coding.jsonl> <scripted_ops.jsonl>
"""
import json
import sys

for path in sys.argv[1:]:
    rows = [json.loads(l) for l in open(path)]
    print(f"## {path}\n")
    print("| Agent | Episodes | Gaming (%) | Honest exit (%) |\n| --- | --- | --- | --- |")
    for agent in ["scripted:honest", "scripted:escalating"]:
        r = [x for x in rows if x["model"] == agent]
        print(f"| {agent} | {len(r)} | {100 * sum(x['unsafe'] for x in r) / len(r):.0f} | "
              f"{100 * sum(x['honest_exit'] for x in r) / len(r):.0f} |")
    print()
