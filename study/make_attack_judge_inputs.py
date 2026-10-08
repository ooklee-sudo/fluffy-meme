"""Judge inputs for the edit-based attacks, same 300 machine papers and ids as p2 (first 2,000 tokens of each attacked paper).
  h1 = LLM rewrite (p2) then feature-aware edit (e=1);  p = feature-aware edit only (e=1) on the original cleaned text.
Seeds are deterministic (crc32), identical to hybrid_eval.py, so the judged texts are exactly the ones the screen was scored on."""
import json, zlib, numpy as np
import attack_eval as A
from attack_paraphrase import clean
load = lambda p: [json.loads(l) for l in open(p, encoding="utf-8")]
key = {k["id"]: k for k in load("data/judge_key.jsonl")}
rows = {r["id"]: r["text"] for r in load("data/attack/p2_full.jsonl")}
ORIG = {(g, r["human_id"]): r["text"] for g in ("gpt4o", "claude", "llama") for r in load(f"data/synthetic/{g}.jsonl")}
rng = lambda pid, tag: np.random.RandomState(zlib.crc32(f"{pid}|{tag}".encode()))
out = {"h1": [], "p": []}
for i, t in rows.items():
    g, sid = key[i]["source"], key[i]["source_id"]
    h1 = A.attack(t, 1.0, rng(sid, "H1")); p = A.attack(" ".join(clean(ORIG[(g, sid)])), 1.0, rng(sid, "P"))
    out["h1"].append(dict(id=i, text=" ".join(h1.split()[:2000]))); out["p"].append(dict(id=i, text=" ".join(p.split()[:2000])))
for lvl, L in out.items():
    with open(f"data/attack/{lvl}_judge.jsonl", "w", encoding="utf-8") as f:
        for r in L: f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(lvl, len(L), "excerpts; median words", int(np.median([len(r["text"].split()) for r in L])))
