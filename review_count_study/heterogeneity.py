"""Mechanism and robustness analyses for the gap effect (no LLM calls): ensemble gap, star-rating strata, signed gap,
winsorized votes, and the ensemble gap x experience interaction. NB2 with log review age as offset, clustered by product.
Usage: python heterogeneity.py --data-dir data --prompt ours --out results
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

import models

BASE = "np.log(len_chars) + C(star_f) + has_image"
BASE_STRATUM = "np.log(len_chars) + has_image"  # rating dummies are constant within a stratum


def fit(d, rhs, y="count"):
    al = models._estimate_alpha(d.assign(count=d[y]), [rhs])
    return smf.glm(f"{y} ~ " + rhs, data=d, family=sm.families.NegativeBinomial(alpha=al), offset=np.log(d["exposure"])).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(d["parent_asin"])[0]})


def row(label, m, term, n):
    ci = np.exp(m.conf_int().loc[term])
    return dict(spec=label, N=int(n), irr=float(np.exp(m.params[term])), lo=float(ci[0]), hi=float(ci[1]), p=float(m.pvalues[term]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data"); ap.add_argument("--prompt", default="ours"); ap.add_argument("--out", default="results")
    a = ap.parse_args()
    t = pd.read_csv(Path(a.data_dir) / "analysis_table.csv")
    lab = pd.read_csv(Path(a.data_dir) / "product_labels.csv")[["parent_asin", "good_type"]].dropna()
    cols = [f"stars_llm_{a.prompt}_{l}" for l in ("claude", "llama", "gpt")]
    d = t.dropna(subset=cols).copy()
    d["stars_ens"] = d[cols].mean(axis=1)
    d["gap"] = (d.stars - d.stars_ens).abs()
    d["up"] = (d.stars_ens - d.stars).clip(lower=0)      # LLM reads the text as more positive than the author's rating
    d["down"] = (d.stars - d.stars_ens).clip(lower=0)    # LLM reads the text as more negative than the author's rating
    d["exposure"] = d.days_since_post.clip(lower=1); d["star_f"] = d.stars.astype(int)
    q = d["count"].quantile(0.999); d["count_w"] = d["count"].clip(upper=q)
    d = d.merge(lab, on="parent_asin", how="inner"); d["experience"] = (d.good_type == "experience").astype(int)
    R = []
    R.append(row("Ensemble gap, all reviews", fit(d, f"gap + {BASE}"), "gap", len(d)))
    R.append(row(f"Ensemble gap, votes winsorized at the 99.9th percentile ({q:.0f})", fit(d, f"gap + {BASE}", y="count_w"), "gap", len(d)))
    m = fit(d, f"gap * experience + {BASE}")
    R.append(row("Ensemble gap, search goods (product labels)", m, "gap", len(d)))
    R.append(row("Ensemble gap x experience (product labels)", m, "gap:experience", len(d)))
    for s in range(1, 6):
        ds = d[d.star_f == s]
        R.append(row(f"Ensemble gap, {s}-star reviews", fit(ds, f"gap + {BASE_STRATUM}"), "gap", len(ds)))
    mm = fit(d, f"up + down + {BASE}")
    R.append(row("LLM more positive than author's rating (per star)", mm, "up", len(d)))
    R.append(row("LLM more negative than author's rating (per star)", mm, "down", len(d)))
    c = mm.cov_params(); diff = mm.params["down"] - mm.params["up"]; se = float(np.sqrt(c.loc["down", "down"] + c.loc["up", "up"] - 2 * c.loc["down", "up"]))
    from scipy.stats import norm
    R.append(dict(spec="Ratio: more-negative / more-positive reading", N=len(d), irr=float(np.exp(diff)), lo=float(np.exp(diff - 1.96 * se)), hi=float(np.exp(diff + 1.96 * se)), p=float(2 * norm.sf(abs(diff / se)))))
    for s_ in (1, 2, 3, 4):
        ds = d[d.star_f == s_]
        if ds.up.gt(0).sum() > 30 and ds.down.gt(0).sum() > 30:
            ms = fit(ds, f"up + down + {BASE_STRATUM}")
            R.append(row(f"{s_}-star: LLM more positive than rating (per star)", ms, "up", len(ds)))
            R.append(row(f"{s_}-star: LLM more negative than rating (per star)", ms, "down", len(ds)))
    Rd = pd.DataFrame(R); Path(a.out).mkdir(exist_ok=True); Rd.to_csv(Path(a.out) / f"heterogeneity_{a.prompt}.csv", index=False)
    d["gap_share_mid"] = d.star_f.isin([2, 3, 4])
    print(f"prompt {a.prompt}: N={len(d)}; share of reviews by star: {d.star_f.value_counts(normalize=True).sort_index().round(3).to_dict()}; mean ensemble gap by star: {d.groupby('star_f').gap.mean().round(2).to_dict()}")
    print(Rd.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
