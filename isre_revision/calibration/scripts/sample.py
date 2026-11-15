"""Sample HumanEval+ solutions from language models through OpenRouter.

Protocol follows the manuscript (Section EC.4): one fixed prompt, temperature 0.8,
max 1,024 output tokens, 20 samples per task. Output is appended to
data/samples/<model>.jsonl and the script resumes where it left off.

usage: python3 -I sample.py TASKS_JSON OUT_DIR MODEL [MODEL ...]
"""
import json
import os
import random
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

URL = "https://openrouter.ai/api/v1/chat/completions"
N_SAMPLES, TEMP, MAX_TOK, WORKERS = 20, 0.8, 1024, 24
INSTR = ("Complete the following Python function. Reply with the complete implementation, "
         "including any imports it needs, in a single python code block and nothing else.")
KEY = os.environ.get("OPENROUTER_API_KEY", "sk-or-proxy-injected")  # the proxy injects the real key


def extract(reply, entry_point):
    blocks = re.findall(r"```(?:python|py)?[^\n]*\n(.*?)```", reply, flags=re.S)
    for b in blocks:
        if re.search(rf"def\s+{re.escape(entry_point)}\s*\(", b):
            return b, "block_with_def"
    if blocks:
        return blocks[0], "first_block"
    return reply, "raw"


def call(model, prompt):
    body = json.dumps({"model": model, "temperature": TEMP, "max_tokens": MAX_TOK,
                       "messages": [{"role": "user", "content": f"{INSTR}\n\n```python\n{prompt}```"}]}).encode()
    for attempt in range(8):
        req = urllib.request.Request(URL, data=body, headers={
            "Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.loads(r.read())
            if "choices" not in d:
                raise RuntimeError(str(d)[:300])
            msg = d["choices"][0]["message"]
            return (msg.get("content") or ""), d.get("usage", {}), d.get("model"), d.get("provider")
        except urllib.error.HTTPError as e:
            if e.code in (400, 401, 403, 404):
                raise RuntimeError(f"HTTP {e.code}: {e.read()[:300]}")
            time.sleep(min(60, 2 ** attempt + random.random()))
        except Exception:
            time.sleep(min(60, 2 ** attempt + random.random()))
    raise RuntimeError("retries exhausted")


def main():
    tasks = json.load(open(sys.argv[1]))
    out_dir = sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    for model in sys.argv[3:]:
        path = os.path.join(out_dir, model.replace("/", "__") + ".jsonl")
        done = set()
        if os.path.exists(path):
            for line in open(path):
                r = json.loads(line)
                done.add((r["task_id"], r["sample"]))
        jobs = [(t, i) for t in tasks for i in range(N_SAMPLES) if (t["task_id"], i) not in done]
        lock = threading.Lock()
        t0, n_ok, n_err = time.time(), 0, 0
        with open(path, "a") as f, ThreadPoolExecutor(WORKERS) as ex:
            futs = {ex.submit(call, model, t["prompt"]): (t, i) for t, i in jobs}
            for fu in as_completed(futs):
                t, i = futs[fu]
                try:
                    reply, usage, served, provider = fu.result()
                except Exception as e:
                    n_err += 1
                    print(f"[{model}] {t['task_id']}#{i} error: {e}", flush=True)
                    if n_err > 50 and n_ok == 0:
                        print(f"[{model}] aborting model: too many errors", flush=True)
                        ex.shutdown(cancel_futures=True)
                        break
                    continue
                code, how = extract(reply, t["entry_point"])
                with lock:
                    f.write(json.dumps(dict(model=model, served_model=served, provider=provider,
                                            task_id=t["task_id"], sample=i, reply=reply, code=code,
                                            extraction=how, usage=usage)) + "\n")
                    f.flush()
                n_ok += 1
        print(f"[{model}] done: {n_ok} new, {n_err} errors, {len(done)} pre-existing, "
              f"{time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
