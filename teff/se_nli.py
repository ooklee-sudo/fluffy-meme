"""Entailment-clustered semantic entropy on the free-generation completions.

Follows the procedure of Farquhar et al. (2024): two completions share a
cluster if each entails the other given the question; the entropy is taken over
cluster frequencies (discrete form). Uses microsoft/deberta-large-mnli.

  python se_nli.py results/free_<model>.json
"""
import json
import sys
import time

import numpy as np
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from teff_core import TASKS, make_user

NLI = "microsoft/deberta-large-mnli"
tok = AutoTokenizer.from_pretrained(NLI)
nli = AutoModelForSequenceClassification.from_pretrained(NLI).eval()
ENT = [i for i, l in nli.config.id2label.items() if l.lower() == "entailment"][0]
cache = {}
n_calls = 0
t_nli = 0.0


def entails(q, a, b):
    global n_calls, t_nli
    if (q, a, b) in cache:
        return cache[(q, a, b)]
    t0 = time.perf_counter()
    enc = tok(f"{q} {a}", f"{q} {b}", return_tensors="pt", truncation=True,
              max_length=256)
    with torch.no_grad():
        lg = nli(**enc).logits[0]
    t_nli += time.perf_counter() - t0
    n_calls += 1
    r = int(lg.argmax()) == ENT
    cache[(q, a, b)] = r
    return r


def cluster(q, texts):
    clusters = []                                    # list of lists of indices
    for i, t in enumerate(texts):
        for c in clusters:
            r = texts[c[0]]
            if r == t or (entails(q, r, t) and entails(q, t, r)):
                c.append(i)
                break
        else:
            clusters.append([i])
    return clusters


def entropy_from(clusters, n):
    p = np.array([len(c) for c in clusters]) / n
    return float(-(p * np.log(p)).sum())


def exact_entropy(texts):
    vals, cnt = np.unique(texts, return_counts=True)
    p = cnt / len(texts)
    return float(-(p * np.log(p)).sum())


def boot_se(q, texts, B=200, seed=0):
    rng = np.random.default_rng(seed)
    n = len(texts)
    out = []
    for _ in range(B):
        pick = [texts[i] for i in rng.integers(0, n, n)]
        out.append(entropy_from(cluster(q, pick), n))
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))


if __name__ == "__main__":
    path = sys.argv[1]
    d = json.load(open(path))
    res = d["res"]
    out = {}
    for key, c in res.items():
        task = key.split("|")[0]
        q = make_user(task)
        texts = c["texts"]
        cl = cluster(q, texts)
        lo, hi = boot_se(q, texts)
        out[key] = dict(se_nli=entropy_from(cl, len(texts)), n_clusters=len(cl),
                        se_exact=exact_entropy(texts), boot_lo=lo, boot_hi=hi)
        print(key, out[key], flush=True)
    d["se"] = out
    d["nli_calls"] = n_calls
    d["nli_seconds"] = t_nli
    json.dump(d, open(path, "w"))
    print("NLI calls", n_calls, "seconds", round(t_nli, 1))
