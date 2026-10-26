"""Mutation-score pilot for the human baseline of 'reach'.

Pool of faults  = AST mutants of one module (arithmetic, comparison, boolean, constant, 'not' removal).
Human reach     = share of mutants killed by the module's existing, human-written test file.
Tool reach      = share killed by tests an LLM writes from the module source alone (K independent attempts).
A(K)            = tool kill share / human kill share, reported with two denominators:
                  (a) all mutants, (b) mutants killed by at least one side (a proxy that drops equivalent mutants).

Steps:
  python3 mutation_pilot.py setup   [--repo URL --module toolz/itertoolz.py --tests toolz/tests/test_itertoolz.py]
  python3 mutation_pilot.py mutants --max 150
  python3 mutation_pilot.py human
  python3 mutation_pilot.py llm     --model anthropic/claude-haiku-5.5 --k 3
  python3 mutation_pilot.py report

Caveats for the paper: mutants are not real faults; equivalent mutants inflate the denominator; the human suite is the
accumulated effort of years, so it is not a budget-matched baseline.
"""
import argparse, ast, json, os, random, re, shutil, subprocess, urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(HERE, "work")
CFG = os.path.join(W, "cfg.json")


def sh(cmd, cwd=None, timeout=600):
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout + r.stderr


def cfg():
    return json.load(open(CFG))


SWAP_BIN = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.FloorDiv, ast.FloorDiv: ast.Mult, ast.Mod: ast.Mult}
SWAP_CMP = {ast.Eq: ast.NotEq, ast.NotEq: ast.Eq, ast.Lt: ast.LtE, ast.LtE: ast.Lt, ast.Gt: ast.GtE, ast.GtE: ast.Gt,
            ast.Is: ast.IsNot, ast.IsNot: ast.Is, ast.In: ast.NotIn, ast.NotIn: ast.In}


def sites(tree):
    """Yield (index, description, node) for every mutable site; docstrings are skipped."""
    doc = set()
    for n in ast.walk(tree):
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)) and n.body \
                and isinstance(n.body[0], ast.Expr) and isinstance(getattr(n.body[0], "value", None), ast.Constant):
            doc.add(id(n.body[0].value))
    i = 0
    for n in ast.walk(tree):
        d = None
        if isinstance(n, ast.BinOp) and type(n.op) in SWAP_BIN:
            d = f"{type(n.op).__name__}->{SWAP_BIN[type(n.op)].__name__}"
        elif isinstance(n, ast.Compare) and type(n.ops[0]) in SWAP_CMP:
            d = f"{type(n.ops[0]).__name__}->{SWAP_CMP[type(n.ops[0])].__name__}"
        elif isinstance(n, ast.BoolOp):
            d = "And<->Or"
        elif isinstance(n, ast.Constant) and type(n.value) is int and id(n) not in doc:
            d = f"const {n.value}->{n.value + 1}"
        elif isinstance(n, ast.UnaryOp) and isinstance(n.op, ast.Not):
            d = "remove not"
        if d:
            yield i, d, n
            i += 1


def mutate(n):
    if isinstance(n, ast.BinOp):
        n.op = SWAP_BIN[type(n.op)]()
    elif isinstance(n, ast.Compare):
        n.ops[0] = SWAP_CMP[type(n.ops[0])]()
    elif isinstance(n, ast.BoolOp):
        n.op = ast.Or() if isinstance(n.op, ast.And) else ast.And()
    elif isinstance(n, ast.Constant):
        n.value = n.value + 1
    elif isinstance(n, ast.UnaryOp):          # 'not x' -> 'x'
        inner = n.operand
        n.__class__ = type(inner); n.__dict__.clear(); n.__dict__.update(inner.__dict__)


def make_mutants(src):
    """List of (description, mutated source), one mutation per mutant."""
    out = []
    count = len(list(sites(ast.parse(src))))
    for i in range(count):
        t = ast.parse(src)
        d, node = [(d, x) for j, d, x in sites(t) if j == i][0]
        mutate(node)
        try:
            out.append((d, ast.unparse(ast.fix_missing_locations(t))))
        except Exception:
            pass
    return out


def run_pytest(repo, target, ids=None, timeout=60):
    args = " ".join(f"'{i}'" for i in ids) if ids else target
    try:
        r = subprocess.run(f"{W}/venv/bin/python -m pytest -x -q --no-header -p no:cacheprovider {args}",
                           shell=True, cwd=repo, capture_output=True, text=True, timeout=timeout)
        return r.returncode          # 0 pass; otherwise the mutant is detected
    except subprocess.TimeoutExpired:
        return 124                   # a mutant that hangs counts as detected


def kill_matrix(mutants, test_target, ids=None, workers=4):
    c = cfg(); base = os.path.join(W, "repo"); modpath = c["module"]
    orig = open(os.path.join(base, modpath)).read()
    tdir = os.path.dirname(c["tests"])
    copies = []
    for w in range(workers):
        p = os.path.join(W, f"copy{w}")
        if os.path.exists(p):
            shutil.rmtree(p)
        shutil.copytree(base, p); copies.append(p)
    results = [None] * len(mutants)

    def worker(w):
        p = copies[w]
        for idx in range(w, len(mutants), workers):
            open(os.path.join(p, modpath), "w").write(mutants[idx][1])
            results[idx] = run_pytest(p, test_target, ids) != 0
        open(os.path.join(p, modpath), "w").write(orig)

    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(worker, range(workers)))
    return results


def step_setup(a):
    os.makedirs(W, exist_ok=True)
    if not os.path.exists(os.path.join(W, "repo")):
        rc, o = sh(f"git clone -q --depth 1 {a.repo} {W}/repo"); assert rc == 0, o
    if not os.path.exists(os.path.join(W, "venv")):
        rc, o = sh(f"uv venv -q --python 3.11 {W}/venv && uv pip install -q --python {W}/venv/bin/python pytest -e {W}/repo"); assert rc == 0, o
    json.dump(dict(repo=a.repo, module=a.module, tests=a.tests), open(CFG, "w"))
    c = cfg()
    print("existing tests pass on the original module:", run_pytest(os.path.join(W, "repo"), c["tests"], timeout=300) == 0)


def step_mutants(a):
    c = cfg(); src = open(os.path.join(W, "repo", c["module"])).read()
    ms = make_mutants(src)
    random.Random(0).shuffle(ms)
    ms = ms[: a.max]
    json.dump(ms, open(os.path.join(W, "mutants.json"), "w"))
    from collections import Counter
    print(len(ms), "mutants;", dict(Counter(d.split()[0] if d.startswith("const") else d for d, _ in ms)))


def step_human(a):
    c = cfg(); ms = json.load(open(os.path.join(W, "mutants.json")))
    killed = kill_matrix(ms, c["tests"], workers=a.workers)
    json.dump(killed, open(os.path.join(W, "human_killed.json"), "w"))
    print(f"human (existing tests) kill share: {sum(killed)}/{len(killed)} = {sum(killed)/len(killed):.3f}")


def chat(model, prompt, tries=3):
    """Returns (text, cost). Reasoning models can spend the whole budget thinking and return no content: retry."""
    cost = 0.0
    for _ in range(tries):
        req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
            data=json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": 16000,
                             "temperature": 0.8}).encode(),
            headers={"Content-Type": "application/json",
                     **({"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"]} if os.environ.get("OPENROUTER_API_KEY") else {})})
        j = json.load(urllib.request.urlopen(req, timeout=600))
        cost += j.get("usage", {}).get("cost") or 0.0
        text = j["choices"][0]["message"].get("content")
        if text:
            return text, cost
        print("  empty content (finish_reason=%s); retrying" % j["choices"][0].get("finish_reason"))
    return "", cost


def step_llm(a):
    c = cfg(); ms = json.load(open(os.path.join(W, "mutants.json")))
    base = os.path.join(W, "repo"); src = open(os.path.join(base, c["module"])).read()
    modname = c["module"][:-3].replace("/", "."); tdir = os.path.dirname(c["tests"])
    prompt = (f"Below is the source of the Python module `{modname}`. Write a thorough pytest test file for it. Test the "
              f"behaviour of its public functions, including edge cases. Import from `{modname}`. Output only one python code block.\n\n"
              f"```python\n{src}\n```")
    cost, per_attempt = 0.0, []
    for k in range(a.k):
        text, cst = chat(a.model, prompt); cost += cst
        m = re.findall(r"```python\n(.*?)```", text, re.S)
        fn = f"test_llm_attempt{k}.py"
        open(os.path.join(base, tdir, fn), "w").write(m[0] if m else text)
        r = subprocess.run(f"{W}/venv/bin/python -m pytest -q --no-header -p no:cacheprovider -rA --tb=no {tdir}/{fn}",
                           shell=True, cwd=base, capture_output=True, text=True, timeout=300)
        ids = re.findall(r"(?m)^PASSED (\S+)", r.stdout)       # keep only tests that pass on the original
        print(f"attempt {k}: {len(ids)} tests pass on the original")
        if not ids:
            per_attempt.append([False] * len(ms)); continue
        killed = kill_matrix(ms, "", ids=ids, workers=a.workers)
        per_attempt.append(killed)
        print(f"  kill share {sum(killed)/len(killed):.3f}")
    json.dump(dict(per_attempt=per_attempt, cost=cost, model=a.model), open(os.path.join(W, "llm_killed.json"), "w"))
    print(f"model cost ${cost:.4f}")


def step_report(a):
    import numpy as np
    h = np.array(json.load(open(os.path.join(W, "human_killed.json"))), bool)
    L = json.load(open(os.path.join(W, "llm_killed.json"))); pa = np.array(L["per_attempt"], bool)
    n = len(h); rng = np.random.default_rng(0)
    print(f"{n} mutants; human kill {h.mean():.3f}")
    for k in range(1, len(pa) + 1):
        t = pa[:k].any(axis=0)
        for name, mask in (("all mutants", np.ones(n, bool)), ("killed by either side", h | t)):
            if h[mask].sum() == 0:
                continue
            est = t[mask].mean() / h[mask].mean(); bs = []
            for _ in range(2000):
                i = rng.integers(0, n, n); mk = mask[i]
                if h[i][mk].mean() > 0:
                    bs.append(t[i][mk].mean() / h[i][mk].mean())
            print(f"k={k} [{name}]: tool {t[mask].mean():.3f}, human {h[mask].mean():.3f}, A = {est:.2f} "
                  f"(95% CI {np.percentile(bs,2.5):.2f}-{np.percentile(bs,97.5):.2f})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("setup"); s.add_argument("--repo", default="https://github.com/pytoolz/toolz")
    s.add_argument("--module", default="toolz/itertoolz.py"); s.add_argument("--tests", default="toolz/tests/test_itertoolz.py")
    s = sp.add_parser("mutants"); s.add_argument("--max", type=int, default=150)
    s = sp.add_parser("human"); s.add_argument("--workers", type=int, default=4)
    s = sp.add_parser("llm"); s.add_argument("--model", default="anthropic/claude-haiku-5.5"); s.add_argument("--k", type=int, default=3); s.add_argument("--workers", type=int, default=4)
    sp.add_parser("report")
    a = ap.parse_args()
    {"setup": step_setup, "mutants": step_mutants, "human": step_human, "llm": step_llm, "report": step_report}[a.cmd](a)
