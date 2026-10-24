"""Product-level goods classification with LLMs: search vs experience, hedonic vs utilitarian.

Definitions follow the usage in Winter et al. (2026) / Kubler et al. (2024) / Nelson (1970): a search good's main
quality can be judged reliably before purchase from seller-provided information; an experience good's cannot (fit,
taste, scent, comfort, effectiveness, durability). Hedonic = bought mainly for pleasure/sensory-emotional value;
utilitarian = mainly for a functional task. Anchors from WZH: smartphone (search, hedonic), printer (search,
utilitarian), mascara (experience, hedonic), vacuum cleaner (experience, utilitarian).
LLM labels are NOT human-validated: report cross-LLM agreement and inspect a random sample before relying on them.

Usage: python product_labels.py --meta-dir meta --out-dir labels --model anthropic/claude-haiku-5.5 [--limit N]
"""
import argparse
import glob
import json
from pathlib import Path

import pandas as pd

import llm_coding

SYSTEM = """You classify one Amazon product (given by its listing information, not by reviews).
Return ONLY a JSON object: {"product_type": "<generic product type, 2-4 words>", "good_type": "search" or "experience", "motive": "hedonic" or "utilitarian"}.

good_type: "search" if the product's main quality can be judged reliably BEFORE purchase from information the seller provides (specifications, dimensions, compatibility, photos, ratings). "experience" if the main quality can only be judged AFTER using, tasting, wearing or trying it (e.g. fit, comfort, taste, scent, skin reaction, feel, durability, how well it actually works).
motive: "hedonic" if the product is bought mainly for pleasure, enjoyment, sensory or emotional value or self-expression. "utilitarian" if it is bought mainly to perform a functional task or solve a practical need.
Decide for the product itself. Anchors: smartphone = search, hedonic; printer = search, utilitarian; mascara = experience, hedonic; vacuum cleaner = experience, utilitarian."""


def describe(o):
    cats = " > ".join([c for c in (o.get("categories") or []) if c][-4:])
    feats = "; ".join((o.get("features") or [])[:3])[:300]
    return (f"Title: {(o.get('title') or '')[:200]}\nMain category: {o.get('main_category')}\n"
            f"Category path: {cats}\nFeatures: {feats}\nDescription: {(o.get('description') or '')[:250]}")


class ProductCoder(llm_coding.OpenRouterCoder):
    def __init__(self, model):
        super().__init__(model, "product")
        self.system, self.raw_user = SYSTEM, True

    def code(self, text):
        o = llm_coding._parse_json(self._call(text, max_tokens=80))
        g, m = str(o.get("good_type", "")).lower(), str(o.get("motive", "")).lower()
        if g not in ("search", "experience") or m not in ("hedonic", "utilitarian"):
            raise ValueError(f"bad labels {o!r}")
        return {"product_type": str(o.get("product_type", ""))[:60], "good_type": g, "motive": m}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta-dir", required=True); ap.add_argument("--out-dir", required=True)
    ap.add_argument("--model", default="anthropic/claude-haiku-5.5")
    ap.add_argument("--workers", type=int, default=32); ap.add_argument("--limit", type=int)
    a = ap.parse_args()
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    rows = []
    for f in sorted(glob.glob(f"{a.meta_dir}/meta_*.jsonl")):
        rows += [json.loads(l) for l in open(f)]
    meta = pd.DataFrame(rows).drop_duplicates("parent_asin")
    if a.limit:
        meta = meta.sample(a.limit, random_state=0)
    meta["text"] = [describe(r) for r in meta.to_dict("records")]
    coder = ProductCoder(a.model)
    res = llm_coding.code_reviews(meta[["parent_asin", "text"]].reset_index(drop=True), coder,
                                  out / f"product_cache_{a.model.replace('/', '_')}.jsonl", workers=a.workers)
    res = res.drop(columns=["text"])
    res.to_csv(out / f"product_labels_{a.model.replace('/', '_')}.csv", index=False)
    print("[usage]", coder.usage, "| unparsed:", int(res["good_type"].isna().sum()))
    print(res["good_type"].value_counts(dropna=False).to_dict(), res["motive"].value_counts(dropna=False).to_dict())


if __name__ == "__main__":
    main()
