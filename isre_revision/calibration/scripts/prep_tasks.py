"""Extract inputs, expected results and tolerance from HumanEval+ test code by parsing
(never executing) the dataset's check() function. Writes data/tasks.json."""
import ast, json, sys
import pandas as pd

src, out = sys.argv[1], sys.argv[2]
df = pd.read_parquet(src)
tasks, skipped = [], []
for _, r in df.iterrows():
    tree = ast.parse(r["test"])
    check = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "check"), None)
    vals, atol = {}, None
    reason = None
    if check is None:
        reason = "no check()"
    else:
        for st in check.body:
            if isinstance(st, ast.Assign) and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name) \
                    and st.targets[0].id in ("inputs", "results"):
                try:
                    vals[st.targets[0].id] = ast.literal_eval(st.value)
                except Exception:
                    reason = f"non-literal {st.targets[0].id}"
            if isinstance(st, ast.For):
                for sub in ast.walk(st):
                    if isinstance(sub, ast.Call) and getattr(sub.func, "id", None) == "assertion":
                        if len(sub.args) == 3:
                            try:
                                atol = ast.literal_eval(sub.args[2])
                            except Exception:
                                reason = "non-literal atol"
                        else:
                            reason = "non-standard assertion"
                    if isinstance(sub, ast.Call) and getattr(sub.func, "id", None) != "assertion" \
                            and getattr(sub.func, "id", None) not in ("candidate", "zip", "enumerate"):
                        reason = reason or f"custom call {ast.unparse(sub.func)}"
        if reason is None and ("inputs" not in vals or "results" not in vals):
            reason = "missing inputs/results"
    if reason:
        skipped.append((r["task_id"], reason))
        continue
    tasks.append(dict(task_id=r["task_id"], prompt=r["prompt"], entry_point=r["entry_point"],
                      canonical_solution=r["canonical_solution"], inputs=vals["inputs"],
                      results=vals["results"], atol=atol if atol is not None else 0))
json.dump(tasks, open(out, "w"))
print("kept", len(tasks), "skipped", len(skipped))
for s in skipped:
    print("  ", s)
