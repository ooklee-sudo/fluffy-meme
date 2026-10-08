"""Mean event counts per 500 tokens before and after the LLM paraphrase attack (first 2,000 tokens; papers with >= 2,000 tokens in both versions)."""
import json, numpy as np
import features as F
from attack_paraphrase import clean
load = lambda p: [json.loads(l) for l in open(p, encoding="utf-8")]
key = {k["id"]: k for k in load("data/judge_key.jsonl")}
att = {r["id"]: r["text"] for r in load("data/attack/p2_full.jsonl")}
orig = {(g, r["human_id"]): r["text"] for g in ("gpt4o", "claude", "llama") for r in load(f"data/synthetic/{g}.jsonl")}
def rates(text):
    toks = text.split()[:2000]
    return None if len(toks) < 2000 else F.counts(" ".join(toks)).mean(0)
human = np.mean([h for h in (rates(r["text"]) for r in load("data/human.jsonl")) if h is not None], axis=0)
R = {}
for g in ("gpt4o", "claude", "llama"):
    o, a = [], []
    for i, t in att.items():
        k = key[i]
        if k["source"] != g: continue
        ro, ra = rates(" ".join(clean(orig[(g, k["source_id"])]))), rates(t)
        if ro is not None and ra is not None: o.append(ro); a.append(ra)
    R[g] = (np.mean(o, 0), np.mean(a, 0), len(o))
print("mean count per 500 tokens (human | original -> attacked) by target generator; n =", {g: R[g][2] for g in R})
print(f"{'event':14s}{'human':>8s}" + "".join(f"{g+' orig':>14s}{g+' att':>12s}" for g in R))
for j, n in enumerate(F.NAMES): print(f"{n:14s}{human[j]:8.2f}" + "".join(f"{R[g][0][j]:14.2f}{R[g][1][j]:12.2f}" for g in R))
