"""Sample LLM solutions via OpenRouter with a hard spend cap.

Resumable: each (model, task_id, sample) is written once to data/samples.jsonl with its token usage and
cost (OpenRouter `usage.cost`), so cost data for the economic model comes for free.
"""
import argparse
import json
import os
import pathlib
import random
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

DATA = pathlib.Path(__file__).parent / "data"
URL = "https://openrouter.ai/api/v1/chat/completions"
PROMPT = ("Complete the following Python function. Reply with the complete implementation, including any "
          "imports it needs, in a single ```python code block and nothing else.\n\n```python\n{prompt}```")

lock = threading.Lock()
spent = 0.0
stop = threading.Event()


def call(model, prompt, temperature, max_tokens):
    body = json.dumps({"model": model, "temperature": temperature, "max_tokens": max_tokens,
                       "messages": [{"role": "user", "content": PROMPT.format(prompt=prompt)}],
                       "usage": {"include": True}}).encode()
    headers = {"Content-Type": "application/json"}
    if os.environ.get("OPENROUTER_API_KEY"):  # not needed behind a proxy that injects credentials
        headers["Authorization"] = "Bearer " + os.environ["OPENROUTER_API_KEY"]
    req = urllib.request.Request(URL, body, headers)
    last = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except Exception as e:  # network/429/5xx: back off and retry
            last = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"giving up: {last}")


def work(job, out, budget, temperature, max_tokens):
    global spent
    if stop.is_set():
        return
    model, task, k = job
    t0 = time.time()
    try:
        resp = call(model, task["prompt"], temperature, max_tokens)
        msg = resp["choices"][0]["message"].get("content") or ""
        usage = resp.get("usage", {})
        rec = {"model": model, "task_id": task["task_id"], "sample": k, "text": msg,
               "prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens"),
               "cost": usage.get("cost"), "latency": round(time.time() - t0, 2),
               "finish": resp["choices"][0].get("finish_reason")}
    except Exception as e:
        rec = {"model": model, "task_id": task["task_id"], "sample": k, "error": str(e)[:200]}
    with lock:
        out.write(json.dumps(rec) + "\n")
        out.flush()
        spent += rec.get("cost") or 0.0
        if spent >= budget:
            stop.set()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", required=True)
    ap.add_argument("--tasks", type=int, default=20)
    ap.add_argument("--samples", type=int, default=5)
    ap.add_argument("--budget", type=float, default=5.0, help="hard cap in USD for THIS run")
    ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default=str(DATA / "samples.jsonl"))
    a = ap.parse_args()

    tasks = json.loads((DATA / "tasks.json").read_text())
    ok = pathlib.Path(DATA / "canonical_ok.json")
    if ok.exists():  # only tasks whose reference solution passes the harness
        keep = set(json.loads(ok.read_text()))
        tasks = [t for t in tasks if t["task_id"] in keep]
    random.Random(a.seed).shuffle(tasks)  # fixed shuffle so --tasks N is a stable prefix
    tasks = tasks[:a.tasks]
    out_path = pathlib.Path(a.out)
    done = set()
    if out_path.exists():
        for line in out_path.read_text().splitlines():
            r = json.loads(line)
            if "error" not in r:
                done.add((r["model"], r["task_id"], r["sample"]))
    jobs = [(m, t, k) for t in tasks for m in a.models for k in range(a.samples) if (m, t["task_id"], k) not in done]
    print(f"{len(jobs)} calls to make ({len(done)} already done); budget ${a.budget:.2f}")
    with open(out_path, "a") as out, ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(lambda j: work(j, out, a.budget, a.temperature, a.max_tokens), jobs))
    print(f"spent ${spent:.4f} this run; stopped_by_budget={stop.is_set()}")


if __name__ == "__main__":
    main()
