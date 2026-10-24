"""Run sampled (or canonical) solutions through the HumanEval+ inputs; one result row per sample.

Defect proxy: distinct failure signatures per sample (exception type / wrong-answer shape / timeout / load error).
Raw failing-index sets are kept so detection curves under any test ordering can be rebuilt later.
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).parent
DATA = HERE / "data"


def extract_code(text, entry_point):
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", text or "", re.S)
    for b in blocks:
        if f"def {entry_point}" in b:
            return b
    if blocks:
        return blocks[0]
    return text or ""


def run(task, code):
    payload = {k: task[k] for k in ("prompt", "entry_point", "test_src", "inputs", "results", "atol")}
    payload["code"] = code
    try:
        p = subprocess.run([sys.executable, "-I", str(HERE / "_runner.py")], input=json.dumps(payload),
                           capture_output=True, text=True, timeout=120)
        return json.loads(p.stdout)
    except subprocess.TimeoutExpired:
        n = len(task["inputs"])
        return {"n": n, "fails": {"PARENT_TIMEOUT": list(range(n))}}
    except Exception as e:
        n = len(task["inputs"])
        return {"n": n, "fails": {"HARNESS:" + type(e).__name__: list(range(n))}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--canonical", action="store_true", help="validate harness on reference solutions")
    ap.add_argument("--samples", default=str(DATA / "samples.jsonl"))
    ap.add_argument("--out", default=str(DATA / "results.jsonl"))
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    tasks = {t["task_id"]: t for t in json.loads((DATA / "tasks.json").read_text())}

    if a.canonical:
        raw = {json.loads(l)["task_id"]: json.loads(l)["prompt"] + json.loads(l)["canonical_solution"]
               for l in (DATA / "humanevalplus.jsonl").read_text().splitlines()}  # body only; prepend the stub
        jobs = [(tid, raw[tid], {"model": "canonical", "task_id": tid, "sample": 0}) for tid in tasks]
    else:
        jobs = []
        done = set()
        outp = pathlib.Path(a.out)
        if outp.exists():
            done = {(r["model"], r["task_id"], r["sample"]) for r in map(json.loads, outp.read_text().splitlines())}
        for line in pathlib.Path(a.samples).read_text().splitlines():
            r = json.loads(line)
            if "error" in r or (r["model"], r["task_id"], r["sample"]) in done:
                continue
            jobs.append((r["task_id"], extract_code(r["text"], tasks[r["task_id"]]["entry_point"]),
                         {k: r[k] for k in ("model", "task_id", "sample", "cost", "prompt_tokens", "completion_tokens")}))

    def go(j):
        tid, code, meta = j
        res = run(tasks[tid], code)
        return {**meta, "n": res["n"], "fails": res["fails"]}

    rows = []
    with ThreadPoolExecutor(a.workers) as ex:
        rows = list(ex.map(go, jobs))
    if a.canonical:
        bad = [r for r in rows if r["fails"]]
        (DATA / "canonical_ok.json").write_text(json.dumps(sorted(r["task_id"] for r in rows if not r["fails"])))
        print(f"canonical: {len(rows)} tasks, {len(bad)} with failures (excluded from the study)")
        for r in bad[:15]:
            print(" ", r["task_id"], {k: len(v) for k, v in r["fails"].items()})
        return
    with open(a.out, "a") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"wrote {len(rows)} rows to {a.out}")


if __name__ == "__main__":
    main()
