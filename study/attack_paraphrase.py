"""LLM paraphrase attack on the 300 machine excerpts used in the judge comparison (100 per generator). Runs on your PC; needs only `requests`.
  set OPENROUTER_API_KEY=...
  python attack_paraphrase.py --level p1 --limit 3
Levels:  p1 = plain paraphrase;  p2 = rewrite so that it reads as if written by an experienced human researcher.
Each excerpt (cleaned exactly as for the judges, first 3,000 tokens) is rewritten in two chunks of 1,500 tokens and rejoined.
Outputs: data/attack/<level>_full.jsonl (id, text: used for the screen) and data/attack/<level>_judge.jsonl (id, text: first 2,000 tokens, input for judge.py).
Resumable; fails fast on key/credit errors. Default attacker is an open-weight model (cheap)."""
import argparse, json, os, re, time, threading, requests
from concurrent.futures import ThreadPoolExecutor

PROMPTS = {
 "p1": "Paraphrase the following passage from a scientific paper. Preserve the meaning, the technical content, and the approximate length. Return only the paraphrased passage.\n\nPassage:\n\n",
 "p2": ("Rewrite the following passage from a scientific paper so that it reads as if it were written by an experienced human researcher rather than by an AI "
        "model: vary sentence length and structure, use the natural discourse habits of academic prose, and keep the meaning, the technical content, and the "
        "approximate length. Return only the rewritten passage.\n\nPassage:\n\n"),
}
def clean(t):          # identical to make_judge_input.clean, with whitespace tokenization
    t = re.sub(r"(?m)^\s*#{1,6}\s.*$", " ", t)
    t = re.sub(r"(?m)^\s*(Introduction|Methods|Results|Discussion and Conclusion|Discussion)\s*$", " ", t)
    t = re.sub(r"[*_`]{1,3}", "", t); t = re.sub(r"(?m)^\s*[-•]\s+", "", t)
    return t.split()

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--level", required=True, choices=list(PROMPTS)); ap.add_argument("--model", default="meta-llama/llama-3.3-70b-instruct")
    ap.add_argument("--limit", type=int, default=0); ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    key = (os.environ.get("OPENROUTER_API_KEY") or "").strip().strip('"').strip("'").strip()
    print(f"key loaded: {len(key)} chars, starts with {key[:6]!r}", flush=True)
    if not key.isascii() or len(key) < 40: raise SystemExit("The key looks wrong. Set OPENROUTER_API_KEY to your REAL key (no placeholder text, no spaces).")
    kmap = [json.loads(l) for l in open("data/judge_key.jsonl", encoding="utf-8")]
    kmap = [k for k in kmap if k["source"] != "human"]
    texts = {}
    for g in {k["source"] for k in kmap}:
        for l in open(f"data/synthetic/{g}.jsonl", encoding="utf-8"):
            r = json.loads(l); texts[(g, r["human_id"])] = r["text"]
    os.makedirs("data/attack", exist_ok=True)
    fo, jo = f"data/attack/{a.level}_full.jsonl", f"data/attack/{a.level}_judge.jsonl"
    done = {json.loads(l)["id"] for l in open(fo, encoding="utf-8")} if os.path.exists(fo) else set()
    todo = [k for k in kmap if k["id"] not in done][: a.limit or None]
    print(f"already done: {len(done)}; to rewrite: {len(todo)} with {a.model}, level {a.level}", flush=True)
    lock = threading.Lock(); n = [0]

    def rewrite(chunk):
        for attempt in range(10):
            try:
                r = requests.post("https://openrouter.ai/api/v1/chat/completions", timeout=300, headers={"Authorization": f"Bearer {key}"},
                                  json={"model": a.model, "temperature": 0.7, "max_tokens": 3500, "messages": [{"role": "user", "content": PROMPTS[a.level] + chunk}]})
                if r.status_code != 200: raise RuntimeError(f"HTTP {r.status_code}: {r.text[:300]}")
                out = r.json()["choices"][0]["message"].get("content") or ""
                if len(out.split()) < 0.5 * len(chunk.split()): raise RuntimeError("answer too short")
                return out.strip(), r.json().get("usage", {})
            except Exception as e:
                if any(c in str(e)[:12] for c in ("401", "402", "403")): print("FATAL (key/credit problem), stopping:", str(e)[:300], flush=True); os._exit(1)
                wait = 20 if "429" in str(e) else min(2 ** attempt * 3, 60); print(f"  wait {wait}s ({str(e)[:70]})", flush=True); time.sleep(wait)
        raise RuntimeError("giving up")

    def work(k):
        toks = clean(texts[(k["source"], k["source_id"])])[:3000]; t0 = time.time(); parts, cost = [], 0.0
        for i in range(0, len(toks), 1500):
            out, u = rewrite(" ".join(toks[i:i + 1500])); parts.append(out); cost += u.get("cost", 0) or 0
        full = " ".join(parts); j = " ".join(full.split()[:2000])
        with lock:
            open(fo, "a", encoding="utf-8").write(json.dumps(dict(id=k["id"], text=full, seconds=time.time() - t0, cost=cost), ensure_ascii=False) + "\n")
            open(jo, "a", encoding="utf-8").write(json.dumps(dict(id=k["id"], text=j), ensure_ascii=False) + "\n")
            n[0] += 1; print(f"{n[0]}/{len(todo)} {k['id']} {len(full.split())} words {time.time()-t0:.0f}s", flush=True)
    with ThreadPoolExecutor(max_workers=a.workers) as ex: list(ex.map(work, todo))
