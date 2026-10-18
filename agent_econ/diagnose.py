"""Diagnostics for the pilot: parse failures and how many tasks were actually allocated each day."""
import collections, glob, json, os

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")

print("=== parse failures ===")
pf = os.path.join(RES, "parse_failures.jsonl")
if os.path.exists(pf):
    rows = [json.loads(l) for l in open(pf, encoding="utf-8")]
    c = collections.Counter((r["model"], r["stage"], r["finish"]) for r in rows)
    for k, v in c.most_common():
        print(v, k)
    for r in rows[:3]:
        print("sample:", r["model"], r["stage"], "tokens", r["completion_tokens"], repr(r["text"][:200]))
else:
    print("no parse_failures.jsonl (no failures)")

print("\n=== tasks allocated per day (= tasks_per_day when fully allocated) ===")
print(f"{'world':40s}{'avg_win':>8s}{'days<3':>8s}{'tasks per agent':>26s}")
for f in sorted(glob.glob(os.path.join(RES, "pilot*_*.events.jsonl"))):
    ev = [json.loads(l) for l in open(f, encoding="utf-8")]
    al = [e for e in ev if e["type"] == "allocation"]
    if not al:
        continue
    n = [len(e["winners"]) for e in al]
    per = collections.Counter(w for e in al for w in e["winners"])
    name = os.path.basename(f).replace(".events.jsonl", "")
    print(f"{name:40s}{sum(n)/len(n):8.2f}{sum(1 for x in n if x < min(3, max(n))):8d}   {[per.get(i, 0) for i in range(6)]}")
