"""Step 13: extension sets. (a) DeepSeek V4.1 Flash as a fourth generator: 100 papers attacked with the same six attacks as Steps 7 and 9;
(b) a third field (economics, arXiv econ.*): human papers and the four generators' papers, clean + 50% sentence mixing + 10% typos.
python3 s13_ext_build.py ds_attacks | econ_attacks
"""
import argparse, json, random, re
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from common import *
import s7_attacks as S7, s9_adaptive as S9
rd = lambda f: [json.loads(l) for l in open(os.path.join(DATA, f))]

def ds_attacks(a):
    docs = [d for d in rd("machine_deepseek.jsonl") if len(d["text"].split()) >= 2400]; random.Random(11).shuffle(docs); docs = docs[:100]
    samp = pd.read_csv(os.path.join(DATA, "judge_sample.csv")); neg = set(samp[samp.generator == "human"].id); pools = S9.human_pool(neg)
    out1, out2 = os.path.join(DATA, "attacked_ds.jsonl"), os.path.join(DATA, "attacked2_ds.jsonl")
    def one(args):
        k, d = args; rows = S7.job((d, a.cap_usd, 900 + k)); rw = next((r["text"] for r in rows if r["cond"] == "rewrite"), None)
        orig = next(r for r in rows if r["cond"] == "orig"); orig.update(source=d["source"])
        rows2 = S9.job((orig, rw, pools["pmc" if str(d["source"]).startswith("PMC") else "arxiv"], a.cap_usd, 1300 + k))
        return rows, rows2
    with ThreadPoolExecutor(a.workers) as ex, open(out1, "w") as f1, open(out2, "w") as f2:
        for i, (r1, r2) in enumerate(ex.map(one, list(enumerate(docs)))):
            for r in r1: f1.write(json.dumps(r) + "\n")
            for r in r2: f2.write(json.dumps(r) + "\n")
            if i % 10 == 0: print(i, "/", len(docs), f"spend ${spend():.2f}", flush=True)

def econ_attacks(a):
    hum = rd("human_econ.jsonl"); rows = []; rng = random.Random(5)
    for g in ("gpt4o", "claude", "llama", "deepseek"):
        for d in rd(f"machine_econ_{g}.jsonl"):
            if len(d["text"].split()) < 2000: continue
            base = " ".join(d["text"].split()[:2400]); own = d["source"]
            pool = []
            for h in hum:
                if h["id"] == own: continue
                for s in S9.SENT.split(h["text"]):
                    n = len(s.split())
                    if 8 <= n <= 60 and s[:1].isupper(): pool.append(s.strip())
            for cond, text in (("orig", base), ("mix50", S9.mix(base, 0.5, pool, rng)), ("noise10", S9.noise(base, 0.1, rng))):
                rows.append(dict(id=d["id"], cond=cond, text=text, generator=g, source=own, label=1, field="econ"))
    with open(os.path.join(DATA, "attacked_econ.jsonl"), "w") as f:
        for r in rows: f.write(json.dumps(r) + "\n")
    print(len(rows), "econ machine documents")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("step", choices=["ds_attacks", "econ_attacks"]); ap.add_argument("--workers", type=int, default=12); ap.add_argument("--cap-usd", type=float, default=125.0)
    a = ap.parse_args(); {"ds_attacks": ds_attacks, "econ_attacks": econ_attacks}[a.step](a)
