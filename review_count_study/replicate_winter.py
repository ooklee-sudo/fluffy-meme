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
    ap.add_argument("--sample", required=True); ap.add_argument("--coded", required=True)
    ap.add_argument("--out-dir", required=True); ap.add_argument("--model", default="anthropic/claude-haiku-5.5")
    ap.add_argument("--workers", type=int, default=16)
    a = ap.parse_args()
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)

    base = load_data.load_amazon_sample(a.sample)
    extra = pd.read_parquet(a.sample)[["user_id", "asin", "timestamp", "has_image", "parent_asin"]]
    extra["review_id"] = extra["user_id"] + "|" + extra["asin"] + "|" + extra["timestamp"].astype(str)
    base = base.merge(extra[["review_id", "has_image", "parent_asin"]], on="review_id")
    coded = pd.read_parquet(a.coded)
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

    # ---------------- Study 1 analogue
    r, _ = stats.pearsonr(d["stars"], d["stars_llm"])
    print(f"\n[Study 1] N={len(d)}  r(author stars, LLM stars)={r:.3f}  exact match={np.mean(d.gap == 0):.1%}  "
          f"off by >=2: {np.mean(d.gap >= 2):.1%}   (paper: r=.763, 37% misclassified, ~5% off by >=2)")
    print(d.groupby("category")["gap"].agg(["mean", "size"]).round(3).to_string())
    print(d.groupby("star_f")["gap"].mean().round(3).rename("mean gap by author star").to_string())

    # ---------------- Study 2 analogue: Tobit
    ctrl = "len_chars + C(star_f) + has_image + age"
    t1, _ = fit_tobit(f"count ~ gap + experience + {ctrl}", d, "group_id")
    t2, _ = fit_tobit(f"count ~ gap * experience + {ctrl}", d, "group_id")
    print("\n[Study 2, Tobit left-censored at 0; SE clustered by user]  (paper Model 2: gap +4.345*, gap x experience -7.239***)")
    print(t2.loc[["gap", "experience", "gap:experience", "len_chars", "has_image", "age"]].round(3).to_string())
    t2.to_csv(out / "replication_tobit_model2.csv")

    # ---------------- Our count specification
    f_nb = lambda rhs: smf.glm("count ~ " + rhs, data=d, family=sm.families.NegativeBinomial(alpha=models._estimate_alpha(d, [rhs])),
                               offset=np.log(d["exposure"])).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d["group_id"])[0]})
    base_rhs = "np.log(len_chars) + C(star_f) + has_image"
    n1, n2 = f_nb(f"gap + experience + {base_rhs}"), f_nb(f"gap * experience + {base_rhs}")
    tab = models.irr_table(n2).loc[["gap", "experience", "gap:experience", "np.log(len_chars)", "has_image"]]
    print("\n[Study 2 analogue, NB2 with log(age) offset; IRR]\n", tab.round(3).to_string())
    tab.to_csv(out / "replication_nb2_model2.csv")

    # ---------------- Extension: gap + LLM content features
    d["sentiment_c"] = d["sentiment"] - 3
    d = d[d["error"].isna()] if "error" in d else d
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
