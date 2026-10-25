"""Engagement-elasticity estimation on SAGraph (Section 6 and Table 7 of the manuscript).

Data: SAGraph (Zhang et al., 2025), CC-BY 4.0. Download the folder
  https://drive.google.com/drive/folders/1_JkyudTJcrrduKx8_G87PocSVSISUZK-
(files <product>_profile.graph.anon and <product>_interaction.graph.anon) and pass its path as --data-dir.

A post is a unique pair (author, post text); y = number of comments and reposts attached to it.
Model: E[y | f, product] = exp(alpha_product + theta * ln f), beta = 1 - theta, estimated by
Poisson pseudo-maximum likelihood (PPML) and by a zero-truncated Poisson (ZTP); SEs clustered by author.
"""
import argparse, json, os
import numpy as np, pandas as pd
import statsmodels.api as sm
from scipy.stats import norm
from statsmodels.discrete.truncated_model import TruncatedLFPoisson

PRODUCTS = ["abc_reading", "electric_toothbrush", "intelligent_floor_scrubber",
            "ruby_face_cream", "spark_thinking", "supor_boosted_showerhead"]


def load_posts(data_dir, product):
    with open(os.path.join(data_dir, f"{product}_profile.graph.anon"), encoding="utf-8") as fh:
        prof = json.load(fh)
    followers = {int(k): v["user_followers"] for k, v in prof.items()}
    ident = {int(k): (v.get("user_description", ""), v.get("user_friends")) for k, v in prof.items()}
    with open(os.path.join(data_dir, f"{product}_interaction.graph.anon"), encoding="utf-8") as fh:
        inter = json.load(fh)
    rows = []
    for author, recs in inter.items():
        a = int(author)
        if a not in followers:
            continue
        counts = {}
        for r in recs:
            key = r["text_raw"]
            c = counts.setdefault(key, [0, 0])
            c[0 if r["interact_type"] == "comment" else 1] += 1
        for key, (nc, nr) in counts.items():
            rows.append((product, a, followers[a], nc, nr, hash(ident[a])))
    df = pd.DataFrame(rows, columns=["product", "author", "followers", "comments", "reposts", "ident"])
    df["y"] = df.comments + df.reposts
    return df


def clusters(d, how):
    """Cluster ids: 'author' = account within product (an account that posts in several campaigns is a separate
    cluster per campaign); 'merged' = likely same account across campaigns (identical description and following
    count, same order of magnitude of followers) share one cluster."""
    if how == "merged":
        key = d["ident"].astype(str) + "|" + np.floor(np.log10(d["followers"].clip(lower=1))).astype(str)
    else:
        key = d["product"] + "|" + d["author"].astype(str)
    return pd.factorize(key)[0]


def fit_ppml(df, ycol="y", fcol="f", cluster="author"):
    X = pd.get_dummies(df["product"], dtype=float)
    X["lnf"] = np.log(df[fcol].to_numpy())
    groups = clusters(df, cluster)
    res = sm.GLM(df[ycol].to_numpy(), X, family=sm.families.Poisson()).fit(
        cov_type="cluster", cov_kwds={"groups": groups})
    th, se = res.params["lnf"], res.bse["lnf"]
    return 1 - th, (1 - th - 1.96 * se, 1 - th + 1.96 * se), se, float(2 * norm.sf(abs((1 - th) / se)))


def fit_ztp(df, ycol="y", fcol="f", cluster="author"):
    d = df[df[ycol] >= 1]
    X = pd.get_dummies(d["product"], dtype=float)
    X["lnf"] = np.log(d[fcol].to_numpy())
    groups = clusters(d, cluster)
    start = sm.GLM(d[ycol].to_numpy(), X, family=sm.families.Poisson()).fit().params.to_numpy()
    res = TruncatedLFPoisson(d[ycol].to_numpy(), X, truncation=0).fit(
        start_params=start, method="bfgs", disp=0, maxiter=500, cov_type="cluster", cov_kwds={"groups": groups})
    th, se = res.params["lnf"], res.bse["lnf"]
    return 1 - th, (1 - th - 1.96 * se, 1 - th + 1.96 * se), se, float(2 * norm.sf(abs((1 - th) / se)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out", default="../results")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    frames = [load_posts(a.data_dir, p) for p in PRODUCTS]
    allp = pd.concat(frames, ignore_index=True)
    allp.to_csv(os.path.join(a.out, "sagraph_posts.csv.gz"), index=False)
    allp["f"] = allp.followers
    rows = []

    def add(name, d, ycol="y", fcol="f", ztp=True, cluster="author"):
        b, ci, se, p = fit_ppml(d, ycol, fcol, cluster)
        row = dict(sample=name, posts=len(d), authors=d[['product','author']].drop_duplicates().shape[0], beta_ppml=b, se=se, p_beta_zero=p, lo=ci[0], hi=ci[1])
        if ztp:
            bz, cz, sez, pz = fit_ztp(d, ycol, fcol, cluster)
            row.update(beta_ztp=bz, se_ztp=sez, lo_ztp=cz[0], hi_ztp=cz[1])
        rows.append(row)
        print(row, flush=True)

    big = allp[allp.f >= 10]
    for p in PRODUCTS:
        add(p, big[big["product"] == p])
    add("Pooled, all accounts (f>=10)", big)
    add("Pooled, 1e3<=f<1e5", big[(big.f >= 1e3) & (big.f < 1e5)])
    add("Pooled, f>=1e5", big[big.f >= 1e5])
    add("Pooled, f in [10,1e3)", big[big.f < 1e3])
    for p in PRODUCTS:
        add(p + ", f>=1e5", big[(big["product"] == p) & (big.f >= 1e5)])
    add("Pooled, all accounts, clusters merged across campaigns", big, cluster="merged")
    # robustness: comments only, floor at 10 followers
    c = big[big.comments >= 1]
    add("Comments only (f>=10)", c, ycol="comments")
    fl = allp.copy(); fl["f"] = fl.f.clip(lower=10)
    add("All accounts, f floored at 10", fl)
    pd.DataFrame(rows).to_csv(os.path.join(a.out, "table7_estimates.csv"), index=False)


if __name__ == "__main__":
    main()
