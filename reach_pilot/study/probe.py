"""Check which candidate targets install and have a passing baseline (py3.11 venv per repo)."""
import json, os, subprocess, sys
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), "work")
def sh(c, cwd=None, t=900):
    r = subprocess.run(c, shell=True, cwd=cwd, capture_output=True, text=True, timeout=t); return r.returncode, r.stdout + r.stderr
ok = []
for tg in json.load(open("targets.json")):
    d = f"{W}/{tg['name']}"; os.makedirs(d, exist_ok=True)
    if not os.path.exists(f"{d}/repo"):
        rc, o = sh(f"git clone -q --depth 1 {tg['repo']} {d}/repo")
        if rc: print(tg["name"], "clone failed", o[:100]); continue
    if not os.path.exists(f"{d}/venv"):
        rc, o = sh(f"uv venv -q --python 3.11 {d}/venv && uv pip install -q --python {d}/venv/bin/python pytest -e {d}/repo")
        if rc: print(tg["name"], "install failed", o[-200:]); continue
    for mod, test in tg["modules"]:
        if not os.path.exists(f"{d}/repo/{mod}") or not os.path.exists(f"{d}/repo/{test}"):
            print(tg["name"], mod, "MISSING module/test"); continue
        rc, o = sh(f"{d}/venv/bin/python -m pytest -q --no-header -p no:cacheprovider -x {test}", cwd=f"{d}/repo", t=300)
        n = len(open(f"{d}/repo/{mod}").read().splitlines())
        print(f"{tg['name']:14s} {mod:34s} lines={n:5d} baseline_pass={rc==0} {o.strip().splitlines()[-1][:60] if o.strip() else ''}")
