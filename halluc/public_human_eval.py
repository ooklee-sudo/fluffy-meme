"""Clustering, position pattern, context-length effect and allocation gain on PUBLIC HUMAN hallucination labels
(no LLM judge anywhere in this script).

Datasets (downloaded separately, not stored in this repo):
  WikiBio GPT-3  (potsawee/wiki_bio_gpt3_hallucination, CC-BY-SA-3.0): GPT-3 biographies, sentence labels
                 accurate / minor_inaccurate / major_inaccurate.  Event = not accurate (strict: major).
  RAGTruth       (summarisation part; MIT; https://github.com/ParticleMedia/RAGTruth, here the HF copy wandb/RAGTruth-processed):
                 news summaries by 6 LLMs with human-marked hallucination SPANS (char offsets). A sentence is an error if a
                 span overlaps it.  Event = any span (strict: 'Evident Conflict' / 'Subtle Conflict' only).
Units are sentences (RAGTruth: regex segmentation of the response).  Per group:
  rate, lead vs later, position quintiles, Fano of w-sentence windows vs an independent logistic null (position [+ model
  + log context length]), document heterogeneity tau, and out-of-sample policy gains (5-fold over documents).
"""
import argparse
import json
import re

import numpy as np
import pandas as pd
import statsmodels.api as sm

import alloc_eval as ae
from analyze import fano, fano_null

SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(\[])")


def sentence_offsets(text):
    out, start = [], 0
    for m in SPLIT.finditer(text):
        out.append((start, m.start()))
        start = m.end()
    out.append((start, len(text)))
    return [(a, b) for a, b in out if text[a:b].strip()]


def wikibio_docs(path, strict, min_units):
    df = pd.read_parquet(path)
    docs = []
    for i, r in df.iterrows():
        ann = list(r["annotation"])
        y = [int(a == "major_inaccurate") if strict else int(a != "accurate") for a in ann]
        if len(y) >= min_units:
            docs.append({"id": f"wb{i}", "y": np.array(y), "group": "wikibio", "ctx": 0.0, "model": "gpt-3"})
    return docs


def ragtruth_docs(train, test, task, strict, min_units):
    df = pd.concat([pd.read_parquet(train), pd.read_parquet(test)])
    df = df[(df.task_type == task) & (df.quality == "good")]
    docs = []
    for _, r in df.iterrows():
        spans = json.loads(r["hallucination_labels"]) if isinstance(r["hallucination_labels"], str) else list(r["hallucination_labels"])
        if strict:
            spans = [s for s in spans if "Conflict" in s.get("label_type", "")]
        offs = sentence_offsets(r["output"])
        y = [int(any(s["start"] < b and s["end"] > a for s in spans)) for a, b in offs]
        if len(y) >= min_units:
            docs.append({"id": f"rt{r['id']}", "y": np.array(y), "group": r["model"], "ctx": float(np.log(len(r["context"]))), "model": r["model"]})
    return docs


def to_ae(docs, models=None, use_ctx=False):
    """Attach the feature matrix used by alloc_eval: [1, lead, pos, pos^2, (model dummies), (log context)]."""
    out = []
    ctx_mean = np.mean([d["ctx"] for d in docs])
    for d in docs:
        n = len(d["y"])
        rank = np.arange(1, n + 1)
        pos = (rank - 0.5) / n
        cols = [np.ones(n), (rank == 1).astype(float), pos - 0.5, (pos - 0.5) ** 2]
        for m in (models or []):
            cols.append(np.full(n, float(d["model"] == m)))
        if use_ctx:
            cols.append(np.full(n, d["ctx"] - ctx_mean))
        out.append({"title": d["id"], "y": d["y"], "X": np.column_stack(cols), "c": np.ones(n)})
    return out


def frame(docs, models=None, use_ctx=False):
    rows = []
    cm = np.mean([d["ctx"] for d in docs])
    for d in docs:
        n = len(d["y"])
        for t, y in enumerate(d["y"], 1):
            row = dict(doc=d["id"], t=t, n=n, y=int(y), lt=np.log(t), pos=(t - 0.5) / n)
            for m in (models or []):
                row["m_" + m] = float(d["model"] == m)
            if use_ctx:
                row["ctx"] = d["ctx"] - cm
            rows.append(row)
    return pd.DataFrame(rows)


def describe(name, docs, w, models=None, use_ctx=False, B=300):
    df = frame(docs, models, use_ctx)
    if df.empty:
        print(f"{name}: no documents"); return
    q = pd.cut(df.pos, [0, .2, .4, .6, .8, 1.0], labels=False)
    lead = df[df.t == 1].y.mean(); later = df[df.t > 1].y.mean()
    cols = ["lt"] + [c for c in df.columns if c.startswith("m_")][1:] + (["ctx"] if use_ctx else [])
    X = sm.add_constant(df[cols])
    m = sm.GLM(df.y, X, family=sm.families.Binomial()).fit()
    prob = m.predict(X).values
    rng = np.random.default_rng(0)
    obs, nl = fano(df, w), fano_null(df, w, prob, B, rng)
    p = (np.sum(nl >= obs) + 1) / (B + 1)
    _, tau = ae.fit(to_ae(docs, models, use_ctx))
    print(f"{name:<24}docs {df.doc.nunique():5d} sentences {len(df):6d} rate {df.y.mean():.3f} | lead {lead:.3f} later {later:.3f} | "
          f"quintiles {np.round([df[q == k].y.mean() for k in range(5)], 3)} | Fano(w={w}) {obs:.2f} vs null {nl.mean():.2f} "
          f"[{np.percentile(nl, 2.5):.2f},{np.percentile(nl, 97.5):.2f}] p={p:.3f} | tau {tau:.2f}")


def policy(name, docs, models=None, use_ctx=False, folds=5):
    ad = to_ae(docs, models, use_ctx)
    rg = np.random.default_rng(0)
    fold = np.zeros(len(ad), int)
    fold[rg.permutation(len(ad))] = np.arange(len(ad)) % folds
    print(f"  policy gains, {name} ({len(ad)} docs):")
    for label, mode in (("within-doc budget", "within"), ("pooled budget", "pooled")):
        for phi in (0.1, 0.3):
            keys = ("uniform", "lead", "tail", "static") if mode == "within" else ("uniform", "static", "adaptive")
            agg = {k: np.zeros(len(ad)) for k in keys}
            tot = np.zeros(len(ad))
            for f in range(folds):
                te = np.where(fold == f)[0]
                g, t = ae.fit([ad[i] for i in np.where(fold != f)[0]])
                if mode == "within":
                    c, tt = ae.eval_within([ad[i] for i in te], g, t, phi)
                else:
                    c, tt = ae.eval_pooled([ad[i] for i in te], g, t, phi, 1.0, np.random.default_rng(f))
                for k in keys:
                    agg[k][te] = c[k]
                tot[te] = tt
            T = tot.sum()
            lo, hi = ae.boot(agg["static"], agg["uniform"], tot, B=1000)
            extra = f"lead {agg['lead'].sum()/T:.3f} tail {agg['tail'].sum()/T:.3f}" if mode == "within" else \
                    f"adaptive-static {(agg['adaptive'].sum()-agg['static'].sum())/T:+.3f}"
            print(f"    {label:<18} phi {phi:.1f}: uniform {agg['uniform'].sum()/T:.3f} static {agg['static'].sum()/T:.3f} "
                  f"static-uniform {(agg['static'].sum()-agg['uniform'].sum())/T:+.3f} [{lo:+.3f},{hi:+.3f}]  {extra}")


def context_effect(docs):
    """Document-level: error rate per sentence vs the length of the source text."""
    df = pd.DataFrame([{"ctx": d["ctx"], "rate": d["y"].mean(), "n": len(d["y"]), "any": int(d["y"].any()), "model": d["model"]} for d in docs])
    df["tert"] = pd.qcut(df.ctx, 3, labels=["short source", "mid", "long source"])
    print("  source length tertile -> share of sentences in error / share of responses with any error:")
    for t, g in df.groupby("tert", observed=True):
        print(f"    {t:<13} ctx chars ~{np.exp(g.ctx.median()):6.0f}: sentence error {np.average(g.rate, weights=g.n):.3f}, any error {g['any'].mean():.3f} (n={len(g)})")
    X = sm.add_constant(pd.concat([df[["ctx"]], pd.get_dummies(df.model, drop_first=True).astype(float)], axis=1))
    mm = sm.GLM(df["any"], X, family=sm.families.Binomial()).fit(cov_type="HC1")
    print(f"    logit(any error) on log source length, controlling for model: coef {mm.params['ctx']:+.2f} (z {mm.params['ctx']/mm.bse['ctx']:+.1f})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wikibio", required=True)
    ap.add_argument("--rt-train", required=True)
    ap.add_argument("--rt-test", required=True)
    ap.add_argument("--task", default="Summary")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--min-units", type=int, default=4)
    ap.add_argument("--w", type=int, default=3)
    a = ap.parse_args()
    tag = "strict (major / conflict only)" if a.strict else "any inaccuracy / any hallucination span"
    print(f"event definition: {tag}; documents need >= {a.min_units} sentences; Fano windows w={a.w}\n")
    print("== WikiBio GPT-3 (biographies, sentence-level human labels)")
    wb = wikibio_docs(a.wikibio, a.strict, a.min_units)
    describe("wikibio", wb, a.w)
    policy("wikibio", wb)
    print(f"\n== RAGTruth {a.task} (human-marked hallucination spans)")
    rt = ragtruth_docs(a.rt_train, a.rt_test, a.task, a.strict, a.min_units)
    models = sorted({d["model"] for d in rt})
    for m in models:
        describe(m, [d for d in rt if d["model"] == m], a.w, use_ctx=True)
    describe("ALL (model+ctx control)", rt, a.w, models, True)
    print("\n  long-context question:")
    context_effect(rt)
    policy("RAGTruth, position only", rt)
    policy("RAGTruth, + model + log source length", rt, models, True)


if __name__ == "__main__":
    main()
