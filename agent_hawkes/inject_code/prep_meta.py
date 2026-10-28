"""Per-bug metadata for the coding experiment: developer test files (from the fixed commit), test target,
fail-to-pass tests, tests passing on the buggy version, and the failing output shown to the agent. Writes bug_meta.json."""
import json, os, shutil, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "/home/user/fluffy-meme/reach_pilot/bugsinpy")
import bip_lib as B
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bug_meta.json")
valid = [k for k, v in json.load(open("/home/user/fluffy-meme/reach_pilot/bugsinpy/valid_bugs.json")).items() if v.get("valid")]


def copy_tree(wt):
    tmp = tempfile.mkdtemp(prefix="bipc_", dir="/home/user/bipruns")
    shutil.copytree(wt, tmp, dirs_exist_ok=True, ignore=shutil.ignore_patterns(".git"), symlinks=True); return tmp


def one(key):
    proj, bug = key.split("/")
    try:
        kv = B.info(proj, bug); wt = f"{B.W}/{proj}/wt{bug}"; py = f"{B.W}/{proj}/venv{bug}/bin/python"
        repo = f"{B.W}/{proj}/repo.git"; tests = {}
        for f in B.dev_test_files(kv):
            rc, o = B.sh(f"git --git-dir={repo} show {kv['fixed_commit_id']}:{f}"); assert rc == 0, o[:100]; tests[f] = o
        target = kv["run_test"].split("pytest", 1)[-1].strip() if "pytest" in kv["run_test"] else " ".join(tests)
        d = wt; B.revert(wt)
        for f, txt in tests.items(): open(f"{d}/{f}", "w").write(txt)
        before, out_b = B.run_pytest_xml(d, py, target)
        rc, raw = B.sh(f"{py} -m pytest -x -q -p no:cacheprovider {target} 2>&1 | tail -40", cwd=d, env=dict(os.environ, PYTHONPATH=d))
        ok, _ = B.apply_fix(d, kv, "fix") if False else (None, None)
        # apply the developer fix in a second copy to get fail-to-pass tests
        d2 = wt
        p = f"{d2}/.fix.diff"; open(p, "w", encoding="utf-8", newline="").write(B.patch_text(kv))
        rc2, o2 = B.sh(f"patch -p1 -s < {p}", cwd=d2); os.remove(p)
        after, _ = B.run_pytest_xml(d2, py, target)
        B.revert(wt)
        f2p = [t for t, (oc, _) in before.items() if oc in ("failed", "error") and after.get(t, ("", ""))[0] == "passed"]
        p2p = [t for t, (oc, _) in before.items() if oc == "passed" and after.get(t, ("", ""))[0] == "passed"]
        src = [l[6:].strip() for l in B.patch_text(kv).splitlines() if l.startswith("+++ b/")]
        return key, dict(ok=bool(f2p) and rc2 == 0, target=target, tests=tests, f2p=f2p, p2p=p2p, fail_output=raw[-3000:], fixed_files=src)
    except Exception as e:
        return key, dict(ok=False, err=str(e)[:300])


if __name__ == "__main__":
    os.makedirs("/home/user/bipruns", exist_ok=True)
    old = json.load(open(OUT)) if os.path.exists(OUT) else {}
    todo = [k for k in valid if not old.get(k, {}).get("ok")]
    with ThreadPoolExecutor(6) as ex: res = dict(ex.map(one, todo))
    old.update(res); res = old
    json.dump(res, open(OUT, "w"), indent=1)
    print(sum(v["ok"] for v in res.values()), "of", len(res), [k for k, v in res.items() if not v["ok"]][:20])
