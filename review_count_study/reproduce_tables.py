"""Recompute the manuscript's tables from the replication data (no raw text, no LLM calls).

Inputs (data/): analysis_table.csv  (review-level ids, ratings, votes, controls, category-level labels and the six
columns stars_llm_<prompt>_<llm>) and product_labels.csv (product-level LLM labels).
Outputs (printed and written to --out): numbers.json and tables.md with Table 1, Table 2, Web Appendix C and D.
Usage: python reproduce_tables.py --data-dir data --out results [--procs 4]
Runtime: a few minutes (24 Tobit fits). Standard errors are clustered by product (parent_asin).
"""
import argparse
import json
import multiprocessing as mp
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

import models
from tobit import fit_tobit

COMBOS = [("ours", "claude"), ("ours", "llama"), ("ours", "gpt"), ("orig", "claude"), ("orig", "llama"), ("orig", "gpt")]
NAMES = {"claude": "Claude Haiku 5.5", "llama": "Llama 3.3 70B", "gpt": "GPT-4.1 nano"}
BASE = "np.log(len_chars) + C(star_f) + has_image"
TB = "len_chars + C(star_f) + has_image + age"
T = None; LAB = None


def init(data_dir):
    global T, LAB
    T = pd.read_csv(Path(data_dir) / "analysis_table.csv")
    LAB = pd.read_csv(Path(data_dir) / "product_labels.csv")[["parent_asin", "good_type", "motive"]].dropna()
    T["experience"] = (T["category"] == "experience").astype(int)  # category-level assumption


def prep(prompt, llm, product):
    d = T.copy()
    d["stars_llm"] = d[f"stars_llm_{prompt}_{llm}"]
    d = d.dropna(subset=["stars_llm"]).copy()
    d["gap"] = (d["stars"] - d["stars_llm"]).abs()
    d["exposure"] = d["days_since_post"].clip(lower=1); d["age"] = d["exposure"]; d["star_f"] = d["stars"].astype(int)
    if product:
        d = d.merge(LAB, on="parent_asin", how="inner")
        d["experience"] = (d["good_type"] == "experience").astype(int); d["hedonic"] = (d["motive"] == "hedonic").astype(int)
    return d


def nb(d, rhs, group="parent_asin"):
    al = models._estimate_alpha(d, [rhs])
    return smf.glm("count ~ " + rhs, data=d, family=sm.families.NegativeBinomial(alpha=al), offset=np.log(d["exposure"])).fit(
        cov_type="cluster", cov_kwds={"groups": pd.factorize(d[group])[0]})


def one(job):
    prompt, llm, product = job
    d = prep(prompt, llm, product)
    out = dict(prompt=prompt, llm=llm, labels="product" if product else "category", N=len(d),
               r=float(np.corrcoef(d.stars, d.stars_llm)[0, 1]), exact=float((d.gap == 0).mean()), off2=float((d.gap >= 2).mean()))
    g = d.groupby("star_f").gap.mean(); out["gap_star1"], out["gap_star3"] = float(g[1]), float(g[3])
    o = smf.ols("gap ~ hedonic + C(star_f) + len_chars + age", data=d).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.parent_asin)[0]})
    out["hed"], out["hed_p"] = float(o.params["hedonic"]), float(o.pvalues["hedonic"])
    t1 = fit_tobit(f"count ~ gap + experience + {TB}", d, "parent_asin"); t2 = fit_tobit(f"count ~ gap * experience + {TB}", d, "parent_asin")
    out.update(tob1=float(t1.loc["gap", "coef"]), tob1_p=float(t1.loc["gap", "p"]), tob2=float(t2.loc["gap", "coef"]), tob2_p=float(t2.loc["gap", "p"]),
               tobi=float(t2.loc["gap:experience", "coef"]), tobi_p=float(t2.loc["gap:experience", "p"]))
    m1 = nb(d, f"gap + experience + {BASE}"); m2 = nb(d, f"gap * experience + {BASE}")
    for tag, m, k in (("nb1", m1, "gap"), ("nb2", m2, "gap"), ("nbi", m2, "gap:experience")):
        ci = np.exp(m.conf_int().loc[k])
        out[tag] = float(np.exp(m.params[k])); out[tag + "_lo"], out[tag + "_hi"], out[tag + "_p"] = float(ci[0]), float(ci[1]), float(m.pvalues[k])
    mu = nb(d, f"gap * experience + {BASE}", group="group_id"); out["nbi_user_p"] = float(mu.pvalues["gap:experience"])
    if True:
        z = models.zero_inflation_check(d.assign(exposure=d["exposure"]))
        out.update(zi_nb_llf=z["nb_llf"], zi_zi_llf=z["zinb_llf"], zi_nb_aic=z["nb_aic"], zi_zi_aic=z["zinb_aic"], zi_p0=z["p_structural_zero"])
    return out


def pf(p): return "<.001" if p < .0005 else f"{p:.3f}".lstrip("0")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data"); ap.add_argument("--out", default="results"); ap.add_argument("--procs", type=int, default=4)
    ap.add_argument("--dump-model-data", help="only write the six model-ready product-level data files (input of misclass_sensitivity.py) to this folder and exit")
    a = ap.parse_args()
    if a.dump_model_data:
        init(a.data_dir); Path(a.dump_model_data).mkdir(parents=True, exist_ok=True)
        cols = ["review_id", "parent_asin", "count", "gap", "experience", "hedonic", "len_chars", "star_f", "has_image", "exposure", "age", "stars", "stars_llm"]
        for p, l in COMBOS:
            prep(p, l, True)[cols].to_csv(Path(a.dump_model_data) / f"{p}_{l}.csv", index=False)
        print("wrote", len(COMBOS), "files to", a.dump_model_data); return
    Path(a.out).mkdir(exist_ok=True)
    jobs = [(p, l, prod) for (p, l) in COMBOS for prod in (False, True)]
    with mp.Pool(a.procs, initializer=init, initargs=(a.data_dir,)) as pool:
        res = pool.map(one, jobs)
    R = pd.DataFrame(res); R.to_csv(Path(a.out) / "numbers.csv", index=False)
    key = lambda p, l, lab: R[(R.prompt == p) & (R.llm == l) & (R.labels == lab)].iloc[0]
    L = []
    L.append("TABLE 1\n| Prompt | LLM | r | Exact match | Hedonic coef., category (p) | Hedonic coef., product (p) |\n|---|---|---|---|---|---|")
    for p, l in COMBOS:
        c, q = key(p, l, "category"), key(p, l, "product")
        L.append(f"| {'Ours' if p=='ours' else 'Original'} | {NAMES[l]} | {c.r:.3f}".replace("0.", ".") + f" | {c.exact:.1%} | {c.hed:+.3f} ({pf(c.hed_p)}) | {q.hed:+.3f} ({pf(q.hed_p)}) |".replace("+0.", "+.").replace("-0.", "−."))
    L.append("\nTABLE 2\n| Prompt | LLM | Gap IRR, Model 1 (category) | Gap × experience IRR (category) | Gap IRR, Model 1 (product) | Gap × experience IRR (product) |\n|---|---|---|---|---|---|")
    for p, l in COMBOS:
        c, q = key(p, l, "category"), key(p, l, "product")
        L.append(f"| {'Ours' if p=='ours' else 'Original'} | {NAMES[l]} | {c.nb1:.2f} ({pf(c.nb1_p)}) | {c.nbi:.2f} ({pf(c.nbi_p)}) | {q.nb1:.2f} ({pf(q.nb1_p)}) | {q.nbi:.2f} ({pf(q.nbi_p)}) |")
    L.append("\nWEB APPENDIX C\n| Prompt | LLM | Goods labels | Tobit M1 gap | Tobit M2 gap | Tobit M2 gap × exp | NB2 M1 gap IRR | NB2 M2 gap IRR | NB2 M2 gap × exp IRR |\n|---|---|---|---|---|---|---|---|---|")
    for lab in ("category", "product"):
        for p, l in COMBOS:
            c = key(p, l, lab)
            L.append(f"| {p.replace('orig','original')} | {NAMES[l]} | {lab} | {c.tob1:.2f} ({pf(c.tob1_p)}) | {c.tob2:.2f} ({pf(c.tob2_p)}) | {c.tobi:.2f} ({pf(c.tobi_p)}) | {c.nb1:.2f} [{c.nb1_lo:.2f}, {c.nb1_hi:.2f}] | {c.nb2:.2f} [{c.nb2_lo:.2f}, {c.nb2_hi:.2f}] | {c.nbi:.2f} [{c.nbi_lo:.2f}, {c.nbi_hi:.2f}] |")
    L.append("\nWEB APPENDIX D\n| Prompt | LLM | Goods labels | logLik NB2 | logLik ZINB | AIC NB2 / ZINB | Implied P(structural zero) |\n|---|---|---|---|---|---|---|")
    for lab in ("category", "product"):
        for p, l in COMBOS:
            c = key(p, l, lab)
            L.append(f"| {p.replace('orig','original')} | {NAMES[l]} | {lab} | {c.zi_nb_llf:.2f} | {c.zi_zi_llf:.2f} | {c.zi_nb_aic:.1f} / {c.zi_zi_aic:.1f} | {c.zi_p0:.2e} |")
    (Path(a.out) / "tables.md").write_text("\n".join(L))
    print("\n".join(L))


if __name__ == "__main__":
    main()
