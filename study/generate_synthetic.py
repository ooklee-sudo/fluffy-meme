"""Generate synthetic papers locally. Keys are read from environment variables, never from files.
  set OPENAI_API_KEY=...      python generate_synthetic.py --provider openai    --model gpt-4o --out data/synthetic/gpt4o.jsonl
  set ANTHROPIC_API_KEY=...   python generate_synthetic.py --provider anthropic --model <claude-model-id> --out data/synthetic/claude.jsonl
  set OPENROUTER_API_KEY=...  python generate_synthetic.py --provider openrouter --model openai/gpt-4o --out data/synthetic/gpt4o.jsonl
  set TOGETHER_API_KEY=...    python generate_synthetic.py --provider together  --model <model-id> --out data/synthetic/llama3.jsonl
Resumable: re-run the same command and finished prompts are skipped. Use --limit 20 for a cheap trial."""
import argparse, json, os, time, requests

ap = argparse.ArgumentParser()
ap.add_argument("--provider", required=True, choices=["openai", "anthropic", "together", "openrouter"])
ap.add_argument("--model", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--prompts", default="data/prompts.jsonl"); ap.add_argument("--limit", type=int, default=0); ap.add_argument("--workers", type=int, default=1)
a = ap.parse_args()
KEY = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "together": "TOGETHER_API_KEY", "openrouter": "OPENROUTER_API_KEY"}[a.provider]
key = (os.environ.get(KEY) or "").strip().strip('"').strip("'").strip()   # tolerate stray spaces/quotes from cmd `set`
if not key: raise SystemExit(f"Set {KEY} first (e.g. `set {KEY}=...` in cmd).")
print(f"key loaded: {len(key)} chars, starts with {key[:6]!r}", flush=True)
if not key.isascii() or len(key) < 40:
    raise SystemExit(f"The key looks wrong ({len(key)} chars, non-ASCII={not key.isascii()}). Replace the placeholder with your REAL key: set {KEY}=sk-or-v1-xxxxxxxx (no Korean text, no spaces).")

def call(prompt):
    if a.provider == "anthropic":
        r = requests.post("https://api.anthropic.com/v1/messages", timeout=300,
            headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
            json={"model": a.model, "max_tokens": 6000, "messages": [{"role": "user", "content": prompt}]})
        if r.status_code != 200: raise RuntimeError(f"HTTP {r.status_code}: {r.text[:500]}")
        j = r.json(); return "".join(b.get("text", "") for b in j["content"]), j["usage"]
    url = {"openai": "https://api.openai.com/v1/chat/completions", "together": "https://api.together.xyz/v1/chat/completions",
           "openrouter": "https://openrouter.ai/api/v1/chat/completions"}[a.provider]
    r = requests.post(url, timeout=300, headers={"Authorization": f"Bearer {key}"},
        json={"model": a.model, "max_tokens": 6000, "messages": [{"role": "user", "content": prompt}]})
    if r.status_code != 200: raise RuntimeError(f"HTTP {r.status_code}: {r.text[:500]}")
    j = r.json(); return j["choices"][0]["message"]["content"], j["usage"]

os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
done = {json.loads(l)["human_id"] for l in open(a.out, encoding="utf-8")} if os.path.exists(a.out) else set()
rows = [json.loads(l) for l in open(a.prompts, encoding="utf-8")]
import random; random.Random(2024).shuffle(rows)   # fixed seed: any --limit is a random subset across fields
rows = [r for r in rows if r["human_id"] not in done][: a.limit or None]
print(f"already done: {len(done)}", flush=True)
SECTIONS = ["Introduction (background, gap, research question, contributions)",
            "Methods (data, design, procedures, statistical analysis)",
            "Results (main quantitative findings, with specific numbers)",
            "Discussion and Conclusion (interpretation, limitations, implications)"]

def call_patient(p):
    """Retry each section call on its own; wait out rate limits (429) instead of discarding finished sections."""
    for attempt in range(12):
        try:
            return call(p)
        except Exception as e:
            if any(c in str(e)[:12] for c in ("401", "402", "403")):
                print("FATAL (key/credit problem), stopping:", str(e)[:300], flush=True); os._exit(1)
            wait = 20 if "429" in str(e) else min(2 ** attempt * 3, 60)
            print(f"  wait {wait}s ({str(e)[:60]})", flush=True); time.sleep(wait)
    raise RuntimeError("giving up on this section")

def one_paper(prompt):
    """One call per section, concatenated: a single call yields only ~800 words, too short for the analysis."""
    parts, t0, tot = [], time.time(), {}
    for sec in SECTIONS:
        p = (prompt + f"\n\nWrite ONLY the {sec} section of this paper, about 900 words, as continuous academic prose "
             "with in-text citations. Start with the section title on its own line. Do not write other sections or a reference list.")
        t1 = time.time()
        print(f"  requesting: {sec.split(' ')[0]} ...", flush=True)
        text, usage = call_patient(p); parts.append(text.strip())
        print(f"  got {sec.split(' ')[0]}: {len(text.split())} words in {time.time()-t1:.0f}s", flush=True)
        for k, v in usage.items():
            if isinstance(v, (int, float)): tot[k] = tot.get(k, 0) + v
    return "\n\n".join(parts), tot, time.time() - t0

import threading
from concurrent.futures import ThreadPoolExecutor
lock = threading.Lock(); counter = [0]

def work(r):
    for attempt in range(4):
        try:
            text, usage, dt = one_paper(r["prompt"]); break
        except Exception as e:
            print("retry", attempt, e, flush=True); time.sleep(2 ** attempt * 3)
    else:
        return
    with lock:
        with open(a.out, "a", encoding="utf-8") as f:
            f.write(json.dumps(dict(human_id=r["human_id"], model=a.model, prompt_level=r["prompt_level"],
                                    text=text, seconds=dt, usage=usage), ensure_ascii=False) + "\n")
        counter[0] += 1
        print(f"{counter[0]}/{len(rows)} {r['human_id']} {dt:.0f}s {len(text.split())} words", flush=True)

print(f"{len(rows)} papers to generate with {a.model} (workers={a.workers})", flush=True)
with ThreadPoolExecutor(max_workers=a.workers) as ex:
    list(ex.map(work, rows))
