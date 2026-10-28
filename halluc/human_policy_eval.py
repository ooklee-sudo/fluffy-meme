"""Allocation policies scored directly against HUMAN labels (FActScore annotations), no LLM judge in the loop.

Unit = annotated sentence with >= 1 S/NS human fact (IR ignored); event = the sentence has an NS fact. Risk model features
come only from what a verifier sees for free: lead-sentence indicator, relative position (and its square), and optionally the
sentence-text content features of alloc_eval. (No rarity: the entity popularity measure is not available for these entities.)
5-fold cross-fitting over documents; gain = share of all human-labelled errors caught by the static policy minus uniform.
"""
import argparse
import json
import os

import numpy as np

import alloc_eval as ae

SOURCES = ("InstructGPT", "ChatGPT", "PerplexityAI")


def build(labeled_dir, src, content, min_units=6):
    docs = []
    for line in open(os.path.join(labeled_dir, src + ".jsonl")):
        r = json.loads(line)
        sents, y = [], []
        for a in r.get("annotations") or []:
            labs = [f["label"] for f in (a.get("human-atomic-facts") or []) if f.get("label") in ("S", "NS")]
            if labs:
                sents.append(a["text"])
                y.append(int("NS" in labs))
        n = len(y)
        if n < min_units:
            continue
        rank = np.arange(1, n + 1)
        pos = (rank - 0.5) / n
        cols = [np.ones(n), (rank == 1).astype(float), pos - 0.5, (pos - 0.5) ** 2]
        if content:
            cols += list(np.array([ae.content_feats(s) for s in sents]).T)
        docs.append({"title": src + "::" + r["topic"], "y": np.array(y), "X": np.column_stack(cols), "c": np.ones(n)})
    return docs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labeled-dir", required=True)
    ap.add_argument("--content", action="store_true")
    ap.add_argument("--folds", type=int, default=5)
    a = ap.parse_args()
    docs = []
    for s in SOURCES:
        d = build(a.labeled_dir, s, a.content)
        print(f"{s}: {len(d)} documents with >= 6 evaluable sentences")
        docs += d
    if a.content:  # standardise appended content columns across all documents
        allx = np.vstack([d["X"][:, 4:] for d in docs])
        mu, sd = allx.mean(0), allx.std(0) + 1e-9
        for d in docs:
            d["X"][:, 4:] = (d["X"][:, 4:] - mu) / sd
    ys = np.concatenate([d["y"] for d in docs])
    lead = np.mean([d["y"][0] for d in docs]); later = np.concatenate([d["y"][1:] for d in docs]).mean()
    print(f"pooled: {len(docs)} docs, {len(ys)} sentences, human error rate {ys.mean():.3f}; lead {lead:.3f}, later {later:.3f}")
    g, tau = ae.fit(docs)
    print("full-sample fit gamma [const, lead, pos, pos^2" + (", date, number, caps, length" if a.content else "") + "] =", np.round(g, 2), " tau =", round(tau, 2))
    rg = np.random.default_rng(0)
    fold = np.zeros(len(docs), int)
    fold[rg.permutation(len(docs))] = np.arange(len(docs)) % a.folds
    print(f"\n{'phi':>5}{'uniform':>9}{'lead':>8}{'tail':>8}{'static':>8}   static-uniform [95% CI]")
    for phi in (0.1, 0.2, 0.3, 0.5):
        agg = {k: np.zeros(len(docs)) for k in ("uniform", "lead", "tail", "static")}
        tot = np.zeros(len(docs))
        for f in range(a.folds):
            te = np.where(fold == f)[0]
            gf, tf = ae.fit([docs[i] for i in np.where(fold != f)[0]])
            c, t = ae.eval_within([docs[i] for i in te], gf, tf, phi)
            for k in agg:
                agg[k][te] = c[k]
            tot[te] = t
        lo, hi = ae.boot(agg["static"], agg["uniform"], tot)
        T = tot.sum()
        print(f"{phi:5.1f}" + "".join(f"{agg[k].sum()/T:9.3f}" for k in ("uniform", "lead", "tail", "static")) + f"   {(agg['static'].sum()-agg['uniform'].sum())/T:+.3f} [{lo:+.3f},{hi:+.3f}]")


if __name__ == "__main__":
    main()
