"""For every stored LLM test file, compare passing test ids parsed by the harness regex with exact ids from JUnit XML."""
import json, os, re, subprocess, glob, xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
W = os.path.join(os.path.dirname(os.path.abspath(__file__)), "work")
T = json.load(open("targets.json")); out = []
jobs = []
for t in T:
    base = f"{W}/{t['name']}/repo"; py = f"{W}/{t['name']}/venv/bin/python"
    for mod, test in t["modules"]:
        tdir = os.path.dirname(test); key = re.sub(r'[^a-z0-9]', '', mod.lower())
        for f in sorted(glob.glob(f"{base}/{tdir}/test_llm_{key}_*.py")): jobs.append((t["name"], mod, base, py, os.path.relpath(f, base)))
def one(j):
    name, mod, base, py, rel = j; env = dict(os.environ, PYTHONPATH=f"{base}/src:{base}"); x = f"/tmp/jx_{os.getpid()}_{abs(hash(rel))}.xml"
    try: r = subprocess.run(f"{py} -m pytest -q --no-header -p no:cacheprovider --color=no -rA --tb=no --junitxml={x} '{rel}'", shell=True, cwd=base, capture_output=True, text=True, timeout=60, env=env)
    except subprocess.TimeoutExpired: return name, mod, rel, -1, -1, 0
    rx = set(re.findall(r"(?m)^PASSED (\S+)", r.stdout)); ok = set()
    try:
        for tc in ET.parse(x).getroot().iter("testcase"):
            if not any(c.tag in ("failure", "error", "skipped") for c in tc): ok.add(tc.get("name"))
    except Exception: pass
    bad = [i for i in rx if i.split("::")[-1] not in ok]
    return name, mod, rel, len(rx), len(ok), len(bad)
with ThreadPoolExecutor(4) as ex:
    for r in ex.map(one, jobs): out.append(r)
import collections
agg = collections.defaultdict(lambda: [0, 0])
for name, mod, rel, n_rx, n_ok, n_bad in out: agg[mod][0] += 1; agg[mod][1] += (n_bad > 0 or n_rx < n_ok)
for k, v in agg.items(): print(k, "files", v[0], "with truncated or missing ids", v[1])
json.dump(out, open("check_ids.json", "w"))
