"""Step 8: score attacked papers.
 local : count-based screen (trained on clean human + the other two generators, excluding the target AND Llama, the rewriter) and a TF-IDF screen.
 judge : Gemini 2.5 Pro on the edit(e=1), rewrite and hybrid(e=1) excerpts (first 2,000 tokens, markdown stripped).
 pod   : docs file for gpu_baselines.py / a RoBERTa scorer (written to data/attacked_docs.jsonl).
Negatives (human papers) for every AUC are the 200 human papers of the judge sample, unattacked.
python3 s8_attack_eval.py local | judge | pod-docs | report
"""
import argparse, json, os
import numpy as np, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from common import *
from s3_features import features
from s5_judges import PROMPT, excerpt, parse

EV = ["paren", "bracket", "semicolon", "quote", "marker", "passive", "nominal"]
CLUST = [f"rate_{e}" for e in EV] + [f"fano_mean_{e}" for e in EV] + [f"fano_slope_{e}" for e in EV]
RATES_DISP = [f"rate_{e}" for e in EV] + [f"disp_{e}" for e in EV]
att = lambda: [json.loads(l) for l in open(os.path.join(DATA, "attacked.jsonl"))]
samp = lambda: pd.read_csv(os.path.join(DATA, "judge_sample.csv"))

def local(a):
    A = att(); feats = pd.read_csv(os.path.join(DATA, "features.csv")); docs = {json.loads(l)["id"]: json.loads(l) for l in open(os.path.join(DATA, "docs.jsonl"))}
    hum_ids = set(samp()[samp().generator == "human"].id)
    rows = []
    for r in A:
        f = features(r["text"])
        if f: rows.append(dict(id=r["id"], cond=r["cond"], generator=r["generator"], **f))
    af = pd.DataFrame(rows); af.to_csv(os.path.join(DATA, "attacked_features.csv"), index=False)
    out = []
    for g in ("gpt4o", "claude", "llama"):
        train_gens = [x for x in ("gpt4o", "claude") if x != g]               # Llama (the rewriter) and the target are excluded
        tr = feats[(feats.generator == "human") | feats.generator.isin(train_gens)]
        tr = tr[~tr.source.isin(set(af[af.generator == g].id.str.split(":", n=1).str[1]) | set())]    # keep all human training papers
        te_h = feats[feats.id.isin(hum_ids)]
        for name, cols in (("screen_baseline", RATES_DISP), ("screen_clustering", CLUST)):
            m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000)).fit(tr[cols].values, tr.label.values)
            for cond, grp in af[af.generator == g].groupby("cond"):
                s = np.concatenate([m.predict_proba(te_h[cols].values)[:, 1], m.predict_proba(grp[cols].values)[:, 1]])
                y = np.concatenate([np.zeros(len(te_h)), np.ones(len(grp))])
                out.append(dict(detector=name, generator=g, cond=cond, auc=roc_auc_score(y, s), n=len(grp)))
    pd.DataFrame(out).to_csv(os.path.join(DATA, "attack_local_results.csv"), index=False); print(pd.DataFrame(out).pivot_table(index=["detector", "generator"], columns="cond", values="auc").round(3))

def judge(a):
    A = [r for r in att() if r["cond"] in ("orig", "edit1.0", "rewrite", "hybrid1.0")]; out = os.path.join(DATA, "attack_judge_scores.csv")
    done = set(); 
    if os.path.exists(out): done = {(r.id, r.cond) for r in pd.read_csv(out).itertuples()}
    jobs = [r for r in A if (r["id"], r["cond"]) not in done]; print(len(jobs), "judge calls")
    def one(r):
        t, c = chat("google/gemini-2.5-pro", [{"role": "user", "content": PROMPT.format(text=excerpt(r["text"]))}], max_tokens=8000, temperature=0.0, cap=a.cap_usd)
        return r["id"], r["cond"], parse(t), c
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(a.workers) as ex, open(out, "a") as f:
        if not done: f.write("id,cond,p_ai,cost\n")
        for i, c, p, cost in ex.map(one, jobs): f.write(f"{i},{c},{'' if p is None else p},{cost:.5f}\n"); f.flush()

def pod_docs(a):
    s = samp(); hum = set(s[s.generator == "human"].id); rows = []
    for l in open(os.path.join(DATA, "docs.jsonl")):
        d = json.loads(l)
        if d["id"] in hum: rows.append(dict(id=d["id"] + "|clean", cond="clean", source=d["source"], label=0, generator="human", text=d["text"]))
    for r in att(): rows.append(dict(id=r["id"] + "|" + r["cond"], cond=r["cond"], source=r["source"], label=1, generator=r["generator"], text=excerpt(r["text"])))
    with open(os.path.join(DATA, "attacked_docs.jsonl"), "w") as f:
        for r in rows: f.write(json.dumps(r) + "\n")
    print(len(rows), "documents for the pod")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("step", choices=["local", "judge", "pod-docs"]); ap.add_argument("--workers", type=int, default=10); ap.add_argument("--cap-usd", type=float, default=75.0)
    a = ap.parse_args(); {"local": local, "judge": judge, "pod-docs": pod_docs}[a.step](a)
