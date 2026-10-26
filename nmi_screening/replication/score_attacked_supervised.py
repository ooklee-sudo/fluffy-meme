"""Supervised detectors scored on attacked papers. For each target generator g: train on clean documents (human papers NOT in the judge sample, plus machine papers of the
other generators, excluding g and Llama, the rewriter, and excluding papers whose source is in the judge sample); score the 200 unattacked human negatives and the
attacked papers of g. Writes AUC per condition.
python3 score_attacked_supervised.py --model tfidf|roberta --train docs.jsonl --attacked attacked_docs.jsonl --sample judge_sample.csv --out out.csv
"""
import argparse, json
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
ap = argparse.ArgumentParser()
ap.add_argument("--model", choices=["tfidf", "roberta"], default="tfidf"); ap.add_argument("--train", required=True); ap.add_argument("--attacked", required=True)
ap.add_argument("--sample", required=True); ap.add_argument("--out", required=True); ap.add_argument("--hf-model", default="roberta-base")
ap.add_argument("--max-len", type=int, default=512); ap.add_argument("--epochs", type=int, default=2); ap.add_argument("--batch", type=int, default=16); ap.add_argument("--lr", type=float, default=2e-5)
a = ap.parse_args()
train = pd.DataFrame([json.loads(l) for l in open(a.train)]); att = pd.DataFrame([json.loads(l) for l in open(a.attacked)])
samp = pd.read_csv(a.sample); hold_h = set(samp[samp.generator == "human"].id)
test_src = {g: set(i.split(":", 1)[1] for i in samp[samp.generator == g].id) for g in ("gpt4o", "claude", "llama")}

def fit_predict(tr, te_texts):
    if a.model == "tfidf":
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        v = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=100000, sublinear_tf=True)
        m = LogisticRegression(max_iter=2000, C=3.0).fit(v.fit_transform(tr.text), tr.label); return m.predict_proba(v.transform(te_texts))[:, 1]
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    torch.manual_seed(0); dev = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(a.hf_model); model = AutoModelForSequenceClassification.from_pretrained(a.hf_model, num_labels=2).to(dev)
    enc = lambda t: tok(list(t), truncation=True, max_length=a.max_len, padding=True, return_tensors="pt")
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=0.01); y = torch.tensor(tr.label.values); n = len(tr)
    steps = a.epochs * ((n + a.batch - 1) // a.batch)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / (0.1 * steps)) * max(0.0, 1 - s / steps)); model.train()
    for ep in range(a.epochs):
        perm = np.random.RandomState(ep).permutation(n)
        for i in range(0, n, a.batch):
            idx = perm[i:i + a.batch]; b = enc(tr.text.values[idx]).to(dev)
            model(**b, labels=y[idx].to(dev)).loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); sched.step(); opt.zero_grad()
    model.eval(); out = []
    with torch.no_grad():
        for i in range(0, len(te_texts), 32):
            b = enc(te_texts[i:i + 32]).to(dev); out.append(torch.softmax(model(**b).logits, -1)[:, 1].float().cpu().numpy())
    return np.concatenate(out)

rows = []
neg = att[att.label == 0]
for g in ("gpt4o", "claude", "llama"):
    # exclude: the human negatives, every document whose source paper is a test paper of this target generator, the target generator and Llama (the rewriter)
    tr = train[~train.id.isin(hold_h) & ~train.source.isin(test_src[g]) & ((train.generator == "human") | (~train.generator.isin([g, "llama"])))]
    pos = att[(att.label == 1) & (att.generator == g)]; te = pd.concat([neg, pos]).reset_index(drop=True)
    s = fit_predict(tr, te.text.values); te["score"] = s
    for cond, grp in pos.groupby("cond"):
        m = te[(te.label == 0) | (te.cond == cond)]
        rows.append(dict(detector=a.model, generator=g, cond=cond, auc=roc_auc_score(m.label, m.score), n=len(grp)))
    print(g, "trained on", len(tr), "documents", flush=True)
r = pd.DataFrame(rows); r.to_csv(a.out, index=False)
print(r.pivot_table(index=["detector", "generator"], columns="cond", values="auc").round(3).to_string())
