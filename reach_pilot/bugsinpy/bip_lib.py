"""BugsInPy harness: prepare a bug (worktree + venv), validate it, and judge LLM-written blind tests.

Pool = real faults that humans found and fixed. A bug is valid when the developer's test fails on the buggy commit
and passes after the fix (the fix is bug_patch.txt applied to the buggy commit).
Detection by a tool = a test it wrote (from the buggy source files only) fails on the buggy version and passes on the fixed one.
"""
import json, os, re, shutil, subprocess, xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.join(HERE, "work"); BIP = f"{W}/bip/projects"
SUSPECT = ("ImportError", "ModuleNotFoundError", "SyntaxError", "IndentationError", "NameError", "fixture ")


def sh(c, cwd=None, t=900, env=None):
    r = subprocess.run(c, shell=True, cwd=cwd, capture_output=True, text=True, timeout=t, env=env); return r.returncode, r.stdout + r.stderr


def info(project, bug):
    d = f"{BIP}/{project}/bugs/{bug}"; kv = {}
    for l in open(f"{d}/bug.info"):
        if "=" in l: k, v = l.strip().split("=", 1); kv[k] = v.strip('"')
    kv["run_test"] = open(f"{d}/run_test.sh").read().strip(); kv["dir"] = d
    kv["project_url"] = re.search(r'github_url="(.+?)"', open(f"{BIP}/{project}/project.info").read()).group(1).rstrip("/")
    return kv


def prepare(project, bug):
    """Return (worktree, python) with the buggy commit checked out and dependencies installed; raises on failure."""
    kv = info(project, bug); pd_ = f"{W}/{project}"; os.makedirs(pd_, exist_ok=True)
    repo = f"{pd_}/repo.git"
    if not os.path.exists(repo):
        rc, o = sh(f"git clone --bare --filter=blob:none {kv['project_url']}.git {repo}", t=1800); assert rc == 0, o[-300:]
    wt = f"{pd_}/wt{bug}"
    if not os.path.exists(wt):
        rc, o = sh(f"git --git-dir={repo} worktree add --detach {wt} {kv['buggy_commit_id']}"); assert rc == 0, o[-300:]
    venv = f"{pd_}/venv{bug}"; py = f"{venv}/bin/python"
    if not os.path.exists(py):
        v = ".".join(kv["python_version"].split(".")[:2])
        if v in ("3.6", "3.7"): v = "3.8"          # uv cannot install 3.6/3.7; the closest available interpreter is used
        sh(f"uv python install {v}")
        rc, o = sh(f"uv venv -q --python {v} {venv}"); assert rc == 0, o[-300:]
        req = f"{kv['dir']}/requirements.txt"
        rc, o = sh(f"uv pip install -q --python {py} -r {req}", t=1800)
        if rc != 0:   # pinned old dependencies often fail to resolve: install one by one, pinned then unpinned, ignore failures
            for l in open(req):
                l = l.strip()
                if not l or l.startswith("#"): continue
                name = re.split(r"[=<>~!;]", l)[0].strip()
                if name in ("pkg-resources", "pkg_resources"): continue
                rc1, _ = sh(f"uv pip install -q --python {py} '{l}'", t=600)
                if rc1 != 0: sh(f"uv pip install -q --python {py} {name}", t=600)
        sh(f"uv pip install -q --python {py} pytest", t=600)
        rc, o = sh(f"uv pip install -q --python {py} -e {wt} --no-deps", t=900)
    if not os.path.exists(f"{venv}/.setup_fixed"):   # old pytest + new setuptools (vendored typeguard) break: use a period-appropriate setuptools
        sh(f"uv pip install -q --python {py} 'setuptools<60' wheel", t=600); open(f"{venv}/.setup_fixed", "w").write("1")
    return wt, py, kv


def dev_test_files(kv):
    return [f.strip() for f in kv["test_file"].split(";") if f.strip()]


def patch_text(kv):
    b = open(f"{kv['dir']}/bug_patch.txt", "rb").read()
    for enc in ("utf-8", "utf-16"):
        try: return b.decode(enc)
        except UnicodeDecodeError: pass
    return b.decode("latin-1")


def apply_fix(wt, kv, tag):
    """Apply the source fix (bug_patch.txt, re-encoded to UTF-8 when needed) to the working tree."""
    p = f"{wt}/.fix.diff"; open(p, "w", encoding="utf-8", newline="").write(patch_text(kv))
    rc, o = sh(f"git apply --whitespace=nowarn {p}", cwd=wt); os.remove(p); return rc == 0, o[:200]


def revert(wt):
    sh("git checkout -q -- . && git clean -fdq", cwd=wt)


def run_pytest_xml(wt, py, target, timeout=300):
    """Run pytest on target, return {test id: (outcome, exception line)}."""
    xml = f"{wt}/.out.xml"
    if os.path.exists(xml): os.remove(xml)
    env = dict(os.environ, PYTHONPATH=wt)
    try:
        rc, out = sh(f"{py} -m pytest -q -p no:cacheprovider --junitxml={xml} {target}", cwd=wt, t=timeout, env=env)
    except subprocess.TimeoutExpired:
        return {}, "timeout"
    res = {}
    if not os.path.exists(xml): return res, out[-300:]
    for tc in ET.parse(xml).getroot().iter("testcase"):
        tid = f"{tc.get('classname')}::{tc.get('name')}"; oc, exc = "passed", ""
        for k in ("failure", "error", "skipped"):
            el = tc.find(k)
            if el is not None: oc, exc = ("failed" if k == "failure" else k), (el.get("message") or "")[:150]
        res[tid] = (oc, exc)
    return res, out[-300:]


def validate(project, bug):
    """Developer test: fails on buggy, passes on fixed (same environment)."""
    wt, py, kv = prepare(project, bug)
    revert(wt)
    # developer tests live in the fixed commit: fetch them
    repo = f"{W}/{project}/repo.git"
    for f in dev_test_files(kv):
        rc, o = sh(f"git --git-dir={repo} show {kv['fixed_commit_id']}:{f} > {wt}/{f}"); 
        if rc != 0: return dict(valid=False, why="cannot fetch dev test: " + o[:100])
    target = kv["run_test"].split("pytest", 1)[-1].strip() if "pytest" in kv["run_test"] else " ".join(dev_test_files(kv))
    before, ob = run_pytest_xml(wt, py, target)
    ok, o = apply_fix(wt, kv, "fix")
    if not ok: revert(wt); return dict(valid=False, why="bug_patch does not apply: " + o)
    after, oa = run_pytest_xml(wt, py, target)
    revert(wt)
    f2p = [t for t, (oc, _) in before.items() if oc == "failed" and after.get(t, ("", ""))[0] == "passed"]
    return dict(valid=bool(f2p), why="" if f2p else f"no fail->pass (before {len(before)}, after {len(after)}) {ob[-120:]}", n_f2p=len(f2p))
