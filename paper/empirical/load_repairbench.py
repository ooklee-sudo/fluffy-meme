"""Extract per-bug (n, k) plausible-patch counts and token usage from RepairBench results."""
import json, os, glob, sys
ROOT = sys.argv[1] if len(sys.argv) > 1 else "/home/user/assert-kth/repairbench/results"
rows = []
for mdir in sorted(glob.glob(f"{ROOT}/*/")):
    model = os.path.basename(mdir.rstrip("/"))
    for ds in ["defects4j", "gitbugjava"]:
        for f in glob.glob(f"{mdir}{ds}/evaluation_*.jsonl"):
            for line in open(f):
                x = json.loads(line)
                ev, gen = x.get("evaluation"), x.get("generation")
                if not ev: continue
                ok = [bool(e) and str(e.get("test")) == "True" for e in ev]
                toks = []
                if isinstance(gen, list):
                    for g in gen:
                        u = (g or {}).get("usage") or {}
                        toks.append((u.get("prompt_tokens") or 0, u.get("completion_tokens") or 0))
                rows.append(dict(model=model, dataset=ds, bug=x["identifier"], n=len(ok), k=sum(ok),
                                 prompt_tok=sum(t[0] for t in toks) / max(len(toks), 1),
                                 comp_tok=sum(t[1] for t in toks) / max(len(toks), 1)))
json.dump(rows, open("bug_counts.json", "w"))
print(len(rows), "bug-model records;", len({r['model'] for r in rows}), "models")
from collections import Counter
print(Counter(r['n'] for r in rows).most_common(6))
