"""Is the 'early sentences are wrong more often' effect real, or a content-type composition effect?

Sentence-level logistic intensity with a flexible (spline) position term and content-type covariates computed from the
claim texts by simple rules (reproducible, no extra judge calls):
  has_date   any claim mentions a year (1000-2099), a month name or a 'born/died' style date
  has_num    any claim has another number (digits or million/billion/thousand)
  caps       mean number of capitalised words per claim, excluding the first word (proper-noun density)
  k          number of claims in the sentence
Models (event = sentence with a contradicted claim; same unit/definitions as analyze_sent.py):
  A  spline(position)
  B  A + rarity + document rate of the other sentences (loo)
  C  B + content-type covariates         <- if the early excess shrinks from B to C, it is composition
  D  C + previous-sentence event
The standardised position profile is reported: predicted rate with position set to each quintile midpoint, all other
covariates at their observed values.
"""
import argparse
import os
import re

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

from analyze_sent import sentence_docs
from common import read_jsonl

MONTH = re.compile(r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\b")
YEAR = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")
NUM = re.compile(r"\b\d[\d,\.]*\b|\b(million|billion|thousand|percent)\b", re.I)
CAP = re.compile(r"\b[A-Z][\w'’\-]+")


def build(docs, mode, skip_first=False):
    rows = []
    for d in docs:
        by = {}
        for c in d["claims"]:
            by.setdefault(c["sent"], []).append(c)
        units = []
        for s in sorted(by):
            cl = by[s]
            labs = [c["label"] for c in cl]
            lab = "C" if "C" in labs else ("S" if "S" in labs else "N")
            if mode == "verif" and lab == "N":
                continue
            txt = [c["claim"] for c in cl]
            units.append(dict(y=int(lab == "C"),
                              has_date=int(any(MONTH.search(t) or YEAR.search(t) for t in txt)),
                              has_num=int(any(NUM.search(YEAR.sub("", t)) for t in txt)),
                              caps=np.mean([max(len(CAP.findall(t)) - 1, 0) for t in txt]),
                              k=len(cl)))
        if skip_first:
            units = units[1:]
        n = len(units)
        if n < 6:
            continue
        tot = sum(u["y"] for u in units)
        for i, u in enumerate(units):
            rows.append(dict(doc=d["title"], pos=(i + 0.5) / n, n=n, prev=units[i - 1]["y"] if i else 0,
                             loo=(tot - u["y"]) / (n - 1), lsl=np.log(d["sitelinks"] + 1), **u))
    df = pd.DataFrame(rows)
    df["lsl_c"] = df.lsl - df.lsl.mean()
    return df


def fit(df, rhs):
    g = df.doc.astype("category").cat.codes
    return smf.glm("y ~ " + rhs, df, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds={"groups": g})


def profile(m, df, centers=(0.1, 0.3, 0.5, 0.7, 0.9)):
    out = []
    for c in centers:
        d2 = df.copy()
        d2["pos"] = c
        out.append(m.predict(d2).mean())
    return np.round(out, 3)


def run(path, mode, skip_first=False):
    df = build(read_jsonl(path), mode, skip_first)
    print(f"\n===== {os.path.basename(path)} [{mode}{', lead sentence dropped' if skip_first else ''}]: {df.doc.nunique()} docs, {len(df)} sentences, event rate {df.y.mean():.3f} =====")
    q = pd.cut(df.pos, [0, .2, .4, .6, .8, 1], labels=False)
    comp = df.groupby(q)[["has_date", "has_num", "caps", "k"]].mean().round(2)
    comp["event"] = df.groupby(q).y.mean().round(3)
    print("composition by position quintile:\n", comp.to_string())
    print("event rate by content type: has_date=1: %.3f, has_date=0: %.3f | has_num=1: %.3f, has_num=0: %.3f"
          % (df[df.has_date == 1].y.mean(), df[df.has_date == 0].y.mean(), df[df.has_num == 1].y.mean(), df[df.has_num == 0].y.mean()))
    spl = "bs(pos, df=4)"
    specs = [("A spline(pos)", spl),
             ("B + rarity + docrate", spl + " + lsl_c + loo"),
             ("C + content type", spl + " + lsl_c + loo + has_date + has_num + caps + k"),
             ("D + prev sentence", spl + " + lsl_c + loo + has_date + has_num + caps + k + prev")]
    print(f"\n{'model':<24}{'AIC':>9}   standardised rate at position 0.1/0.3/0.5/0.7/0.9")
    res = {}
    for nm, rhs in specs:
        m = fit(df, rhs)
        res[nm] = m
        print(f"{nm:<24}{m.aic:9.1f}   {profile(m, df)}")
    mC, mD = res["C + content type"], res["D + prev sentence"]
    print("\nmodel C content-type coefficients (z):", {k: f"{mC.params[k]:+.2f} ({mC.params[k]/mC.bse[k]:+.1f})" for k in ["has_date", "has_num", "caps", "k"]})
    print("model D: prev = %+.2f (z %+.1f), lsl_c = %+.2f (z %+.1f)" % (mD.params["prev"], mD.params["prev"] / mD.bse["prev"], mD.params["lsl_c"], mD.params["lsl_c"] / mD.bse["lsl_c"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lab", nargs="+", required=True)
    ap.add_argument("--mode", choices=["all", "verif"], nargs="+", default=["all", "verif"])
    ap.add_argument("--skip-first", action="store_true", help="drop each document's lead sentence")
    a = ap.parse_args()
    for p in a.lab:
        for mode in a.mode:
            run(p, mode, a.skip_first)


if __name__ == "__main__":
    main()
