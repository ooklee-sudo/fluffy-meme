"""Judge (Gemini) on attacked machine papers versus clean human papers, and versus the same papers before the attack.
Usage: python3 judge_attack_eval.py <level>   (reads data/judge/gemini_<level>.jsonl, written by judge.py --input data/attack/<level>_judge.jsonl)"""
import sys, json, numpy as np
from sklearn.metrics import roc_auc_score
load = lambda p: [json.loads(l) for l in open(p, encoding="utf-8")]
key = {k["id"]: k for k in load("data/judge_key.jsonl")}
clean = {r["id"]: r for r in load("data/judge/gemini.jsonl")}
for level in sys.argv[1:]:
    att = {r["id"]: r for r in load(f"data/judge/gemini_{level}.jsonl")}
    print(f"\n== Gemini judge, attack level {level} ==\n{'target':8s}{'n':>5s}  clean AUC / flagged@50    attacked AUC / flagged@50")
    hum = [clean[i]["p_ai"] for i in clean if key[i]["source"] == "human" and clean[i]["p_ai"] is not None]
    for g in ("gpt4o", "claude", "llama"):
        ids = [i for i in att if key[i]["source"] == g and att[i]["p_ai"] is not None and i in clean and clean[i]["p_ai"] is not None]
        if not ids: continue
        c = [clean[i]["p_ai"] for i in ids]; a = [att[i]["p_ai"] for i in ids]
        row = []
        for m in (c, a):
            y = np.r_[np.zeros(len(hum)), np.ones(len(m))]; s = np.r_[hum, m]
            row.append(f"{roc_auc_score(y, s):.3f} / {np.mean(np.array(m) >= 50):.2f}")
        print(f"{g:8s}{len(ids):5d}   {row[0]:>22s}   {row[1]:>24s}")
