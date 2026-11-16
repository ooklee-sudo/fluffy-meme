"""Extract MBPP+ tasks into the same schema as prep_tasks.py, by parsing (never executing)
the dataset's check(). The model prompt follows EvalPlus: the task description and the first
example assertion inside a docstring. Writes data/tasks_mbpp.json."""
import ast, json, re, sys
import pandas as pd

df = pd.read_parquet(sys.argv[1])
tasks, skipped = [], []
for _, r in df.iterrows():
    tid = f"Mbpp/{int(r['task_id'])}"
    m = re.match(r"\s*assert\s+(?:not\s+)?\(?\s*(?:math\.isclose\(|set\()?\s*([A-Za-z_]\w*)\s*\(", r["test_list"][0])
    if not m:
        skipped.append((tid, "no entry point")); continue
    entry = m.group(1)
    tree = ast.parse(r["test"])
    vals, atol, reason = {}, None, None
    if True:
        for st in tree.body:
            if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name) \
                    and st.targets[0].id in ("inputs", "results"):
                try:
                    vals[st.targets[0].id] = ast.literal_eval(st.value)
                except Exception:
                    reason = f"non-literal {st.targets[0].id}"
            if isinstance(st, ast.For):
                for sub in ast.walk(st):
                    if isinstance(sub, ast.Call) and getattr(sub.func, "id", None) == "assertion":
                        try:
                            atol = ast.literal_eval(sub.args[2]) if len(sub.args) == 3 else None
                        except Exception:
                            reason = "non-literal atol"
                    elif isinstance(sub, ast.Call) and getattr(sub.func, "id", None) not in (entry, "zip", "enumerate", "assertion"):
                        reason = reason or f"custom call {ast.unparse(sub.func)}"
        if reason is None and ("inputs" not in vals or "results" not in vals):
            reason = "missing inputs/results"
    if reason:
        skipped.append((tid, reason)); continue
    prompt = '"""\n' + r["prompt"].strip() + "\n" + r["test_list"][0].strip() + '\n"""\n'
    tasks.append(dict(task_id=tid, prompt=prompt, entry_point=entry, canonical_solution=r["code"],
                      inputs=vals["inputs"], results=vals["results"], atol=atol or 0,
                      test_imports=list(r["test_imports"])))
import pickle
pickle.dump(tasks, open(sys.argv[2], "wb"))   # pickle keeps tuples, sets and complex numbers intact
json.dump([{k: t[k] for k in ("task_id", "prompt", "entry_point")} for t in tasks],
          open(sys.argv[2].rsplit(".", 1)[0] + "_meta.json", "w"))
import collections
print("kept", len(tasks), "skipped", len(skipped), collections.Counter(s[1].split(" ")[0] for s in skipped))
import numpy as np
Ms = [len(t["inputs"]) for t in tasks]
print("inputs per task: median", np.median(Ms), "min", min(Ms), "max", max(Ms), "share >=50:", np.mean(np.array(Ms) >= 50))
