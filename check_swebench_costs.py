"""Check whether official SWE-bench leaderboard submissions record cost information.

Run this on a machine that can reach GitHub (needs GITHUB_TOKEN for the API listing).
It lists submissions under evaluation/<split>/ of SWE-bench/experiments, reads each metadata.yaml and
prints (a) which submissions mention cost/price/token fields, (b) a sample of those lines.
It does NOT download logs or trajectories (those are on S3 and need an AWS account); if you have
downloaded some trajectories (*.traj), pass their folder with --trajs to see model_stats cost fields.

Usage:  python check_swebench_costs.py [split=verified] [max_submissions=60] [--trajs DIR]
NOTE: written from the repository layout described in its docs; not tested against the live repository.
"""
import json
import os
import re
import sys
import urllib.request

REPO = "SWE-bench/experiments"
TOKEN = os.environ.get("GITHUB_TOKEN")
PAT = re.compile(r"cost|price|usd|\$|token", re.I)


def get(url, raw=False):
    h = {"User-Agent": "cost-check", "Accept": "application/vnd.github+json"}
    if TOKEN:
        h["Authorization"] = f"Bearer {TOKEN}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=h), timeout=60) as r:
        data = r.read().decode("utf-8", "replace")
    return data if raw else json.loads(data)


args = [a for a in sys.argv[1:] if not a.startswith("--")]
split = args[0] if args else "verified"
limit = int(args[1]) if len(args) > 1 else 60
subs = [x["name"] for x in get(f"https://api.github.com/repos/{REPO}/contents/evaluation/{split}") if x["type"] == "dir"]
subs = sorted(subs)[-limit:]                      # most recent submissions (folders start with the date)
print(f"{len(subs)} submissions checked in evaluation/{split}")

with_cost = 0
for s in subs:
    try:
        txt = get(f"https://raw.githubusercontent.com/{REPO}/main/evaluation/{split}/{s}/metadata.yaml", raw=True)
    except Exception as e:
        print(f"  {s}: no metadata.yaml ({e})")
        continue
    hits = [l.strip() for l in txt.splitlines() if PAT.search(l)]
    if hits:
        with_cost += 1
        print(f"  {s}: " + " | ".join(hits[:3]))
print(f"\nsubmissions whose metadata mentions cost/price/token: {with_cost} of {len(subs)}")

if "--trajs" in sys.argv:
    folder = sys.argv[sys.argv.index("--trajs") + 1]
    n = nz = 0
    for root, _, files in os.walk(folder):
        for f in files:
            if f.endswith(".traj"):
                try:
                    ms = (json.load(open(os.path.join(root, f))).get("info") or {}).get("model_stats") or {}
                except Exception:
                    continue
                n += 1
                nz += bool(ms.get("instance_cost"))
    print(f"trajectories with nonzero instance_cost: {nz} of {n}")
