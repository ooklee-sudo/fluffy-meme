"""Online Appendix B: recovery of known parameters on synthetic campaign data (Table B.1).

Synthetic data mimic an influencer-campaign dataset with timestamps: 400 authors with follower counts drawn
log-uniformly between 1e5 and 1e7, six products, 15 posts per author over 60 days, author and product random effects,
post-level noise, log-normal reply delays (median 0.8 h, log-sd 1.2), and interaction times thinned by a known daily
profile with an evening peak at 21:30. Estimators: PPML (and OLS on ln(1+y) for comparison) for beta; a grid search
for the evening peak of the daily profile on three calibration products, evaluated on three held-out products.
The generating counts follow E[y] = exp(c + a_author + a_product + (1 - beta) ln f + e) with e ~ N(0, 0.5^2);
the unspecified scale constants (random-effect sds, intercept) are our choices and are listed in the code.
"""
import argparse, os
import numpy as np, pandas as pd
import statsmodels.api as sm

from simulator import circadian_table

SD_AUTHOR, SD_PRODUCT, SD_POST, INTERCEPT = 0.8, 0.3, 0.5, -9.0
N_AUTHORS, N_PRODUCTS, POSTS, DAYS = 400, 6, 15, 60


def simulate(beta, rng):
    f = np.exp(rng.uniform(np.log(1e5), np.log(1e7), N_AUTHORS))
    prod_of_author = rng.integers(0, N_PRODUCTS, N_AUTHORS)
    a_auth = rng.normal(0, SD_AUTHOR, N_AUTHORS); a_prod = rng.normal(0, SD_PRODUCT, N_PRODUCTS)
    rows, times = [], []
    profile = circadian_table(21.5)  # known daily profile, evening peak at 21:30
    for i in range(N_AUTHORS):
        for _ in range(POSTS):
            mu = np.exp(INTERCEPT + a_auth[i] + a_prod[prod_of_author[i]] + (1 - beta) * np.log(f[i]) + rng.normal(0, SD_POST))
            raw_y = rng.poisson(mu)
            t_post = rng.uniform(0, DAYS * 24)
            delays = rng.lognormal(np.log(0.8), 1.2, raw_y)
            t = t_post + delays
            keep = rng.random(raw_y) < profile[((t % 24) * 4).astype(int) % 96] / profile.max()  # thinning by the daily profile
            rows.append((i, prod_of_author[i], f[i], int(keep.sum())))
            times.extend(zip([prod_of_author[i]] * int(keep.sum()), (t[keep] % 24), delays[keep]))
    return pd.DataFrame(rows, columns=["author", "product", "f", "y"]), pd.DataFrame(times, columns=["product", "hour", "delay"])


def fit_beta(df):
    X = pd.get_dummies(df["product"], dtype=float); X["lnf"] = np.log(df["f"])
    r = sm.GLM(df["y"], X, family=sm.families.Poisson()).fit(cov_type="cluster", cov_kwds={"groups": df["author"]})
    ppml = (1 - r.params["lnf"], 1 - r.params["lnf"] - 1.96 * r.bse["lnf"], 1 - r.params["lnf"] + 1.96 * r.bse["lnf"])
    ols = sm.OLS(np.log1p(df["y"]), X).fit()
    return ppml, 1 - ols.params["lnf"]


def hourly(times, products):
    h = times[times["product"].isin(products)]["hour"]
    c, _ = np.histogram(h, bins=np.arange(0, 25)); return c / c.sum()


def profile_dist(mu):
    p = circadian_table(mu).reshape(24, 4).mean(axis=1); return p / p.sum()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default="../results"); ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    rng = np.random.default_rng(a.seed); out = []
    for beta in (0.0, 0.35):
        df, tm = simulate(beta, rng)
        (b, lo, hi), b_ols = fit_beta(df)
        calib, held = [0, 1, 2], [3, 4, 5]
        obs_c = hourly(tm, calib)
        grid = np.arange(18.0, 24.01, 0.1)
        tv = [0.5 * np.abs(profile_dist(m) - obs_c).sum() for m in grid]
        mu_hat = float(grid[int(np.argmin(tv))])
        obs_h = hourly(tm, held)
        tv_held = 0.5 * np.abs(profile_dist(mu_hat) - obs_h).sum(); tv_flat = 0.5 * np.abs(np.full(24, 1 / 24) - obs_h).sum()
        r = float(np.corrcoef(profile_dist(mu_hat), obs_h)[0, 1])
        med = float(np.median(tm[tm["product"].isin(calib)]["delay"]))
        out.append(dict(true_beta=beta, posts=len(df), ppml=round(b, 3), ppml_lo=round(lo, 3), ppml_hi=round(hi, 3), ols_ln1p=round(b_ols, 3),
                        fitted_evening_peak=round(mu_hat, 1), heldout_tv=round(tv_held, 3), flat_tv=round(tv_flat, 3), heldout_r=round(r, 3),
                        fitted_delay_median=round(med, 2)))
        print(out[-1])
    pd.DataFrame(out).to_csv(os.path.join(a.out, "tableB1_validation.csv"), index=False)


if __name__ == "__main__":
    main()
