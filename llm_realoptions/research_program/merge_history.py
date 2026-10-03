"""Concatenate enriched history files into one (frame 'base' for the first frame, 'layer' for the layer-targeted frame); a repository-model pair appears once.
usage: python merge_history.py out.jsonl in1.jsonl in2.jsonl ..."""
import json, sys
out, seen, n = sys.argv[1], set(), 0
with open(out, "w") as f:
    for p in sys.argv[2:]:
        for l in open(p):
            if not l.strip(): continue
            r = json.loads(l); k = (r["repo"], r["model"])
            if k in seen: continue
            seen.add(k); r.setdefault("frame", "base"); f.write(json.dumps(r) + "\n"); n += 1
print(n, "pairs written to", out)
