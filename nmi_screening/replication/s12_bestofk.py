"""Step 12: detector-in-the-loop attack. The attacker can query one detector's score (Fast-DetectGPT, scored on the pod) and keeps, for each paper,
the lowest-scoring of K candidates: K LLM rewrites (Llama 3.3 70B, temperature 1, alternating two prompts) or K random 50% sentence mixes.
This step writes the candidates (data/bestofk_cands.jsonl); select_bestofk() in s12_select.py picks the winner after pod scoring.
python3 s12_bestofk.py --k 6 [--gens gpt4o claude llama] [--workers 16] [--cap-usd 120]
"""
import argparse, json, random
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from common import *
from s7_attacks import REWRITE
from s9_adaptive import R2, human_pool, mix

def rw_candidate(text, k, cap):
    toks = text.split()[:2400]; out = []; prompt = REWRITE if k % 2 == 0 else R2
    for i in range(0, len(toks), 800):
        chunk = " ".join(toks[i:i + 800]); t, _ = chat("meta-llama/llama-3.3-70b-instruct", [{"role": "user", "content": prompt.format(n=len(toks[i:i + 800]), chunk=chunk)}], max_tokens=2000, temperature=1.0, cap=cap)
        if not t: return None
        out.append(t.strip())
    t = " ".join(out); return t if len(t.split()) >= 2000 else None

def job(args):
    r, pool, k, cap, seed = args; rows = []
    t = rw_candidate(r["text"], k, cap)
    if t: rows.append(dict(id=r["id"], kind="rw", k=k, text=t))
    rows.append(dict(id=r["id"], kind="mix", k=k, text=mix(r["text"], 0.5, pool, random.Random(seed * 100 + k))))
    for x in rows: x.update(generator=r["generator"], source=r["source"], label=1)
    return rows

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--k", type=int, default=6); ap.add_argument("--workers", type=int, default=16); ap.add_argument("--cap-usd", type=float, default=120.0)
    ap.add_argument("--src", default="attacked.jsonl"); ap.add_argument("--out", default="bestofk_cands.jsonl"); ap.add_argument("--limit", type=int, default=0); a = ap.parse_args()
    samp = pd.read_csv(os.path.join(DATA, "judge_sample.csv")); neg = set(samp[samp.generator == "human"].id); pools = human_pool(neg)
    orig = [json.loads(l) for l in open(os.path.join(DATA, a.src))]; orig = [r for r in orig if r["cond"] == "orig"]
    if a.limit: orig = orig[:a.limit]
    out = os.path.join(DATA, a.out); done = {(x["id"], x["k"]) for x in map(json.loads, open(out))} if os.path.exists(out) else set()
    jobs = [(r, pools["pmc" if str(r["source"]).startswith("PMC") else "arxiv"], k, a.cap_usd, 500 + j) for j, r in enumerate(orig) for k in range(a.k) if (r["id"], k) not in done]
    print(len(done), "candidate pairs done;", len(jobs), "to do", flush=True)
    with ThreadPoolExecutor(a.workers) as ex, open(out, "a") as f:
        futs = [ex.submit(job, j) for j in jobs]
        for n, fu in enumerate(as_completed(futs)):
            for x in fu.result(): f.write(json.dumps(x) + "\n")
            f.flush()
            if n % 20 == 0: print(n, "/", len(jobs), f"spend ${spend():.2f}", flush=True)
    print("done")
