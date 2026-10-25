"""Pilot: measure fault *detection* by an LLM (via OpenRouter) on SWT-bench Lite, Django instances.

For one instance: (1) ask the model for a test patch that reproduces the issue (SWT-bench prompt, bm25-27k context);
(2) apply it to the buggy commit and run the touched test files; (3) apply the gold fix and run again;
(4) judge detection = some test FAILS on the buggy commit and PASSES after the gold fix.

No Docker (Docker Hub rate-limits image pulls): a git worktree + a uv-managed virtualenv per instance.
OpenRouter authentication is injected by the proxy in the sandbox; elsewhere set OPENROUTER_API_KEY.

Usage:  python3 swt_pilot.py INSTANCE_ID MODEL [--repeat N] [--workdir DIR]
"""
import argparse, json, os, re, subprocess, sys, time, urllib.request
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_URL = "https://huggingface.co/api/datasets/eth-sri/SWT-bench_Lite_bm25_27k_zsb/parquet/default/test/0.parquet"
REPO_URL = "https://github.com/django/django"


def sh(cmd, cwd=None, timeout=900, env=None):
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)
    return r.returncode, (r.stdout + r.stderr)


def load(workdir):
    p = os.path.join(workdir, "swt_lite_test.parquet")
    if not os.path.exists(p):
        sh(f"curl -sL -m 180 -o {p} {DATA_URL}")
    return pd.read_parquet(p)


def py_for(version):
    v = tuple(int(x) for x in str(version).split(".")[:2])
    return "3.8" if v < (3, 1) else ("3.9" if v < (4, 2) else "3.11")


def prepare(row, workdir):
    """Bare blobless clone (shared) + one worktree and venv per instance."""
    bare = os.path.join(workdir, "django.git")
    if not os.path.exists(bare):
        rc, out = sh(f"git clone --bare --filter=blob:none {REPO_URL} {bare}", timeout=1800); assert rc == 0, out
    wt = os.path.join(workdir, "wt", row.instance_id)
    if not os.path.exists(wt):
        rc, out = sh(f"git --git-dir={bare} worktree add --detach {wt} {row.base_commit}", timeout=900); assert rc == 0, out
    venv = os.path.join(workdir, "venv", f"{row.instance_id}")
    if not os.path.exists(venv):
        py = py_for(row.version)
        sh(f"uv python install {py}")
        rc, out = sh(f"uv venv --python {py} {venv}"); assert rc == 0, out
        rc, out = sh(f"uv pip install --python {venv}/bin/python -e {wt} -r {wt}/tests/requirements/py3.txt", timeout=1200)
        if rc != 0:  # old pins may fail; fall back to the minimum needed to run the suite
            rc, out = sh(f"uv pip install --python {venv}/bin/python -e {wt} asgiref sqlparse pytz jinja2 numpy pillow", timeout=1200)
            assert rc == 0, out
    return wt, venv


def extract_patch(text):
    m = re.search(r"<patch>\s*(.*?)</patch>", text, re.S)
    body = m.group(1) if m else text
    m2 = re.search(r"```(?:diff|patch)?\n(.*?)```", body, re.S)
    body = m2.group(1) if m2 else body
    body = body.strip("\n") + "\n"
    return body if "diff --git" in body else None


def chat(model, prompt, max_tokens=4000):
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                         "max_tokens": max_tokens, "temperature": 0.7}).encode(),
        headers={"Content-Type": "application/json",
                 **({"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"]} if os.environ.get("OPENROUTER_API_KEY") else {})})
    with urllib.request.urlopen(req, timeout=300) as r:
        j = json.load(r)
    return j["choices"][0]["message"]["content"], j.get("usage", {})


STATUS = re.compile(r"^(?P<name>.+?) \.\.\. (?P<st>ok|FAIL|ERROR|skipped.*|expected failure|unexpected success)\s*$")


def run_tests(wt, venv, modules):
    """Run Django's runner on the given test modules; return {test line: status}."""
    env = dict(os.environ, PYTHONPATH=wt)
    rc, out = sh(f"{venv}/bin/python tests/runtests.py --settings=test_sqlite -v 2 --parallel 1 {' '.join(modules)}", cwd=wt, env=env, timeout=900)
    res, pending = {}, ""
    for line in out.splitlines():
        m = STATUS.match(line)
        if m:
            res[(pending + m['name']).strip()] = m['st']; pending = ""
        elif line.startswith("test") and "..." not in line:
            pending = line + " "
        elif line.startswith("test"):
            pending = ""
    return res, out


def touched_modules(patch):
    mods = []
    for f in re.findall(r"^diff --git a/(\S+) b/\S+", patch, re.M):
        if f.startswith("tests/") and f.endswith(".py"):
            mods.append(f[len("tests/"):-3].replace("/", "."))
    return sorted(set(mods))


def run_instance(row, model, workdir, rep=0):
    t0 = time.time()
    wt, venv = prepare(row, workdir)
    out = dict(instance_id=row.instance_id, model=model, rep=rep, detected=False, reason="", cost_tokens=None)
    text, usage = chat(model, row.text)
    out["cost_tokens"] = usage
    patch = extract_patch(text)
    open(os.path.join(workdir, f"{row.instance_id}.{rep}.model_patch.diff"), "w").write(patch or text)
    if not patch:
        out["reason"] = "no_patch"; return out
    sh("git checkout -q -- . && git clean -fdq", cwd=wt)
    pf = os.path.join(workdir, f"{row.instance_id}.{rep}.model_patch.diff")
    rc, o = sh(f"git apply --whitespace=nowarn {pf}", cwd=wt)
    if rc != 0:
        out["reason"] = "patch_does_not_apply: " + o[:200]; return out
    mods = touched_modules(patch)
    if not mods:
        out["reason"] = "no_test_module"; return out
    before, log_b = run_tests(wt, venv, mods)
    gold = row.patch.replace("<patch>", "").replace("</patch>", "").strip("\n") + "\n"
    gf = os.path.join(workdir, f"{row.instance_id}.gold.diff"); open(gf, "w").write(gold)
    rc, o = sh(f"git apply --whitespace=nowarn {gf}", cwd=wt)
    assert rc == 0, "gold patch failed: " + o[:300]
    after, log_a = run_tests(wt, venv, mods)
    f2p = [t for t, s in before.items() if s == "FAIL" and after.get(t) == "ok"]
    err = [t for t, s in before.items() if s == "ERROR"]
    out.update(detected=bool(f2p), f2p=f2p[:5], n_before_fail=sum(s == "FAIL" for s in before.values()),
               n_before_error=len(err), n_tests=len(before), seconds=round(time.time() - t0, 1))
    out["reason"] = "ok" if f2p else ("tests_error_not_fail" if err and not any(s == 'FAIL' for s in before.values()) else "no_fail_to_pass")
    sh("git checkout -q -- . && git clean -fdq", cwd=wt)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("instance"); ap.add_argument("model")
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--workdir", default=os.path.join(HERE, "work"))
    a = ap.parse_args()
    os.makedirs(a.workdir, exist_ok=True)
    df = load(a.workdir)
    row = next(df[df.instance_id == a.instance].itertuples())
    for r in range(a.repeat):
        res = run_instance(row, a.model, a.workdir, r)
        print(json.dumps(res, default=str))
