"""Move rows of failed API calls (finish_reason 'error:...') out of a results file, so that they are queried again on resume and are not counted as parse failures.
The removed rows are appended to <file>_errors.jsonl (kept as a record). usage: python clean_errors.py results\\study1b.jsonl"""
import json, os, sys
from collections import Counter
path = sys.argv[1]; keep, err = [], []
for line in open(path, encoding="utf-8"):
    if not line.strip(): continue
    try: r = json.loads(line)
    except json.JSONDecodeError: continue
    (err if str(r.get("finish_reason", "")).startswith("error:") else keep).append(line.rstrip("\n"))
if err:
    base, ext = os.path.splitext(path)
    with open(base + "_errors.jsonl", "a", encoding="utf-8", newline="\n") as f: f.write("\n".join(err) + "\n")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f: f.write("\n".join(keep) + "\n")
    os.replace(tmp, path)
c = Counter(json.loads(l)["model_key"] + "/" + json.loads(l)["channel"] for l in err)
print(f"{len(err)} failed-call rows moved out of {path}; {len(keep)} rows kept." + (" By model/channel: " + str(dict(c)) if err else " Nothing to clean."))
