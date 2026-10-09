"""Run the real-data grid through EasyTPP, 4 jobs in parallel, appending to runs/results.jsonl (resumable).

    python -m semantic_hawkes.bench --epochs 8 --sizes 200 0      # 0 = full training set
"""
import argparse
import itertools
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

DATASETS = ["us-earthquake", "nyc-taxi", "amazon-review", "chicago-crime", "stack-overflow"]
MODELS = ["NHP", "THP", "FreeHawkesTPP", "SemHawkesTPP"]
OUT = "semantic_hawkes/runs/results.jsonl"


def done():
    if not os.path.exists(OUT):
        return set()
    return {(r["data"], r["model"], r["n_train"], r["seed"], r["tag"]) for r in map(json.loads, open(OUT))}


def job(args):
    d, m, n, seed, epochs = args
    tag = "qwen" if m == "SemHawkesTPP" else ""
    cmd = [sys.executable, "-m", "semantic_hawkes.run_easytpp", "--data", f"semantic_hawkes/real_data/tppllm/{d}",
           "--model", m, "--epochs", str(epochs), "--seed", str(seed), "--tag", tag]
    if n:
        cmd += ["--n_train", str(n)]
    if m == "SemHawkesTPP":
        cmd += ["--emb", f"semantic_hawkes/emb/{d}_qwen.npy"]
    env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    line = [l for l in p.stdout.splitlines() if l.startswith("RESULT ")]
    if not line:
        print("FAILED", args, p.stderr[-600:], flush=True)
        return
    with open(OUT, "a") as f:
        f.write(line[0][7:] + "\n")
    print("ok", args, line[0][7:140], flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--sizes", type=int, nargs="+", default=[200, 0])
    ap.add_argument("--seeds", type=int, nargs="+", default=[2019])
    ap.add_argument("--datasets", nargs="+", default=DATASETS)
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args()
    os.makedirs("semantic_hawkes/runs", exist_ok=True)
    have = done()
    todo = []
    for d, n, s, m in itertools.product(a.datasets, a.sizes, a.seeds, MODELS):
        tag = "qwen" if m == "SemHawkesTPP" else ""
        if (d, m, n or None, s, tag) not in have:
            todo.append((d, m, n, s, a.epochs))
    # longest jobs first so the 4 workers stay busy
    todo.sort(key=lambda x: (x[0] != "stack-overflow", x[0] != "nyc-taxi", -x[2] if x[2] else -10**9))
    print(len(todo), "jobs", flush=True)
    with ThreadPoolExecutor(a.jobs) as ex:
        list(ex.map(job, todo))
