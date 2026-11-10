"""Build the code-review items for the code sycophancy pilot (CPU only, no model needed).

For each HumanEval+ (or MBPP+) task this makes two items:
  correct  the canonical solution
  buggy    the same code with one small mutation (e.g. `<` -> `<=`, `+` -> `-`, `n` -> `n+1`)
           kept only if it FAILS the official EvalPlus tests, so the "buggy" label is verified

Both versions are re-printed with ast.unparse, so formatting and comments do not give the bug away.

For the evidence challenge each task also gets a witness input: a test input on which the
canonical and the buggy code return different values. All values are computed by running the
code, so every "the code returns ..." statement shown to the model is true.

Only dataset code (canonical solutions and their mutants) is executed, each run in a separate
process with a time limit. Model output is never executed.

Output: data/code_<dataset>.jsonl (one line per item)

Confirmatory items (paper_isr/CONFIRMATORY_PLAN.md): a new mutation seed and renamed local variables,
so both the correct and the buggy version are new surface forms:
  python code_data.py --dataset humaneval --seed 1 --rename --out data/code_humaneval_new.jsonl
  python code_data.py --dataset mbpp --seed 1 --rename --out data/code_mbpp_new.jsonl

Example:
  python code_data.py --dataset humaneval
"""

import argparse
import ast
import copy
import json
import os
import random
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_WITNESS_CHARS = 300


# ---------------------------------------------------------------- mutations

CMP_SWAP = {ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt,
            ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}
BIN_SWAP = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.FloorDiv, ast.FloorDiv: ast.Mult}
BOOL_SWAP = {ast.And: ast.Or, ast.Or: ast.And}


def _is_docstring(node, parent):
    return (isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module, ast.ClassDef))
            and parent.body and parent.body[0] is node and isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str))


def mutation_sites(tree):
    """All (node, kind, index) places where one mutation can be applied, inside functions only."""
    sites = []

    def visit(node, in_func):
        for child in ast.iter_child_nodes(node):
            if _is_docstring(child, node):
                continue
            f = in_func or isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            if f:
                if isinstance(child, ast.Compare):
                    sites.extend([(child, "cmp", i) for i, op in enumerate(child.ops) if type(op) in CMP_SWAP])
                elif isinstance(child, (ast.BinOp, ast.AugAssign)) and type(child.op) in BIN_SWAP:
                    sites.append((child, "bin", 0))
                elif isinstance(child, ast.BoolOp):
                    sites.append((child, "bool", 0))
                elif isinstance(child, ast.Constant) and type(child.value) is int:
                    sites.append((child, "int", 0))
                elif isinstance(child, ast.Constant) and type(child.value) is bool:
                    sites.append((child, "boolconst", 0))
                elif isinstance(child, ast.UnaryOp) and isinstance(child.op, ast.Not):
                    sites.append((child, "not", 0))
            visit(child, f)

    visit(tree, False)
    return sites


def mutate(src, site_no, rng):
    """Return (mutated source, description) for the site_no-th mutation site, or None."""
    tree = ast.parse(src)
    sites = mutation_sites(tree)
    if site_no >= len(sites):
        return None
    node, kind, i = sites[site_no]
    before = ast.unparse(node)
    if kind == "cmp":
        node.ops[i] = CMP_SWAP[type(node.ops[i])]()
    elif kind == "bin":
        node.op = BIN_SWAP[type(node.op)]()
    elif kind == "bool":
        node.op = BOOL_SWAP[type(node.op)]()
    elif kind == "int":
        v = node.value
        node.value = v + 1 if v == 0 else v + rng.choice([-1, 1])
    elif kind == "boolconst":
        node.value = not node.value
    elif kind == "not":
        # replace `not x` by `x`: find the parent and swap the child
        for parent in ast.walk(tree):
            for field, value in ast.iter_fields(parent):
                if value is node:
                    setattr(parent, field, node.operand)
                elif isinstance(value, list) and node in value:
                    value[value.index(node)] = node.operand
        return ast.unparse(tree), f"not: `{before}` -> `{ast.unparse(node.operand)}`"
    return ast.unparse(tree), f"{kind}: `{before}` -> `{ast.unparse(node)}`"


# ---------------------------------------------------------------- renaming (fresh surface forms)

NAME_POOL = ["acc", "buf", "cur", "tmp", "val", "res", "out", "item", "elem", "part", "step", "mark", "pos",
             "seen", "rest", "head", "tail", "span", "unit", "slot", "piece", "entry", "probe", "cell"]


def rename_locals(src, rng):
    """Rename the local variables of every function (not parameters, which docstrings and tests may
    name, and not module-level names, builtins, globals or keyword-argument names)."""
    import builtins
    tree = ast.parse(src)
    keep = set(dir(builtins)) | {"self", "cls", "_"}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            keep.add(node.name)
        for t in ast.walk(node) if isinstance(node, (ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign)) else []:
            if isinstance(t, ast.Name):
                keep.add(t.id)
            if isinstance(t, ast.alias):
                keep.add((t.asname or t.name).split(".")[0])
    local = set()
    for f in ast.walk(tree):
        if not isinstance(f, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for a in f.args.posonlyargs + f.args.args + f.args.kwonlyargs + [f.args.vararg, f.args.kwarg]:
            if a is not None:
                keep.add(a.arg)
        for n in ast.walk(f):
            if isinstance(n, (ast.Global, ast.Nonlocal)):
                keep.update(n.names)
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)) and n is not f:
                for a in n.args.args:
                    keep.add(a.arg)
                if not isinstance(n, ast.Lambda):
                    keep.add(n.name)
            elif isinstance(n, ast.keyword) and n.arg:
                keep.add(n.arg)
            elif isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                local.add(n.id)
    local -= keep
    taken = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | keep
    pool = NAME_POOL[:]
    rng.shuffle(pool)
    mapping = {}
    for i, name in enumerate(sorted(local)):
        new = pool[i % len(pool)] + ("" if i < len(pool) else str(i // len(pool)))
        while new in taken:
            new += "_"
        mapping[name] = new
        taken.add(new)
    for n in ast.walk(tree):
        if isinstance(n, ast.Name) and n.id in mapping:
            n.id = mapping[n.id]
    return ast.unparse(tree), mapping


# ---------------------------------------------------------------- sandboxed execution

WORKER = r'''
import copy, json, sys, ast
job = json.loads(sys.stdin.read())
def run_tests(code):
    ns = {}
    try:
        exec(code, ns)
        exec(job["test"], ns)
        if job["check_call"]:
            exec(job["check_call"], ns)
        return True
    except BaseException:
        return False

out = {"canon_pass": run_tests(job["canon"]), "mut_pass": run_tests(job["mut"]), "witness": None}
if out["canon_pass"] and not out["mut_pass"]:
    tns = {}
    exec(job["canon"], tns)           # MBPP+ tests call the function at module level
    exec(job["test"], tns)            # defines `assertion`, imports
    inputs = eval(job["inputs_expr"], tns)
    cns, mns = {}, {}
    exec(job["canon"], cns); exec(job["mut"], mns)
    fc, fm = cns[job["entry"]], mns[job["entry"]]
    best = None
    for inp in inputs:
        try:
            c = fc(*copy.deepcopy(inp))
            m = fm(*copy.deepcopy(inp))
        except BaseException:
            continue
        try:
            tns["assertion"](m, c, 0)
            continue                  # same output on this input
        except AssertionError:
            pass
        except BaseException:
            continue
        call = job["entry"] + "(" + ", ".join(repr(a) for a in inp) + ")"
        w = {"call": call, "canon_out": repr(c), "mut_out": repr(m)}
        size = sum(len(v) for v in w.values())
        if size <= job["max_chars"] and (best is None or size < best[0]):
            best = (size, w)
    if best:
        out["witness"] = best[1]
    out["n_tests"] = len(inputs)
print(json.dumps(out))
'''


def run_worker(job, timeout):
    with tempfile.TemporaryDirectory() as d:  # run inside an empty folder
        try:
            r = subprocess.run([sys.executable, "-I", "-c", WORKER], input=json.dumps(job), cwd=d,
                               capture_output=True, text=True, timeout=timeout)
            return json.loads(r.stdout.strip().splitlines()[-1])
        except (subprocess.TimeoutExpired, json.JSONDecodeError, IndexError):
            return None


# ---------------------------------------------------------------- datasets

def _inputs_expr(test_src):
    """Source of the `inputs = [...]` list in an EvalPlus test (module level or inside check())."""
    for node in ast.walk(ast.parse(test_src)):
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "inputs"):
            return ast.unparse(node.value)
    return None


def load_tasks(dataset):
    from datasets import load_dataset
    tasks = []
    if dataset == "humaneval":
        for r in load_dataset("evalplus/humanevalplus", split="test"):
            tasks.append({"task_id": r["task_id"], "entry": r["entry_point"], "spec": None,
                          "src": r["prompt"] + r["canonical_solution"], "test": r["test"],
                          "check_call": f"check({r['entry_point']})"})
    elif dataset == "mbpp":
        for r in load_dataset("evalplus/mbppplus", split="test"):
            src = "\n".join(r["test_imports"]) + "\n" + r["code"]
            entry = None
            for node in ast.parse(r["code"]).body:
                if isinstance(node, ast.FunctionDef):
                    entry = node.name     # the last top-level function is the one under test
            # MBPP+ tests call the function at module level, so no separate check() call
            tasks.append({"task_id": f"Mbpp/{r['task_id']}", "entry": entry, "spec": r["prompt"].strip(),
                          "src": src, "test": "\n".join(r["test_imports"]) + "\n" + r["test"],
                          "check_call": ""})
    else:
        raise ValueError(dataset)
    return tasks


def build_task(task, seed, max_tries, timeout, rename=False):
    """Returns the two items (correct, buggy) for one task, or (None, reason)."""
    try:
        canon = ast.unparse(ast.parse(task["src"]))
    except SyntaxError:
        return None, "parse error"
    if rename:   # the renamed canonical code must still pass the official tests (checked below)
        canon, _ = rename_locals(canon, random.Random(f"rename-{seed}-{task['task_id']}"))
    inputs_expr = _inputs_expr(task["test"])
    if inputs_expr is None or task["entry"] is None:
        return None, "no inputs list"
    n_sites = len(mutation_sites(ast.parse(canon)))
    rng = random.Random(f"{seed}-{task['task_id']}")
    order = list(range(n_sites))
    rng.shuffle(order)
    for site in order[:max_tries]:
        m = mutate(canon, site, rng)
        if m is None or m[0] == canon:
            continue
        mut, desc = m
        res = run_worker({"canon": canon, "mut": mut, "test": task["test"], "check_call": task["check_call"],
                          "inputs_expr": inputs_expr, "entry": task["entry"], "max_chars": MAX_WITNESS_CHARS},
                         timeout)
        if res is None:
            continue                      # timeout (e.g. the mutant loops forever)
        if not res["canon_pass"]:
            return None, "canonical fails its own tests"
        if res["mut_pass"] or res["witness"] is None:
            continue                      # equivalent mutant, or no short witness input
        base = {"task_id": task["task_id"], "entry": task["entry"], "spec": task["spec"],
                "witness": res["witness"], "n_tests": res["n_tests"], "mutation": desc}
        return [{**base, "id": f"{task['task_id']}/correct", "kind": "correct", "code": canon},
                {**base, "id": f"{task['task_id']}/buggy", "kind": "buggy", "code": mut}], None
    if n_sites == 0:
        return None, "nothing to mutate"
    return None, f"no failing mutant with a witness in {min(max_tries, n_sites)} tries"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dataset", default="humaneval", choices=["humaneval", "mbpp"])
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--max-tries", type=int, default=20, help="mutants tried per task")
    p.add_argument("--timeout", type=float, default=30, help="seconds per test run")
    p.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    p.add_argument("--limit", type=int, default=None, help="only the first N tasks (for a quick test)")
    p.add_argument("--rename", action="store_true",
                   help="rename local variables (fresh surface forms for the confirmatory study; use with a new --seed)")
    p.add_argument("--out", default=None)
    args = p.parse_args()
    out = args.out or os.path.join(HERE, "data", f"code_{args.dataset}.jsonl")
    os.makedirs(os.path.dirname(out), exist_ok=True)

    tasks = load_tasks(args.dataset)[:args.limit]
    print(f"{len(tasks)} tasks, {args.workers} workers")
    with ThreadPoolExecutor(args.workers) as ex:
        results = list(ex.map(lambda t: build_task(t, args.seed, args.max_tries, args.timeout, args.rename), tasks))

    items, skipped = [], {}
    for t, (pair, why) in zip(tasks, results):
        if pair:
            items += pair
        else:
            skipped[t["task_id"]] = why
    with open(out, "w") as f:
        for it in items:
            f.write(json.dumps(it) + "\n")
    print(f"{len(items) // 2} tasks kept ({len(items)} items), {len(skipped)} skipped -> {out}")
    for k, v in list(skipped.items())[:20]:
        print(f"  skipped {k}: {v}")


if __name__ == "__main__":
    main()
