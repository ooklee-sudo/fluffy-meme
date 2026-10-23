"""End-to-end: load -> (sample) -> LLM coding -> reliability -> count models.

Examples
  python run_pipeline.py --source demo --coder mock
  python run_pipeline.py --source yelp --review-path yelp_academic_dataset_review.json \
      --user-path yelp_academic_dataset_user.json --n 30000 --coder anthropic
  python run_pipeline.py --source amazon --review-path Electronics.jsonl --category electronics --n 20000 --coder anthropic
  # reliability: add --human-labels human.csv (columns: review_id + coded fields) to compare with LLM
"""
import argparse
from pathlib import Path

import pandas as pd

import llm_coding, load_data, models, prompts, reliability


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["demo", "yelp", "amazon"], default="demo")
    ap.add_argument("--review-path"); ap.add_argument("--user-path"); ap.add_argument("--category", default="amazon")
    ap.add_argument("--n", type=int, default=3000)
    ap.add_argument("--coder", choices=["mock", "anthropic"], default="mock")
    ap.add_argument("--model", default=llm_coding.DEFAULT_MODEL)
    ap.add_argument("--variant", choices=["base", "alt"], default="base")
    ap.add_argument("--human-labels")
    ap.add_argument("--out", default="out")
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(exist_ok=True)

    # 1. data
    if a.source == "demo":
        df = load_data.make_demo(a.n, a.seed)
    elif a.source == "yelp":
        df = load_data.load_yelp(a.review_path, a.user_path)
    else:
        df = load_data.load_amazon(a.review_path, a.category)
    df = load_data.stratified_sample(df, a.n, seed=a.seed) if len(df) > a.n else df
    print(f"[data] {len(df)} reviews, mean count={df['count'].mean():.2f}")

    # 2. LLM coding (cached, resumable)
    coder = llm_coding.MockCoder() if a.coder == "mock" else llm_coding.AnthropicCoder(
        a.model, "base" if a.variant == "base" else "alt")
    coded = llm_coding.code_reviews(df, coder, out / f"coding_cache_{coder.model}_{coder.variant}.jsonl")
    coded.to_parquet(out / "reviews_coded.parquet") if _has_pyarrow() else coded.to_csv(out / "reviews_coded.csv", index=False)
    failed = coded["error"].notna().sum() if "error" in coded else 0
    print(f"[coding] failed rows: {failed}")
    coded = coded[coded["error"].isna()] if "error" in coded else coded

    # 3. reliability vs human labels (if provided)
    if a.human_labels:
        h = pd.read_csv(a.human_labels).set_index("review_id")
        c = coded.set_index("review_id").loc[h.index]
        tab = reliability.agreement_table(c, h)
        tab.to_csv(out / "reliability.csv", index=False)
        print("[reliability]\n", tab.round(3).to_string(index=False))

    # 4. models
    d = models.prepare(coded)
    rhs = models.CONTROLS + models.LLM_TERMS
    print("[collinearity]", models.collinearity_check(d, rhs))
    print("[dispersion]", {k: round(v, 3) for k, v in models.dispersion_report(d, rhs).items()})
    pois = models.fit_glm(d, rhs, "poisson")
    nb = models.fit_glm(d, rhs, "nb")
    print("\n[Poisson IRR, cluster-robust SE]\n", models.irr_table(pois).round(3).to_string())
    print("\n[NB2 IRR, cluster-robust SE]\n", models.irr_table(nb).round(3).to_string())
    models.irr_table(nb).to_csv(out / "irr_nb2.csv")

    # 5. RQ2: held-out deviance by feature set (M1 lexicon baseline needs a lexicon column; skipped if absent)
    sets = {"M0 controls": models.CONTROLS, "M2 +LLM": rhs}
    if "lexicon_sentiment" in d:
        sets["M1 +lexicon"] = models.CONTROLS + ["lexicon_sentiment"]
    cv = models.cv_compare(d, sets)
    cv.to_csv(out / "cv_compare.csv", index=False)
    print("\n[RQ2 held-out Poisson deviance]\n", cv.round(4).to_string(index=False))

    # 6. H3: product-type heterogeneity
    if d["category"].nunique() > 1:
        het = models.heterogeneity(d, rhs)
        print("\n[H3 specificity x category]\n", models.irr_table(het).filter(like="specificity", axis=0).round(3).to_string())


def _has_pyarrow():
    try:
        import pyarrow  # noqa
        return True
    except ImportError:
        return False


if __name__ == "__main__":
    main()
