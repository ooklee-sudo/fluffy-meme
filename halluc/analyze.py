"""Hallucination clustering analysis on claim-level label sequences.

For each document, claims are ordered (t = 1..n); y_t = 1 if claim t is a hallucination (not supported).
Reports:
  1. rate by position decile and rarity tertile            (shape of lambda(t | x))
  2. Fano factor of window counts vs. its null under a fitted *independent* (Bernoulli) intensity model
  3. nested logistic intensity models (AIC): position, rarity, previous-claim event (discrete self-excitation),
     with leave-one-out document rate to absorb document-level heterogeneity
Use --simulate to check the pipeline recovers known mechanisms.
"""
import argparse
import json
import os

import numpy as np
import pandas as pd
import statsmodels.api as sm

from common import DATA, read_jsonl


def to_frame(docs, strict=False):
    rows = []
    for d in docs:
        ys = [int(c["label"] == "C") if strict else int(c["label"] != "S") for c in d["claims"]]
        n = len(ys)
        if n < 8:
            continue
        tot = sum(ys)
        for t, y in enumerate(ys, 1):
            rows.append(dict(doc=d["title"], t=t, n=n, y=y, prev=ys[t - 2] if t > 1 else 0,
                             prev_decay=sum(ys[s] * 0.7 ** (t - 2 - s) for s in range(t - 1)),
                             loo=(tot - y) / (n - 1), lsl=np.log(d["sitelinks"] + 1)))
    df = pd.DataFrame(rows)
    df["lt"] = np.log(df.t)
    df["lsl_c"] = df.lsl - df.lsl.mean()
    return df


def fit(df, cols):
    X = sm.add_constant(df[cols]) if cols else np.ones((len(df), 1))
    m = sm.GLM(df.y, X, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds={"groups": df.doc.astype("category").cat.codes})
    return m


def fano(df, w, p=None):
    """Pooled Fano of non-overlapping window counts. p: per-claim probabilities (null) or None (observed y)."""
    cnt = []
    for _, g in df.groupby("doc", sort=False):
        v = g.y.values if p is None else p[g.index.values]
        for i in range(0, len(g) - w + 1, w):
            cnt.append(v[i:i + w].sum())
    cnt = np.array(cnt)
    return cnt.var(ddof=1) / cnt.mean() if cnt.mean() > 0 else np.nan


def fano_null(df, w, prob, B, rng):
    out = []
    for _ in range(B):
        d2 = df.copy()
        d2["y"] = (rng.random(len(df)) < prob).astype(int)
        out.append(fano(d2, w))
    return np.array(out)


def analyze(df, B=200, seed=0, label=""):
    rng = np.random.default_rng(seed)
    print(f"\n===== {label}: {df.doc.nunique()} docs, {len(df)} claims, overall rate {df.y.mean():.3f} =====")
    q = pd.qcut(df.t / df.n, 5, labels=False)
    print("rate by position quintile (early->late):", np.round(df.groupby(q).y.mean().values, 3))
    r = pd.qcut(df.drop_duplicates("doc").set_index("doc").lsl, 3, labels=["rare", "mid", "popular"])
    print("rate by rarity tertile:", {k: round(v, 3) for k, v in df.groupby(df.doc.map(r)).y.mean().items()})

    cols_seq = [["lt"], ["lt", "lsl_c"], ["lt", "lsl_c", "loo"], ["lt", "lsl_c", "loo", "prev"], ["lt", "lsl_c", "loo", "prev_decay"]]
    names = ["pos", "pos+rarity", "pos+rarity+docrate", "+prev (contagion)", "+decayed history"]
    m0 = fit(df, [])
    print(f"\n{'model':<24}{'AIC':>9}   coefficients (cluster-robust z)")
    print(f"{'constant':<24}{m0.aic:9.1f}")
    models = {}
    for c, nm in zip(cols_seq, names):
        m = fit(df, c)
        models[nm] = m
        co = ", ".join(f"{k}={m.params[k]:+.2f}({m.params[k]/m.bse[k]:+.1f})" for k in c)
        print(f"{nm:<24}{m.aic:9.1f}   {co}")

    # Fano vs. null of the independent intensity model (position + rarity, no history)
    m_ind = models["pos+rarity"]
    prob = m_ind.predict(sm.add_constant(df[["lt", "lsl_c"]])).values
    print(f"\n{'w':>3}{'Fano obs':>10}{'null mean':>11}{'null 95%':>20}{'p':>8}")
    res = {}
    for w in (3, 5, 8):
        obs = fano(df, w)
        nl = fano_null(df, w, prob, B, rng)
        pv = (np.sum(nl >= obs) + 1) / (B + 1)
        res[w] = (obs, nl.mean(), pv)
        print(f"{w:>3}{obs:10.3f}{nl.mean():11.3f}   [{np.percentile(nl,2.5):.3f},{np.percentile(nl,97.5):.3f}]{pv:8.3f}")
    return models, res


def simulate(n_docs=200, n_claims=35, base=-1.3, slope=0.25, rarity_eff=-0.5, gamma=0.0, doc_sd=0.0, seed=0):
    """Known mechanisms: position slope, rarity effect, document-level heterogeneity (doc_sd), contagion (gamma)."""
    rng = np.random.default_rng(seed)
    docs = []
    for i in range(n_docs):
        sl = int(np.exp(rng.uniform(0.7, 4.5)))
        u = rng.normal(0, doc_sd) if doc_sd else 0.0
        ys, prev = [], 0
        for t in range(1, n_claims + 1):
            eta = base + slope * np.log(t) + rarity_eff * (np.log(sl + 1) - 2.5) + u + gamma * prev
            y = int(rng.random() < 1 / (1 + np.exp(-eta)))
            ys.append(y)
            prev = y
        docs.append({"title": f"d{i}", "sitelinks": sl, "claims": [{"label": "N" if y else "S"} for y in ys]})
    return docs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lab", nargs="*", default=[])
    ap.add_argument("--simulate", action="store_true")
    ap.add_argument("--strict", action="store_true", help="event = contradicted only")
    ap.add_argument("--B", type=int, default=200)
    a = ap.parse_args()
    if a.simulate:
        for nm, kw in [("S0 independent (pos+rarity only)", {}),
                       ("S1 + doc heterogeneity (sd=1)", dict(doc_sd=1.0)),
                       ("S2 + contagion gamma=1.0", dict(gamma=1.0)),
                       ("S3 doc heterogeneity + contagion", dict(doc_sd=1.0, gamma=1.0))]:
            analyze(to_frame(simulate(**kw)), a.B, label="SIM " + nm)
        return
    for p in a.lab:
        analyze(to_frame(read_jsonl(p), a.strict), a.B, label=os.path.basename(p) + (" [strict]" if a.strict else ""))


if __name__ == "__main__":
    main()
