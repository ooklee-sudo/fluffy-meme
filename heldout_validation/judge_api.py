"""LLM judge L3 via OpenRouter (different family, larger than the generators). Same prompt as run_heldout.py.
API latency is not comparable with the CPU latency of the 2 s timeout, so no verdict is discarded (failure = False).
Usage: python judge_api.py --gen qwen0.5b --model meta-llama/llama-3.3-70b-instruct --name llama70b
"""
import argparse, json, os, time, urllib.request
from concurrent.futures import ThreadPoolExecutor

RES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results")
JUDGE_SYS = "You are a strict fact checker."


def call(model, system, user, tries=6):
    body = json.dumps({"model": model, "temperature": 0, "max_tokens": 8,
                       "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}).encode()
    for k in range(tries):
        try:
            headers = {"Content-Type": "application/json"}
            if os.environ.get("OPENROUTER_API_KEY"):          # set this variable when running outside a proxy that adds credentials
                headers["Authorization"] = "Bearer " + os.environ["OPENROUTER_API_KEY"]
            req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=body, headers=headers)
            t0 = time.time()
            with urllib.request.urlopen(req, timeout=60) as r:
                j = json.load(r)
            return j["choices"][0]["message"]["content"] or "", time.time() - t0
        except Exception as e:
            time.sleep(2 ** k)
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gen", required=True); ap.add_argument("--model", required=True); ap.add_argument("--name", required=True)
    ap.add_argument("--limit", type=int, default=0); ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    items = [json.loads(l) for l in open(os.path.join(RES, f"gen_{a.gen}.jsonl"))]
    items = [r for r in items if not r["abstain"]]
    path = os.path.join(RES, f"judge_{a.name}_{a.gen}.jsonl")
    done = {json.loads(l)["id"] for l in open(path)} if os.path.exists(path) else set()
    todo = [r for r in items if r["id"] not in done]
    if a.limit: todo = todo[: a.limit]

    def one(r):
        user = (f"Passage: {r['passage']}\n\nQuestion: {r['question']}\n\nAnswer: {r['answer']}\n\n"
                "Is the answer fully supported by the passage? Reply with exactly one word: SUPPORTED or UNSUPPORTED.")
        raw, lat = call(a.model, JUDGE_SYS, user)
        return r["id"], raw, lat

    n_bad = 0
    with open(path, "a") as fh, ThreadPoolExecutor(a.workers) as ex:
        for i, (id_, raw, lat) in enumerate(ex.map(one, todo)):
            if raw is None:
                n_bad += 1; continue          # not written -> retried on the next run
            fh.write(json.dumps({"id": id_, "raw": raw, "unsupported": raw.upper().replace(" ", "").startswith("UNSUP"),
                                 "latency_s": lat, "failure": False}) + "\n"); fh.flush()
            if (i + 1) % 100 == 0: print(f"[{a.name}/{a.gen}] {i+1}/{len(todo)}", flush=True)
    print(f"{a.name}/{a.gen}: wrote {len(todo)-n_bad}, failed {n_bad}")


if __name__ == "__main__":
    main()
