"""Step 5: zero-shot LLM judges. 500 excerpts (200 human papers: 120 medicine + 80 computer science; 100 papers from each generator),
random order, opaque identifiers, first 2,000 tokens, markdown symbols and bare section titles removed. Each judge (GPT-4o, Gemini 2.5 Pro)
is asked at temperature 0 for the probability (0-100) that the excerpt was written by an AI language model. Output data/judge_scores.csv.
python3 s5_judges.py [--workers 8] [--cap-usd 60]
"""
import argparse, json, os, random, re
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from common import *

JUDGES = {"gpt4o": ("openai/gpt-4o-2024-11-20", 600, False), "gemini": ("google/gemini-2.5-pro", 8000, False)}
PROMPT = ("Below is an excerpt from a scientific paper. Estimate the probability that it was written by an AI language model "
          "(for example ChatGPT, Claude or Llama) rather than by a human author. Answer with a single number from 0 to 100, where 0 means "
          "certainly human-written and 100 means certainly AI-written. Output only the number.\n\nExcerpt:\n\n{text}")

def clean(text):
    text = re.sub(r"[#*`_]+", "", text)
    lines = [l for l in text.split("\n") if not re.fullmatch(r"\s*(\d+\.?\s*)?(Introduction|Methods?|Results?|Discussion|Conclusions?|Background|Abstract|Discussion and Conclusion)\s*:?\s*", l, re.I)]
    return "\n".join(lines)

def excerpt(text): return " ".join(clean(text).split()[:2000])

def parse(t):
    m = re.findall(r"\d+(?:\.\d+)?", t or "")
    return float(m[-1]) if m and 0 <= float(m[-1]) <= 100 else None

def call(args):
    jname, row, cap = args
    model, mt, _ = JUDGES[jname]
    t, c = chat(model, [{"role": "user", "content": PROMPT.format(text=row["excerpt"])}], max_tokens=mt, temperature=0.0, cap=cap)
    return dict(id=row["id"], judge=jname, raw=(t or "")[-60:], p_ai=parse(t), cost=c)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=8); ap.add_argument("--cap-usd", type=float, default=60.0); a = ap.parse_args()
    rng = random.Random(5); docs = []
    human = [json.loads(l) for l in open(os.path.join(DATA, "human.jsonl"))]
    pmc = [h for h in human if h["source"] == "pmc"]; arx = [h for h in human if h["source"] == "arxiv"]
    for h in rng.sample(pmc, 120) + rng.sample(arx, 80): docs.append(dict(id=h["id"], generator="human", excerpt=excerpt(h["text"])))
    for g in ("gpt4o", "claude", "llama"):
        ms = [json.loads(l) for l in open(os.path.join(DATA, f"machine_{g}.jsonl"))]
        for m in rng.sample(ms, min(100, len(ms))): docs.append(dict(id=m["id"], generator=g, excerpt=excerpt(m["text"])))
    rng.shuffle(docs)
    for i, d in enumerate(docs): d["oid"] = f"x{i:03d}"
    pd.DataFrame([{k: d[k] for k in ("oid", "id", "generator")} for d in docs]).to_csv(os.path.join(DATA, "judge_sample.csv"), index=False)
    out = os.path.join(DATA, "judge_scores.csv"); done = set()
    if os.path.exists(out): done = {(r.id, r.judge) for r in pd.read_csv(out).itertuples()}
    jobs = [(j, dict(id=d["id"], excerpt=d["excerpt"]), a.cap_usd) for j in JUDGES for d in docs if (d["id"], j) not in done]
    print(len(docs), "excerpts;", len(jobs), "calls", flush=True); first = not os.path.exists(out)
    with ThreadPoolExecutor(a.workers) as ex, open(out, "a") as f:
        if first: f.write("id,judge,p_ai,cost,raw\n")
        for r in ex.map(call, jobs):
            f.write(f"{r['id']},{r['judge']},{'' if r['p_ai'] is None else r['p_ai']},{r['cost']:.5f},{json.dumps(r['raw'])}\n"); f.flush()
    print("done; total spend", round(spend(), 2))
