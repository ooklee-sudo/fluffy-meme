"""Step 10: does the TF-IDF baseline lean on structural artifacts (arXiv header, figure/table/citation/year tokens, length)?
Variants of the same classifier (grouped 5-fold by source paper, and leave-one-generator-out):
 raw        : words+bigrams of the first 2,000 words
 clean      : header before 'Abstract' removed, digits and artifact lexicon (fig, figure, table, et, al, university, arxiv, cs, abstract, ...) removed
 function   : only English stop words kept (content/topic and most artifacts gone)
python3 s10_artifact_control.py
"""
import json, re, os
import numpy as np, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from common import DATA
D = pd.DataFrame([json.loads(l) for l in open(os.path.join(DATA, "docs.jsonl"))])
ART = set("fig figure figures table tables et al university arxiv cs abstract eq equation appendix proceedings conference ieee acm doi http https www com org pp vol".split())
def first(t, n=2000): return " ".join(t.split()[:n])
def clean(t):
    m = re.search(r"abstract", t[:3000], re.I); t = t[m.end():] if m else t
    t = re.sub(r"\d+", " ", t.lower()); w = re.findall(r"[a-z]+", t)
    return " ".join(x for x in w if x not in ART)[:]
def function(t): return " ".join(w for w in re.findall(r"[a-z]+", t.lower()) if w in ENGLISH_STOP_WORDS)
V = {"raw": lambda t: first(t), "clean": lambda t: first(clean(t)), "function": lambda t: first(function(t))}
def fit_pred(tr, te):
    v = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=100000, sublinear_tf=True)
    m = LogisticRegression(max_iter=2000, C=3.0).fit(v.fit_transform(tr.x), tr.label); return m.predict_proba(v.transform(te.x))[:, 1]
rows = []
for name, f in V.items():
    D["x"] = D.text.map(f)
    for g in ("gpt4o", "claude", "llama"):
        S = D[(D.generator == "human") | (D.generator == g)].reset_index(drop=True)
        p = np.zeros(len(S))
        for tr, te in GroupKFold(5).split(S, S.label, S.source): p[te] = fit_pred(S.iloc[tr], S.iloc[te])
        rows.append(dict(variant=name, protocol="grouped-cv", generator=g, auc=roc_auc_score(S.label, p)))
        others = [x for x in ("gpt4o", "claude", "llama") if x != g]                      # unseen generator: train on the other two
        hs = D[D.generator == "human"]; srcs = list(hs.source.unique()); rng = np.random.RandomState(0); rng.shuffle(srcs); half = set(srcs[:len(srcs) // 2])
        tr = D[(D.generator.isin(others) | (D.generator == "human")) & ~D.source.isin(half)]; te = D[((D.generator == g) | (D.generator == "human")) & D.source.isin(half)]
        rows.append(dict(variant=name, protocol="unseen-generator", generator=g, auc=roc_auc_score(te.label, fit_pred(tr, te))))
R = pd.DataFrame(rows); R.to_csv(os.path.join(DATA, "artifact_control_results.csv"), index=False)
print(R.pivot_table(index=["protocol", "generator"], columns="variant", values="auc").round(3)[["raw", "clean", "function"]])
