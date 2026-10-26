"""Train a supervised detector on a train file and write per-document scores for a test file (higher = more likely machine).
python3 ext_train_score.py --model tfidf|roberta --train train.jsonl --test test.jsonl --out scores.csv   (jsonl rows: id, label, text)"""
import argparse, json
import numpy as np, pandas as pd
ap = argparse.ArgumentParser()
ap.add_argument("--model", choices=["tfidf", "roberta"], default="tfidf"); ap.add_argument("--train", required=True); ap.add_argument("--test", required=True); ap.add_argument("--out", required=True)
ap.add_argument("--hf-model", default="roberta-base"); ap.add_argument("--max-len", type=int, default=512); ap.add_argument("--epochs", type=int, default=2); ap.add_argument("--batch", type=int, default=16); ap.add_argument("--lr", type=float, default=2e-5)
a = ap.parse_args()
tr = pd.DataFrame([json.loads(l) for l in open(a.train)]); te = pd.DataFrame([json.loads(l) for l in open(a.test)])
if a.model == "tfidf":
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    v = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=100000, sublinear_tf=True)
    m = LogisticRegression(max_iter=2000, C=3.0).fit(v.fit_transform(tr.text), tr.label); s = m.predict_proba(v.transform(te.text))[:, 1]
else:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    torch.manual_seed(0); dev = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(a.hf_model); model = AutoModelForSequenceClassification.from_pretrained(a.hf_model, num_labels=2).to(dev)
    enc = lambda t: tok(list(t), truncation=True, max_length=a.max_len, padding=True, return_tensors="pt")
    opt = torch.optim.AdamW(model.parameters(), lr=a.lr, weight_decay=0.01); y = torch.tensor(tr.label.values); n = len(tr)
    steps = a.epochs * ((n + a.batch - 1) // a.batch)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda k: min(1.0, (k + 1) / (0.1 * steps)) * max(0.0, 1 - k / steps)); model.train()
    for ep in range(a.epochs):
        perm = np.random.RandomState(ep).permutation(n)
        for i in range(0, n, a.batch):
            idx = perm[i:i + a.batch]; b = enc(tr.text.values[idx]).to(dev)
            model(**b, labels=y[idx].to(dev)).loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); sched.step(); opt.zero_grad()
    model.eval(); out = []
    with torch.no_grad():
        for i in range(0, len(te), 32):
            b = enc(te.text.values[i:i + 32]).to(dev); out.append(torch.softmax(model(**b).logits, -1)[:, 1].float().cpu().numpy())
    s = np.concatenate(out)
pd.DataFrame(dict(id=te.id, score=s)).to_csv(a.out, index=False); print("trained on", len(tr), "scored", len(te))
