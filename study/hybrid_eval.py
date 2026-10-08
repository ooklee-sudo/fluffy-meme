"""PRE-SPECIFIED hybrid attack: LLM rewrite (p2) followed by the feature-aware edit of attack_eval.py, on the same 300 machine papers.
Conditions: R = rewrite only; P = feature-aware edit only (e=1, original text); H0.5 / H1 = rewrite then edit with e = 0.5 / 1.
Detector: clustering screen, never trained on the target (and, in the second table, never on Llama, the rewriter).
Metrics: AUC and share detected at 5% FPR against all clean human papers."""
import json, zlib, numpy as np
import attack_eval as A
import score_attacked as S
from attack_paraphrase import clean
load = lambda p: [json.loads(l) for l in open(p, encoding="utf-8")]
rows = {r["id"]: r["text"] for r in load("data/attack/p2_full.jsonl")}
key = S.key; ORIG = S.ORIG
def rng(pid, tag): return np.random.RandomState(zlib.crc32(f"{pid}|{tag}".encode()))
def texts_for(g, cond):
    out = {}
    for i, t in rows.items():
        k = key[i]
        if k["source"] != g: continue
        sid = k["source_id"]
        if cond == "R": out[sid] = t
        elif cond == "P": out[sid] = A.attack(" ".join(clean(ORIG[(g, sid)])), 1.0, rng(sid, "P"))
        elif cond == "H0.5": out[sid] = A.attack(t, 0.5, rng(sid, "H0.5"))
        elif cond == "H1": out[sid] = A.attack(t, 1.0, rng(sid, "H1"))
    return out
CONDS = [("R", "rewrite only"), ("P", "edit only (e=1)"), ("H0.5", "rewrite + edit (e=0.5)"), ("H1", "rewrite + edit (e=1)")]
res = {}
for label, attacker in (("standard protocol", None), ("Llama (the rewriter) excluded from detector training", "llama")):
    print(f"\n== {label} ==")
    print(f"{'condition':26s}" + "".join(f"{g:>20s}" for g in ("gpt4o", "claude", "llama", "mixture")) + "   [AUC / detected at 5% FPR]")
    first = True
    for cond, name in CONDS:
        vals = {}
        for g in ("gpt4o", "claude", "llama"):
            excl = (attacker,) if (attacker and g != attacker) else ()
            (ac, dc, n), (aa, da, _) = S.run(g, texts_for(g, cond), excl); vals[g] = (ac, dc, aa, da)
        if first:
            print(f"{'original (no attack)':26s}" + "".join(f"{vals[g][0]:14.3f} / {vals[g][1]:.2f}" for g in vals) + f"{np.mean([v[0] for v in vals.values()]):14.3f} / {np.mean([v[1] for v in vals.values()]):.2f}"); first = False
        mix = (np.mean([v[2] for v in vals.values()]), np.mean([v[3] for v in vals.values()]))
        print(f"{name:26s}" + "".join(f"{vals[g][2]:14.3f} / {vals[g][3]:.2f}" for g in vals) + f"{mix[0]:14.3f} / {mix[1]:.2f}", flush=True)
        res[(label, cond)] = {g: vals[g][2:] for g in vals}
