"""Replication-style analysis of Winter, Zacharias & Hartwig (2026, Marketing Letters) on the Amazon sample.

Study 1 analogue: agreement between the author's star rating and an LLM's star rating inferred from text.
Study 2 analogue: helpful votes ~ |stars - stars_llm| x experience good, estimated with
  (a) Tobit, left-censored at 0, SE clustered (as in the paper)  and
  (b) NB2 count model with log(review age) offset (our specification),
plus our extension: does the gap survive when the LLM-coded content features are controlled?

Differences from the paper (document them in any write-up): LLM = a different model/prompt than GPT-4; goods
type = grocery (experience) vs electronics (search) instead of 12 products; no video flag / review-count control;
clusters = users (our sampling cluster) not products; sample of 2,000, not 28,900.
Usage: python replicate_winter.py --sample amazon_sample.parquet --coded out/reviews_coded.parquet --out-dir out
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from patsy import dmatrices
from scipy import stats
from statsmodels.base.model import GenericLikelihoodModel

import llm_coding, load_data, models, star_rating


class Tobit(GenericLikelihoodModel):
    """Left-censored (at 0) Tobit: y* = Xb + e, e~N(0, s^2); y = max(y*, 0)."""

    def loglikeobs(self, params):
        b, s = params[:-1], np.exp(params[-1])
        xb, y = self.exog @ b, self.endog
        cens = y <= 0
        return np.where(cens, stats.norm.logcdf(-xb / s), stats.norm.logpdf((y - xb) / s) - np.log(s))

    def fit(self, start_params=None, maxiter=2000, **kw):
        if start_params is None:
            ols = sm.OLS(self.endog, self.exog).fit()
            start_params = np.append(ols.params, np.log(np.sqrt(ols.scale)))
        return super().fit(start_params=start_params, maxiter=maxiter, method="bfgs", disp=0, **kw)


def fit_tobit(formula, d, group):
    y, X = dmatrices(formula, d, return_type="dataframe")
    m = Tobit(y.iloc[:, 0].to_numpy(float), X.to_numpy(float))
    r = m.fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d[group])[0]})
    names = list(X.columns) + ["log_sigma"]
    out = pd.DataFrame({"coef": r.params, "se": r.bse, "p": r.pvalues}, index=names)
    return out, r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", required=True)
    ap.add_argument("--coded", help="reviews_coded.parquet with LLM content codes; omit to skip the content-feature extension")
    ap.add_argument("--cluster", choices=["group_id", "parent_asin"], default="parent_asin",
                    help="cluster-robust SE unit: parent_asin (product, as in the paper) or group_id (user)")
    ap.add_argument("--out-dir", required=True); ap.add_argument("--model", default="anthropic/claude-haiku-5.5")
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)

    base = load_data.load_amazon_sample(a.sample).drop_duplicates("review_id")  # same user/asin/timestamp can repeat
    raw = pd.read_parquet(a.sample)
    extra = raw[["user_id", "asin", "timestamp", "has_image", "parent_asin"] + (["hedonic"] if "hedonic" in raw else [])].copy()
    extra["review_id"] = extra["user_id"] + "|" + extra["asin"] + "|" + extra["timestamp"].astype(str)
    extra = extra.drop_duplicates("review_id")
    base = base.merge(extra.drop(columns=["user_id", "asin", "timestamp"]), on="review_id").reset_index(drop=True)
    d = base
    if a.coded:
        coded = pd.read_parquet(a.coded).drop_duplicates("review_id")
        content = coded.drop(columns=[c for c in base.columns if c != "review_id" and c in coded.columns], errors="ignore")
        d = base.merge(content, on="review_id", how="left")

    # LLM star inference (cached; failed rows retried on rerun)
    sc = star_rating.StarCoder(a.model)
    st = llm_coding.code_reviews(base[["text"]], sc, out / f"stars_cache_{a.model.replace('/', '_')}.jsonl", workers=a.workers)
    d["stars_llm"] = st["stars_llm"].to_numpy()
    print("[usage]", sc.usage, "| failed star rows:", int(d["stars_llm"].isna().sum()))
    d = d.dropna(subset=["stars_llm"]).copy()
    d["gap"] = (d["stars"] - d["stars_llm"]).abs()
    d["experience"] = (d["category"] == "experience").astype(int)
    d["len_chars"] = d["text"].str.len()
    d["age"] = d["days_since_post"].clip(lower=1)
    d["exposure"] = d["age"]
    d["star_f"] = d["stars"].astype(int)
    d.to_csv(out / "replication_data.csv", index=False)

    G = a.cluster
    # ---------------- Study 1 analogue
    r, _ = stats.pearsonr(d["stars"], d["stars_llm"])
    print(f"\n[Study 1] N={len(d)}  r(author stars, LLM stars)={r:.3f}  exact match={np.mean(d.gap == 0):.1%}  "
          f"off by >=2: {np.mean(d.gap >= 2):.1%}   (paper: r=.763, 37% misclassified, ~5% off by >=2)")
    print(d.groupby("category")["gap"].agg(["mean", "size"]).round(3).to_string())
    print(d.groupby("star_f")["gap"].mean().round(3).rename("mean gap by author star").to_string())
    if "hedonic" in d and (d["hedonic"] >= 0).all():
        o = smf.ols("gap ~ hedonic + C(star_f) + len_chars + age", data=d).fit(
            cov_type="cluster", cov_kwds={"groups": pd.factorize(d[G])[0]})
        print("\n[Study 1 regression, OLS: gap ~ hedonic + rating dummies + length + age]  (paper: hedonic -.058***)")
        print(pd.DataFrame({"coef": o.params, "se": o.bse, "p": o.pvalues}).loc[["hedonic", "len_chars", "age"]].round(4).to_string())
        d.groupby(["category", "hedonic"])["gap"].mean().round(3).rename("mean gap by cell").to_frame().pipe(print)

    # ---------------- Study 2 analogue: Tobit
    ctrl = "len_chars + C(star_f) + has_image + age"
    t1, _ = fit_tobit(f"count ~ gap + experience + {ctrl}", d, G)
    t2, _ = fit_tobit(f"count ~ gap * experience + {ctrl}", d, G)
    keep = ["gap", "experience", "gap:experience", "len_chars", "has_image", "age"]
    print(f"\n[Study 2, Tobit left-censored at 0; SE clustered by {G}]  (paper Model 1: gap -0.650 n.s.; "
          "Model 2: gap +4.345*, gap x experience -7.239***)")
    print("Model 1:\n", t1.reindex(keep).dropna().round(3).to_string())
    print("Model 2:\n", t2.reindex(keep).round(3).to_string())
    t2.to_csv(out / "replication_tobit_model2.csv")

    # ---------------- Our count specifications: NB2 (offset log age) and ZINB
    cl = {"groups": pd.factorize(d[G])[0]}
    base_rhs = "np.log(len_chars) + C(star_f) + has_image"
    def f_nb(rhs):
        al = models._estimate_alpha(d.assign(), [rhs])
        return smf.glm("count ~ " + rhs, data=d, family=sm.families.NegativeBinomial(alpha=al),
                       offset=np.log(d["exposure"])).fit(cov_type="cluster", cov_kwds=cl)
    n1, n2 = f_nb(f"gap + experience + {base_rhs}"), f_nb(f"gap * experience + {base_rhs}")
    for nm, m in (("Model 1", n1), ("Model 2", n2)):
        tab = models.irr_table(m).reindex(["gap", "experience", "gap:experience", "np.log(len_chars)", "has_image"]).dropna(how="all")
        print(f"\n[NB2 count model, log(age) offset; IRR; {nm}]\n", tab.round(3).to_string())
        tab.to_csv(out / f"replication_nb2_{nm[-1]}.csv")

    try:
        z = models.zero_inflation_check(d)
        print("\n[Zero inflation: NB2 vs ZINB (inflation: const + experience)]")
        print(f"  logLik NB2 {z['nb_llf']:.2f} | ZINB {z['zinb_llf']:.2f}   AIC NB2 {z['nb_aic']:.1f} | ZINB {z['zinb_aic']:.1f}")
        print(f"  implied P(structural zero) = {z['p_structural_zero']:.2e} -> "
              + ("ZINB collapses to NB2 (no excess zeros beyond the NB distribution); use NB2" if z["collapsed_to_nb"] else "ZINB differs from NB2; inspect"))
        print(f"  gap IRR: NB2 {z['nb_gap_irr']:.3f} | ZINB count part {z['zinb_gap_irr']:.3f}")
    except Exception as e:
        print("\n[Zero inflation] check failed:", repr(e)[:200])

    # ---------------- Robustness: product vs user clusters for the key NB2 interaction
    for other in ("group_id", "parent_asin"):
        m = smf.glm("count ~ gap * experience + " + base_rhs, data=d,
                    family=sm.families.NegativeBinomial(alpha=models._estimate_alpha(d, ["gap * experience + " + base_rhs])),
                    offset=np.log(d["exposure"])).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d[other])[0]})
        ci = np.exp(m.conf_int().loc["gap:experience"])
        print(f"[robustness] NB2 gap:experience cluster={other}: IRR={np.exp(m.params['gap:experience']):.3f} "
              f"CI [{ci[0]:.3f}, {ci[1]:.3f}] p={m.pvalues['gap:experience']:.3f}")

    # ---------------- Extension: gap + LLM content features
    if a.coded and "sentiment" in d:
        d = d.dropna(subset=["sentiment"]).copy()
        d["sentiment_c"] = d["sentiment"] - 3
        emap = models.rare_level_map(d["dominant_emotion"], 0.05)
        d["dominant_emotion"] = d["dominant_emotion"].map(emap)
        feats = ("sentiment_c + emotional_intensity + specificity + informativeness + argument_balance + narrative + "
                 "explicit_recommendation + comparison")
        n3 = f_nb(f"gap * experience + {feats} + C(dominant_emotion) + {base_rhs}")
        tab3 = models.irr_table(n3).loc[["gap", "experience", "gap:experience", "specificity", "informativeness",
                                          "argument_balance", "emotional_intensity", "sentiment_c"]]
        print("\n[Extension: NB2 with gap AND LLM content features; IRR]\n", tab3.round(3).to_string())
        tab3.to_csv(out / "replication_nb2_with_content.csv")


if __name__ == "__main__":
    main()
