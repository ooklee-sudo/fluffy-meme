"""Supervised detector baselines with the study's cross-generator protocol.

Input : JSONL, one document per line: {"id", "source" (id of the human source paper; keeps a paper and its machine versions in one fold),
        "label" (0 human, 1 machine), "generator" ("human", "gpt4o", "claude", "llama"), "text"}.
Protocol: for each target generator g, 5-fold CV grouped by source paper. Training data = human papers + machine papers of all
        OTHER generators (the generator is never seen); test data = held-out human papers + papers of g. Reports AUC with a
        bootstrap interval, plus per-document scores.
Models : roberta (fine-tuned transformer on the first --max-len tokens; needs a GPU for the default roberta-base) and
        tfidf (word n-gram logistic regression; CPU).

pip install torch transformers accelerate scikit-learn pandas
python3 supervised_baselines.py --data docs.jsonl --model roberta --out roberta_scores.csv   # on a GPU
python3 supervised_baselines.py --data docs.jsonl --model tfidf --out tfidf_scores.csv        # CPU
"""
import argparse, json
import numpy as np, pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold

ap = argparse.ArgumentParser()
ap.add_argument("--data", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--model", choices=["roberta", "tfidf"], default="tfidf")
ap.add_argument("--hf-model", default="roberta-base"); ap.add_argument("--max-len", type=int, default=512)
ap.add_argument("--epochs", type=int, default=2); ap.add_argument("--batch", type=int, default=16); ap.add_argument("--lr", type=float, default=2e-5)
ap.add_argument("--folds", type=int, default=5); ap.add_argument("--limit", type=int, default=0); ap.add_argument("--seed", type=int, default=0)
a = ap.parse_args()
df = pd.DataFrame([json.loads(l) for l in open(a.data)])
if a.limit: df = df.sample(min(a.limit, len(df)), random_state=a.seed).reset_index(drop=True)
gens = [g for g in df.generator.unique() if g != "human"]

def fit_predict_tfidf(tr, te):
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    v = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=100000, sublinear_tf=True)
    X = v.fit_transform(tr.text); m = LogisticRegression(max_iter=2000, C=3.0).fit(X, tr.label)
    return m.predict_proba(v.transform(te.text))[:, 1]

def fit_predict_roberta(tr, te):
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    torch.manual_seed(a.seed); dev = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(a.hf_model)
    model = AutoModelForSequenceClassification.from_pretrained(a.hf_model, num_labels=2).to(dev)
    enc = lambda texts: tok(list(texts), truncation=True, max_length=a.max_len, padding=True, return_tensors="pt")
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=0.01)
    y = torch.tensor(tr.label.values); n = len(tr); steps = a.epochs * ((n + a.batch - 1) // a.batch); step = 0
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / (0.1 * steps)) * max(0.0, 1 - s / steps))
    model.train()
    for ep in range(a.epochs):
        perm = np.random.RandomState(a.seed + ep).permutation(n)
        for i in range(0, n, a.batch):
            idx = perm[i:i + a.batch]; b = enc(tr.text.values[idx]).to(dev)
            loss = model(**b, labels=y[idx].to(dev)).loss; loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); sched.step(); opt.zero_grad()
    model.eval(); out = []
    with torch.no_grad():
        for i in range(0, len(te), a.batch * 2):
            b = enc(te.text.values[i:i + a.batch * 2]).to(dev)
            out.append(torch.softmax(model(**b).logits, -1)[:, 1].float().cpu().numpy())
    return np.concatenate(out)

fp = fit_predict_roberta if a.model == "roberta" else fit_predict_tfidf
rows = []
for g in gens:
    gkf = GroupKFold(n_splits=a.folds)
    for k, (tri, tei) in enumerate(gkf.split(df, df.label, groups=df.source)):
        tr = df.iloc[tri]; te = df.iloc[tei]
        tr = tr[(tr.generator == "human") | (tr.generator != g)]          # target generator is never trained on
        te = te[(te.generator == "human") | (te.generator == g)]
        if te.label.nunique() < 2 or tr.label.nunique() < 2: continue
        s = fp(tr, te)
        rows += [dict(target=g, fold=k, id=i, label=l, score=float(x)) for i, l, x in zip(te.id, te.label, s)]
        print(g, "fold", k, "n_train", len(tr), "n_test", len(te), flush=True)
res = pd.DataFrame(rows); res.to_csv(a.out, index=False)
rng = np.random.default_rng(0)
for g in gens:
    r = res[res.target == g]
    if r.label.nunique() < 2: continue
    auc = roc_auc_score(r.label, r.score)
    bs = []
    for _ in range(1000):
        i = rng.integers(0, len(r), len(r)); rr = r.iloc[i]
        if rr.label.nunique() == 2: bs.append(roc_auc_score(rr.label, rr.score))
    print(f"{a.model} unseen-generator AUC for {g}: {auc:.3f} [{np.percentile(bs,2.5):.3f}, {np.percentile(bs,97.5):.3f}] (n={len(r)})")
