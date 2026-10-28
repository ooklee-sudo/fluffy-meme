"""Sentence-level clustering analysis that removes two confounds seen in the claim-level pilot (RESULTS.md).

Unit = sentence (claims split from one sentence are merged), so a single error counted several times cannot create
lag-1 dependence by itself. Sentence label: C if any claim is contradicted, else S if any is supported, else N.

Views (event = sentence contains a contradicted claim):
  all       every sentence that has at least one claim
  verif     only sentences the reference can speak to (label S or C); N-only sentences are dropped, which controls
            the position/rarity differences in how often the reference covers a fact
"""
import argparse
import os

import numpy as np
import pandas as pd

from analyze import analyze, to_frame
from common import read_jsonl


def sentence_docs(docs, mode, event="C"):
    out = []
    for d in docs:
        by = {}
        for c in d["claims"]:
            by.setdefault(c["sent"], []).append(c["label"])
        units = []
        for s in sorted(by):
            labs = by[s]
            lab = "C" if "C" in labs else ("S" if "S" in labs else "N")
            if event == "notS":  # source-grounded task: anything the source does not support is a hallucination
                lab = "S" if all(x == "S" for x in labs) else "C"
            if mode != "all" and lab == "N":
                continue
            units.append({"label": lab, "k": len(labs)})
        out.append({"title": d["title"], "sitelinks": d["sitelinks"], "claims": units})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lab", nargs="+", required=True)
    ap.add_argument("--B", type=int, default=300)
    ap.add_argument("--mode", choices=["all", "verif"], nargs="+", default=["all", "verif"])
    a = ap.parse_args()
    for p in a.lab:
        docs = read_jsonl(p)
        for mode in a.mode:
            sd = sentence_docs(docs, mode)
            df = to_frame(sd, strict=True)
            analyze(df, a.B, label=f"{os.path.basename(p)} sentence-level [{mode}]")


if __name__ == "__main__":
    main()
