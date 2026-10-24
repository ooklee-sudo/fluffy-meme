"""Download HumanEval+ (EvalPlus) and keep tasks with the standard `inputs`/`results` test layout."""
import ast
import json
import pathlib
import urllib.request

URL = "https://huggingface.co/datasets/evalplus/humanevalplus/resolve/main/test.jsonl"
OUT = pathlib.Path(__file__).parent / "data"


def parse_tests(test_src):
    """Return (inputs, results, atol) from the check() body, or None for non-standard layouts."""
    tree = ast.parse(test_src)
    check = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "check")
    lit, atol = {}, 0
    for st in check.body:
        if isinstance(st, ast.Assign) and isinstance(st.targets[0], ast.Name) and st.targets[0].id in ("inputs", "results"):
            lit[st.targets[0].id] = ast.literal_eval(st.value)
        if isinstance(st, ast.For):
            src = ast.unparse(st)
            if "zip(inputs, results)" not in src:
                return None
            for sub in ast.walk(st):
                if isinstance(sub, ast.Call) and getattr(sub.func, "id", "") == "assertion":
                    atol = ast.literal_eval(sub.args[2])
    if set(lit) != {"inputs", "results"} or len(lit["inputs"]) != len(lit["results"]):
        return None
    return lit["inputs"], lit["results"], atol


def main():
    OUT.mkdir(exist_ok=True)
    raw = OUT / "humanevalplus.jsonl"
    if not raw.exists():
        urllib.request.urlretrieve(URL, raw)
    kept, skipped = [], []
    for line in raw.read_text().splitlines():
        r = json.loads(line)
        parsed = parse_tests(r["test"])
        if parsed is None:
            skipped.append(r["task_id"])
            continue
        inputs, results, atol = parsed
        kept.append({"task_id": r["task_id"], "prompt": r["prompt"], "entry_point": r["entry_point"],
                     "test_src": r["test"], "inputs": inputs, "results": results, "atol": atol})
    (OUT / "tasks.json").write_text(json.dumps(kept))
    print(f"kept {len(kept)} tasks, skipped {len(skipped)}: {skipped}")
    sizes = sorted(len(t["inputs"]) for t in kept)
    print("tests per task: min", sizes[0], "median", sizes[len(sizes) // 2], "max", sizes[-1])


if __name__ == "__main__":
    main()
