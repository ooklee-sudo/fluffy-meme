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
ap.add_argument("--prompts", default="data/prompts.jsonl"); ap.add_argument("--limit", type=int, default=0)
a = ap.parse_args()
KEY = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "together": "TOGETHER_API_KEY", "openrouter": "OPENROUTER_API_KEY"}[a.provider]
key = os.environ.get(KEY)
if not key: raise SystemExit(f"Set {KEY} first (e.g. `set {KEY}=...` in cmd).")

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
done = {json.loads(l)["human_id"] for l in open(a.out)} if os.path.exists(a.out) else set()
rows = [json.loads(l) for l in open(a.prompts)]
import random; random.Random(2024).shuffle(rows)   # fixed seed: any --limit is a random subset across fields
rows = [r for r in rows if r["human_id"] not in done][: a.limit or None]
SECTIONS = ["Introduction (background, gap, research question, contributions)",
            "Methods (data, design, procedures, statistical analysis)",
            "Results (main quantitative findings, with specific numbers)",
            "Discussion and Conclusion (interpretation, limitations, implications)"]

def one_paper(prompt):
    """One call per section, concatenated: a single call yields only ~800 words, too short for the analysis."""
    parts, t0, tot = [], time.time(), {}
    for sec in SECTIONS:
        p = (prompt + f"\n\nWrite ONLY the {sec} section of this paper, about 900 words, as continuous academic prose "
             "with in-text citations. Start with the section title on its own line. Do not write other sections or a reference list.")
        text, usage = call(p); parts.append(text.strip())
        for k, v in usage.items():
            if isinstance(v, (int, float)): tot[k] = tot.get(k, 0) + v
    return "\n\n".join(parts), tot, time.time() - t0

for i, r in enumerate(rows, 1):
    for attempt in range(4):
        try:
            text, usage, dt = one_paper(r["prompt"]); break
        except Exception as e:
            print("retry", attempt, e); time.sleep(2 ** attempt * 3)
    else:
        continue
    with open(a.out, "a", encoding="utf-8") as f:
        f.write(json.dumps(dict(human_id=r["human_id"], model=a.model, prompt_level=r["prompt_level"],
                                text=text, seconds=dt, usage=usage), ensure_ascii=False) + "\n")
    print(f"{i}/{len(rows)} {r['human_id']} {dt:.0f}s {len(text.split())} words", flush=True)
