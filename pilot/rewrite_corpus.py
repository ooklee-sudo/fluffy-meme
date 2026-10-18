"""Build the machine-rewritten reference corpus through OpenRouter.

Input  : JSONL of human-written chunks, one object per line:
         {"id": str, "text": str, "disclosure": str (optional)}
         `disclosure` is a short invention description (e.g., the abstract); if
         absent, the first 300 characters of the chunk are used for the
         "draft" prompt.
Output : JSONL of rewrites, one record per call, resumable.
         A run manifest (models, prompts, settings, budget) is written next to it.

The API key is read from OPENROUTER_API_KEY and never written to disk.
A hard budget cap stops the run before any call that could exceed it.
"""
import argparse, json, os, random, sys, threading, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

API = "https://openrouter.ai/api/v1"

MODELS = {  # id: tier
    "meta-llama/llama-4-maverick": "cheap",
    "qwen/qwen3.8-flash": "cheap",
    "deepseek/deepseek-v4.1-flash": "cheap",
    "mistralai/mistral-small-2603": "cheap",
    "google/gemini-3.8-flash": "cheap",
    "openai/gpt-6.1-sol": "top",
    "anthropic/claude-opus-5.5": "top",
}

PROMPTS = {
    "polish": (
        "Below is a passage from a draft patent specification. Polish it for clarity, "
        "grammar and consistent technical terminology, keeping the technical content, "
        "structure and approximate length. Output only the revised passage.\n\n{text}"
    ),
    "expand": (
        "Below is a short summary of an invention. Expand it into a passage of a patent "
        "specification of about {n_words} words, in standard patent drafting style. "
        "Output only the passage.\n\n{disclosure}"
    ),
    "draft": (
        "You are assisting with drafting a U.S. patent application. Using the invention "
        "disclosure below, write a detailed-description passage of about {n_words} words. "
        "Output only the passage.\n\nInvention disclosure:\n{disclosure}"
    ),
}

SETTINGS = {"temperature": 0.7, "max_tokens_factor": 1.6, "reasoning": {"enabled": False}}


def http_json(url, payload=None, key=None, timeout=120):
    req = urllib.request.Request(url, data=None if payload is None else json.dumps(payload).encode())
    req.add_header("Content-Type", "application/json")
    if key:
        req.add_header("Authorization", f"Bearer {key}")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def fetch_prices():
    out = {}
    for m in http_json(f"{API}/models")["data"]:
        pr = m.get("pricing", {})
        try:
            out[m["id"]] = (float(pr["prompt"]), float(pr["completion"]))  # USD per token
        except (KeyError, ValueError):
            pass
    return out


def tok(s):  # rough token estimate
    return max(1, len(s) // 4)


def build_prompt(kind, chunk):
    text = chunk["text"]
    n_words = max(100, len(text.split()))
    disclosure = chunk.get("disclosure") or text[:300]
    return PROMPTS[kind].format(text=text, n_words=n_words, disclosure=disclosure)


def plan_jobs(chunks, n_cheap, n_top, seed, done):
    rng = random.Random(seed)
    jobs = []
    for model, tier in MODELS.items():
        n = n_cheap if tier == "cheap" else n_top
        for kind in PROMPTS:
            for c in rng.sample(chunks, min(n, len(chunks))):
                if (model, kind, c["id"]) not in done:
                    jobs.append((model, kind, c))
    rng.shuffle(jobs)
    return jobs


def est_cost(job, prices):
    model, kind, c = job
    p_in, p_out = prices[model]
    n_in = tok(build_prompt(kind, c))
    n_out = int(tok(c["text"]) * SETTINGS["max_tokens_factor"])
    return n_in * p_in + n_out * p_out, n_out


def call_model(model, prompt, max_tokens, key):
    return http_json(f"{API}/chat/completions", {
        "model": model, "messages": [{"role": "user", "content": prompt}],
        "temperature": SETTINGS["temperature"], "max_tokens": max_tokens,
        "reasoning": SETTINGS["reasoning"], "usage": {"include": True},
    }, key=key)


class Budget:
    def __init__(self, cap):
        self.cap, self.spent, self.reserved, self.lock = cap, 0.0, 0.0, threading.Lock()

    def reserve(self, amount):
        with self.lock:
            if self.spent + self.reserved + amount > self.cap:
                return False
            self.reserved += amount
            return True

    def settle(self, reserved, actual):
        with self.lock:
            self.reserved -= reserved
            self.spent += actual


def main(argv=None, call=call_model, price_fn=fetch_prices):
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--budget", type=float, default=500.0, help="hard cap in USD")
    ap.add_argument("--n-cheap", type=int, default=1000, help="chunks per prompt per cheap model")
    ap.add_argument("--n-top", type=int, default=500, help="chunks per prompt per top model")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--dry-run", action="store_true", help="estimate cost only")
    a = ap.parse_args(argv)

    prices = price_fn()
    missing = [m for m in MODELS if m not in prices]
    if missing:
        sys.exit(f"Models not listed on OpenRouter right now: {missing}")

    chunks = [json.loads(l) for l in open(a.input)]
    done = set()
    if os.path.exists(a.out):
        for l in open(a.out):
            r = json.loads(l)
            done.add((r["model"], r["prompt_type"], r["chunk_id"]))
    jobs = plan_jobs(chunks, a.n_cheap, a.n_top, a.seed, done)

    per_model = {m: 0.0 for m in MODELS}
    for j in jobs:
        per_model[j[0]] += est_cost(j, prices)[0]
    print(f"{len(jobs)} calls planned ({len(done)} already done)")
    for m, c in per_model.items():
        print(f"  {m:36s} est max ${c:8.2f}")
    total = sum(per_model.values())
    print(f"  TOTAL est max ${total:.2f}  (budget cap ${a.budget:.2f})")
    if a.dry_run:
        return
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("Set OPENROUTER_API_KEY in the environment.")

    manifest = {"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "models": MODELS,
                "prompts": PROMPTS, "settings": SETTINGS, "budget_usd": a.budget, "seed": a.seed,
                "n_cheap": a.n_cheap, "n_top": a.n_top}
    json.dump(manifest, open(a.out + ".manifest.json", "w"), indent=2)

    budget, wlock, stop = Budget(a.budget), threading.Lock(), threading.Event()
    fout = open(a.out, "a")

    def work(job):
        if stop.is_set():
            return
        model, kind, c = job
        reserve, max_tokens = est_cost(job, prices)
        reserve *= 1.5  # headroom for token-estimate error
        if not budget.reserve(reserve):
            stop.set()
            return
        actual, rec = 0.0, None
        try:
            for attempt in range(3):
                try:
                    r = call(model, build_prompt(kind, c), max_tokens, key)
                    u = r.get("usage", {})
                    actual = float(u.get("cost") or (u.get("prompt_tokens", 0) * prices[model][0]
                                                     + u.get("completion_tokens", 0) * prices[model][1]))
                    rec = {"model": model, "served_model": r.get("model"), "prompt_type": kind,
                           "chunk_id": c["id"], "output": r["choices"][0]["message"]["content"],
                           "usage": u, "cost_usd": actual,
                           "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
                    break
                except (urllib.error.URLError, KeyError, TimeoutError):
                    time.sleep(2 ** attempt)
        finally:
            budget.settle(reserve, actual)
        if rec:
            with wlock:
                fout.write(json.dumps(rec) + "\n")
                fout.flush()

    with ThreadPoolExecutor(a.workers) as ex:
        list(ex.map(work, jobs))
    print(f"spent ${budget.spent:.2f}; stopped on budget: {stop.is_set()}")


if __name__ == "__main__":
    main()
