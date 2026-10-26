"""Step 9: attacks aimed at probability-based detectors, applied to the same 300 machine papers.
 mix30 / mix50 : 30% / 50% of the sentences are replaced by sentences from human papers of the same field (not the test negatives, not the paper's own source).
 noise3 / noise10 : each word of length >= 4 gets a random typo (swap, drop or repeat a letter) with probability 3% / 10%.
 rewrite2 : the LLM rewrite of Step 7 is rewritten again by Llama 3.3 70B at temperature 1.0 with an instruction to change vocabulary and sentence structure.
Output data/attacked2.jsonl.   python3 s9_adaptive.py [--workers 16]
"""
import argparse, json, random, re
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from common import *

SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z“(\[])")
def human_pool(exclude_ids):
    pools = {"pmc": [], "arxiv": []}
    for l in open(os.path.join(DATA, "human.jsonl")):
        h = json.loads(l)
        if h["id"] in exclude_ids: continue
        for s in SENT.split(h["text"].replace("\n", " ")):
            n = len(s.split())
            if 8 <= n <= 60 and s[:1].isupper(): pools[h["source"]].append(s.strip())
    return pools

def mix(text, p, pool, rng):
    sents = SENT.split(" ".join(text.split())); k = int(round(p * len(sents)))
    for i in rng.sample(range(len(sents)), min(k, len(sents))):
        n = len(sents[i].split()); cand = [s for s in rng.sample(pool, 40) if 0.7 * n <= len(s.split()) <= 1.3 * n + 2]
        sents[i] = cand[0] if cand else rng.choice(pool)
    return " ".join(sents)

def typo(w, rng):
    i = rng.randrange(1, len(w) - 1); k = rng.randrange(3)
    return w[:i] + w[i + 1] + w[i] + w[i + 2:] if k == 0 and i + 2 <= len(w) - 0 and i + 1 < len(w) else (w[:i] + w[i + 1:] if k == 1 else w[:i] + w[i] + w[i:])
def noise(text, p, rng):
    return " ".join(typo(w, rng) if len(w) >= 4 and w.isalpha() and rng.random() < p else w for w in text.split())

R2 = ("Rewrite the following passage so that it uses clearly different vocabulary and sentence structure from the original, while keeping the meaning, the technical content "
      "and the citation markers. The result should be about {n} words long. Output only the rewritten passage.\n\n{chunk}")
def rewrite2(text, cap):
    toks = text.split()[:2400]; out = []
    for i in range(0, len(toks), 800):
        chunk = " ".join(toks[i:i + 800]); t, _ = chat("meta-llama/llama-3.3-70b-instruct", [{"role": "user", "content": R2.format(n=len(toks[i:i + 800]), chunk=chunk)}],
                                                     max_tokens=2000, temperature=1.0, cap=cap)
        if not t: return None
        out.append(t.strip())
    return " ".join(out)

def job(args):
    r, rw, pool, cap, seed = args; rng = random.Random(seed); base = r["text"]; rows = []
    for p in (0.3, 0.5): rows.append(dict(id=r["id"], cond=f"mix{int(p*100)}", text=mix(base, p, pool, rng)))
    for p in (0.03, 0.1): rows.append(dict(id=r["id"], cond=f"noise{int(p*100)}", text=noise(base, p, rng)))
    if rw:
        t = rewrite2(rw, cap)
        if t and len(t.split()) >= 2000: rows.append(dict(id=r["id"], cond="rewrite2", text=t))
    for x in rows: x.update(label=1, generator=r["generator"], source=r["source"])
    return rows

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=16); ap.add_argument("--cap-usd", type=float, default=80.0); a = ap.parse_args()
    samp = pd.read_csv(os.path.join(DATA, "judge_sample.csv")); neg = set(samp[samp.generator == "human"].id)
    att = [json.loads(l) for l in open(os.path.join(DATA, "attacked.jsonl"))]
    orig = {r["id"]: r for r in att if r["cond"] == "orig"}; rew = {r["id"]: r["text"] for r in att if r["cond"] == "rewrite"}
    pools = human_pool(neg)
    out = os.path.join(DATA, "attacked2.jsonl"); done = {json.loads(l)["id"] for l in open(out)} if os.path.exists(out) else set()
    jobs = [(r, rew.get(i), pools["pmc" if str(r["source"]).startswith("PMC") else "arxiv"], a.cap_usd, 300 + k) for k, (i, r) in enumerate(orig.items()) if i not in done]
    print(len(done), "done;", len(jobs), "to do", flush=True)
    with ThreadPoolExecutor(a.workers) as ex, open(out, "a") as f:
        for k, rows in enumerate(ex.map(job, jobs)):
            for x in rows: f.write(json.dumps(x) + "\n")
            if k % 25 == 0: print(k, "/", len(jobs), f"spend ${spend():.2f}", flush=True)
    print("done")
