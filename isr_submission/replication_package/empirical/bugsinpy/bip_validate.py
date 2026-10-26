"""Validate BugsInPy bugs (developer test fails on buggy, passes on fixed) for chosen projects. Resumable; writes valid_bugs.json."""
import json, os, sys, time, argparse, traceback
from concurrent.futures import ThreadPoolExecutor
import bip_lib as B
ap = argparse.ArgumentParser(); ap.add_argument("--projects", default="thefuck,tqdm,httpie,cookiecutter,PySnooper,sanic"); ap.add_argument("--workers", type=int, default=2)
a = ap.parse_args(); OUT = os.path.join(B.HERE, "valid_bugs.json")
res = json.load(open(OUT)) if os.path.exists(OUT) else {}
jobs = [(p, b) for p in a.projects.split(",") for b in sorted(os.listdir(f"{B.BIP}/{p}/bugs"), key=int) if f"{p}/{b}" not in res]
def run(j):
    p, b = j; t = time.time()
    try: r = B.validate(p, b)
    except Exception as e: r = dict(valid=False, why="harness: " + str(e)[:150])
    r["seconds"] = round(time.time() - t); res[f"{p}/{b}"] = r
    json.dump(res, open(OUT, "w"), indent=1); print(p, b, r["valid"], r["why"][:70], flush=True)
with ThreadPoolExecutor(a.workers) as ex: list(ex.map(run, jobs))
v = [k for k, r in res.items() if r["valid"]]; print(len(v), "valid of", len(res))
