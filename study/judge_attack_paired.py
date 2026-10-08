"""Paired bootstrap: Gemini judge AUC after attack minus before attack, on the SAME machine papers (clean human judged papers as negatives)."""
import json, numpy as np
from sklearn.metrics import roc_auc_score
load = lambda p: [json.loads(l) for l in open(p, encoding="utf-8")]
key = {k["id"]: k for k in load("data/judge_key.jsonl")}
S = {n: {r["id"]: r["p_ai"] for r in load(f"data/judge/{f}.jsonl")} for n, f in (("clean", "gemini"), ("h1", "gemini_h1"), ("p", "gemini_p"))}
hum = [S["clean"][i] for i in S["clean"] if key[i]["source"] == "human" and S["clean"][i] is not None]
rng = np.random.RandomState(9)
print(f"{'target':8s}{'attack':>8s}{'n':>5s}   judge AUC before -> after     difference [95% CI]")
for g in ("gpt4o", "claude", "llama"):
    for lv in ("p", "h1"):
        ids = [i for i in S[lv] if key[i]["source"] == g and S[lv][i] is not None and S["clean"].get(i) is not None]
        b = np.array([S["clean"][i] for i in ids], float); a = np.array([S[lv][i] for i in ids], float); h = np.array(hum, float)
        def auc(m, hh): return roc_auc_score(np.r_[np.zeros(len(hh)), np.ones(len(m))], np.r_[hh, m])
        d0 = auc(a, h) - auc(b, h); d = []
        for _ in range(3000):
            mi = rng.randint(0, len(ids), len(ids)); hi = rng.randint(0, len(h), len(h)); d.append(auc(a[mi], h[hi]) - auc(b[mi], h[hi]))
        lo, up = np.percentile(d, [2.5, 97.5]); print(f"{g:8s}{lv:>8s}{len(ids):5d}   {auc(b, h):.3f} -> {auc(a, h):.3f}            {d0:+.3f} [{lo:+.3f}, {up:+.3f}]")
