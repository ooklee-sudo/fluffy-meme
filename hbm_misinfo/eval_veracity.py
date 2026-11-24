"""Evaluate the veracity module, with and without retrieval (ablation).

Datasets, mapped onto the codebook's Layer D labels:
  scifact    SciFact dev claims (Wadden et al., 2020); KB = its 5,183-abstract corpus
             SUPPORT -> supported, CONTRADICT -> refuted, no evidence -> unsupported
  pubhealth  PUBHEALTH test claims (Kotonya & Toni, 2020); KB = MedlinePlus
             true -> supported, false -> refuted, mixture -> contested, unproven -> unsupported
             Many PUBHEALTH claims are news or political events that no medical knowledge
             base can check, so treat its scores as a lower bound, not a target.

Only claim text is shown to the model; gold evidence and fact-check articles are never used.

    python eval_veracity.py --dataset scifact --n 150
    python eval_veracity.py --dataset pubhealth --n 200 --kb data/kb_medlineplus.jsonl
"""
from __future__ import annotations

import argparse
import json
import random
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

import llm
from veracity import VeracityJudge

HF = "https://huggingface.co/datasets"
SOURCES = {
    # Parquet conversions pinned by commit so results are reproducible.
    "pubhealth": f"{HF}/bigbio/pubhealth/resolve/8c7e1932b279adc2676e1a06a5b354480d56ca71/pubhealth_source/test/0000.parquet",
    "scifact": f"{HF}/allenai/scifact/resolve/62f5afb47a6d7f9b228d51eaeffc1d7ed0a87e65/claims/validation/0000.parquet",
}
DEFAULT_KB = {"pubhealth": "data/kb_medlineplus.jsonl", "scifact": "data/kb_scifact.jsonl"}
PUBHEALTH_SRC = ["true", "false", "unproven", "mixture"]  # label order in the bigbio loader
PUBHEALTH_MAP = {"true": "supported", "false": "refuted", "mixture": "contested", "unproven": "unsupported"}
SCIFACT_MAP = {"SUPPORT": "supported", "CONTRADICT": "refuted", "": "unsupported"}


def _download(url: str, path: Path) -> Path:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, path)
    return path


def load(name: str) -> pd.DataFrame:
    df = pd.read_parquet(_download(SOURCES[name], Path(f"data/{name}_eval.parquet")))
    if name == "pubhealth":
        df = df[df["label"].astype(str).isin(["0", "1", "2", "3"])].copy()
        df["gold"] = df["label"].astype(int).map(lambda i: PUBHEALTH_MAP[PUBHEALTH_SRC[i]])
        return df[["claim_id", "claim", "gold"]]
    # SciFact has one row per (claim, evidence doc); keep claims with a single consistent label.
    df["gold"] = df["evidence_label"].fillna("").map(SCIFACT_MAP)
    g = df.groupby("id").agg(claim=("claim", "first"), gold=("gold", lambda s: s.iloc[0] if s.nunique() == 1 else None))
    g = g.dropna().reset_index().rename(columns={"id": "claim_id"})
    return g[["claim_id", "claim", "gold"]]


def macro_f1(gold, pred, labels):
    f1s = {}
    for l in labels:
        tp = sum(g == l and p == l for g, p in zip(gold, pred))
        fp = sum(g != l and p == l for g, p in zip(gold, pred))
        fn = sum(g == l and p != l for g, p in zip(gold, pred))
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1s[l] = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return sum(f1s.values()) / len(labels), f1s


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dataset", choices=sorted(SOURCES), default="scifact")
    ap.add_argument("--n", type=int, default=150, help="claims sampled, stratified by gold label")
    ap.add_argument("--kb", default=None, help="default: the dataset's matching KB")
    ap.add_argument("--pubmed", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    kb = a.kb or DEFAULT_KB[a.dataset]
    out = Path(a.out or f"runs/{a.dataset}")

    df = load(a.dataset)
    labels = sorted(df["gold"].unique())
    per = max(1, a.n // len(labels))
    rows = []
    for _, g in df.groupby("gold"):
        rows += g.sample(min(per, len(g)), random_state=a.seed).to_dict("records")
    random.Random(a.seed).shuffle(rows)

    judge = VeracityJudge(kb, use_pubmed=a.pubmed)
    out.mkdir(parents=True, exist_ok=True)
    summary = {"dataset": a.dataset, "model": llm.MODEL, "n": len(rows), "kb": kb, "pubmed": a.pubmed,
               "gold_counts": dict(Counter(r["gold"] for r in rows))}
    for cond, use_ret in (("no_retrieval", False), ("retrieval", True)):
        def run(r):
            try:
                return judge.judge(r["claim"], use_retrieval=use_ret)["label"]
            except Exception:  # noqa: BLE001 - keep going; failures are reported and scored as 'unsupported'
                return "ERROR"
        with ThreadPoolExecutor(a.workers) as ex:
            preds = list(ex.map(run, rows))
        gold = [r["gold"] for r in rows]
        n_err = preds.count("ERROR")
        preds = ["unsupported" if p == "ERROR" else p for p in preds]
        m, per_f1 = macro_f1(gold, preds, labels)
        acc = sum(g == p for g, p in zip(gold, preds)) / len(gold)
        summary[cond] = {"macro_f1": round(m, 3), "accuracy": round(acc, 3),
                         "f1_per_label": {k: round(v, 3) for k, v in per_f1.items()},
                         "pred_counts": dict(Counter(preds)), "errors": n_err}
        pd.DataFrame({"claim_id": [r["claim_id"] for r in rows], "claim": [r["claim"] for r in rows],
                      "gold": gold, "pred": preds}).to_csv(out / f"preds_{cond}.csv", index=False)
        print(f"{cond:<13} macro-F1={m:.3f} acc={acc:.3f} errors={n_err} {summary[cond]['f1_per_label']}")
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"wrote {out}/summary.json")


if __name__ == "__main__":
    main()
