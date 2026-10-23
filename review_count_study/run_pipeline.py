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

import correction, embeddings, lexicon, llm_coding, load_data, models, prompts, reliability


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", choices=["demo", "yelp", "amazon"], default="demo")
    ap.add_argument("--review-path"); ap.add_argument("--user-path"); ap.add_argument("--category", default="amazon")
    ap.add_argument("--n", type=int, default=3000)
    ap.add_argument("--coder", choices=["mock", "anthropic"], default="mock")
    ap.add_argument("--model", default=llm_coding.DEFAULT_MODEL)
    ap.add_argument("--variant", choices=["base", "alt"], default="base")
    ap.add_argument("--human-labels", help="CSV: review_id + coded fields; must be a simple random sample of the analysis rows")
    ap.add_argument("--demo-human-n", type=int, default=400, help="demo only: simulate this many human labels")
    ap.add_argument("--out", default="out")
    ap.add_argument("--embedding", choices=["none", "tfidf", "st"], default="tfidf", help="text-embedding baseline for RQ2 (M4/M5)")
    ap.add_argument("--emb-dim", type=int, default=20)
    ap.add_argument("--min-level-share", type=float, default=0.05, help="collapse dominant_emotion levels rarer than this into 'other'")
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

    # 3. reliability vs human labels (if provided; the demo simulates them from the noise-free mock coder)
    h = None
    if a.human_labels:
        h = pd.read_csv(a.human_labels).set_index("review_id")
    elif a.source == "demo" and a.demo_human_n > 0:
        sub = coded.sample(min(a.demo_human_n, len(coded)), random_state=a.seed)
        h = llm_coding.code_reviews(sub[load_data.COMMON], llm_coding.MockCoder(False), out / "demo_truth_cache.jsonl")
        h = h.set_index("review_id")[prompts.CODED_FIELDS + ["valid"]]
    if h is not None:
        c = coded.set_index("review_id").loc[h.index]
        tab = reliability.agreement_table(c, h)
        tab.to_csv(out / "reliability.csv", index=False)
        print("[reliability]\n", tab.round(3).to_string(index=False))

    # 4. models
    emap = models.rare_level_map(coded["dominant_emotion"], a.min_level_share)
    print("[levels] dominant_emotion map:", {k: v for k, v in emap.items() if k != v} or "no collapsing needed")
    d = lexicon.add_lexicon_features(models.prepare(coded, emap))
    rhs = models.CONTROLS + models.LLM_TERMS
    print("[collinearity]", models.collinearity_check(d, rhs))
    print("[dispersion]", {k: round(v, 3) for k, v in models.dispersion_report(d, rhs).items()})
    pois = models.fit_glm(d, rhs, "poisson")
    nb = models.fit_glm(d, rhs, "nb")
    print("\n[Poisson IRR, cluster-robust SE]\n", models.irr_table(pois).round(3).to_string())
    print("\n[NB2 IRR, cluster-robust SE]\n", models.irr_table(nb).round(3).to_string())
    models.irr_table(nb).to_csv(out / "irr_nb2.csv")

    # 5. RQ2: held-out deviance by feature set (M1 lexicon baseline needs a lexicon column; skipped if absent)
    sets = {"M0 controls": models.CONTROLS,
            "M1 +lexicon (VADER)": models.CONTROLS + lexicon.LEXICON_TERMS,
            "M2 +LLM": rhs,
            "M3 +lexicon +LLM": rhs + lexicon.LEXICON_TERMS}
    if a.embedding != "none":
        d, ecols = embeddings.add_embeddings(d, a.embedding, a.emb_dim)
        sets["M4 +embedding (unpenalized)"] = models.CONTROLS + ecols
        sets["M4r +embedding (ridge)"] = (models.CONTROLS + ecols, ["emb_"])
        sets["M5r +embedding +LLM (ridge)"] = (rhs + ecols, ["emb_"])
    cv = models.cv_compare(d, sets)
    cv.to_csv(out / "cv_compare.csv", index=False)
    print("\n[RQ2 held-out Poisson deviance]\n", cv.round(4).to_string(index=False))

    # 5b. measurement-error corrected (DSL/PPI-style) Poisson using the human-labelled random subset
    if h is not None:
        hum = models.prepare(h.reset_index().merge(coded[["review_id", "text", "days_since_post", "author_reviews",
                                                          "count", "stars", "group_id"]], on="review_id"), emap)
        hum.index = hum["review_id"].map(pd.Series(d.index, index=d["review_id"]))  # align to d's row index
        res = correction.dsl_poisson(d, hum, rhs)
        res.to_csv(out / "irr_dsl.csv")
        naive = models.irr_table(models.fit_glm(d, rhs, "poisson"))[["IRR", "ci_low", "ci_high"]].add_prefix("naive_")
        both = naive.join(res[["IRR", "ci_low", "ci_high", "p"]].add_prefix("dsl_"), how="inner")
        print(f"\n[Corrected Poisson: DSL with n_human={len(hum)} of N={len(d)} vs naive LLM-only]\n", both.round(3).to_string())

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
