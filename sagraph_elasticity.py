"""Section 5.6 / Appendix B of the DSS manuscript: engagement elasticity and timing calibration.

  python sagraph_elasticity.py --synthetic            # Appendix B check (no data needed)
  python sagraph_elasticity.py --posts posts.csv      # real SAGraph run

posts.csv needs one row per post with columns (names configurable below):
  product, author, followers, n_inter, post_time (hours since epoch or ISO string)
and optionally interactions.csv with one row per comment/repost:
  product, post_id, delay_h, hour_of_day
Build both from the SAGraph release (CC-BY 4.0); the raw layout varies by
version, so adapt `load_sagraph` if your column names differ.
Only numpy / scipy / matplotlib are required.
"""
import argparse, csv, json, os
import numpy as np
from scipy import optimize, stats

OUT = "results"


# ---------------------------------------------------------------- PPML ----
def ppml(y, X, groups, iters=50, tol=1e-10):
    """Poisson pseudo-ML by IRLS with author-clustered (sandwich) SEs."""
    b = np.linalg.lstsq(X, np.log(y + 0.5), rcond=None)[0]   # OLS start
    for _ in range(iters):
        mu = np.exp(np.clip(X @ b, -30, 30))
        z = X @ b + (y - mu) / mu
        W = mu
        XtW = X.T * W
        nb = np.linalg.solve(XtW @ X, XtW @ z)
        if np.max(np.abs(nb - b)) < tol:
            b = nb; break
        b = nb
    mu = np.exp(np.clip(X @ b, -30, 30))
    bread = np.linalg.inv((X.T * mu) @ X)
    score = X * (y - mu)[:, None]
    meat = np.zeros((X.shape[1],) * 2)
    ug = np.unique(groups)
    for g in ug:
        s = score[groups == g].sum(0); meat += np.outer(s, s)
    G, n, k = len(ug), len(y), X.shape[1]
    V = bread @ meat @ bread * (G / (G - 1)) * ((n - 1) / (n - k))
    return b, np.sqrt(np.diag(V))


def estimate_beta(y, f, product, author):
    prods = np.unique(product)
    D = (product[:, None] == prods[None, :]).astype(float)   # product FE (no extra constant)
    X = np.column_stack([np.log(f), D])
    b, se = ppml(y, X, author)
    theta, se_t = b[0], se[0]
    return dict(beta=1 - theta, se=se_t, ci=[1 - theta - 1.96 * se_t, 1 - theta + 1.96 * se_t])


def ols_beta(y, f, product):
    prods = np.unique(product)
    D = (product[:, None] == prods[None, :]).astype(float)
    X = np.column_stack([np.log(f), D])
    b = np.linalg.lstsq(X, np.log1p(y), rcond=None)[0]
    return 1 - b[0]


# -------------------------------------------------------------- timing ----
H = np.arange(24) + 0.5


def profile(p, h=H):
    floor, mu, sd, wmid, sdmid = p
    d = lambda x, m: np.minimum(np.abs(x - m), 24 - np.abs(x - m))
    c = floor + np.exp(-0.5 * (d(h, mu) / sd) ** 2) + wmid * np.exp(-0.5 * (d(h, 12.5) / sdmid) ** 2)
    return c / c.sum()


def fit_profile(hour_counts):
    obs = hour_counts / hour_counts.sum()
    tv = lambda p: 0.5 * np.abs(profile(p) - obs).sum()
    best = None
    for mu0 in (20, 21.5, 23):
        r = optimize.minimize(tv, [0.12, mu0, 2.2, 0.45, 1.8], method="Nelder-Mead",
                              options=dict(maxiter=4000, xatol=1e-4, fatol=1e-8))
        if best is None or r.fun < best.fun: best = r
    p = best.x
    p[2], p[4] = abs(p[2]), abs(p[4])
    return p


def eval_profile(p, hour_counts):
    obs = hour_counts / hour_counts.sum(); fit = profile(p); flat = np.full(24, 1 / 24)
    return dict(tv=0.5 * np.abs(fit - obs).sum(), tv_flat=0.5 * np.abs(flat - obs).sum(),
                r=float(np.corrcoef(fit, obs)[0, 1]))


def fit_delay(delays, cap=48.0):
    d = delays[(delays > 0) & (delays <= cap)]
    ld = np.log(d)
    # truncated log-normal MLE
    def nll(q):
        m, s = q[0], abs(q[1]) + 1e-6
        return -(stats.norm.logpdf(ld, m, s) - np.log(d)).sum() + len(d) * np.log(stats.norm.cdf((np.log(cap) - m) / s))
    r = optimize.minimize(nll, [np.log(np.median(d)), ld.std()], method="Nelder-Mead")
    return r.x[0], abs(r.x[1])


def ks_delay(delays, m, s, cap=48.0):
    d = np.sort(delays[(delays > 0) & (delays <= cap)])
    Fc = stats.norm.cdf((np.log(cap) - m) / s)
    cdf = stats.norm.cdf((np.log(d) - m) / s) / Fc
    n = len(d); e = np.arange(1, n + 1) / n
    return float(max(np.max(e - cdf), np.max(cdf - (e - 1 / n))))


# ---------------------------------------------------------- synthetic -----
def synth(true_beta, seed=0, n_auth=400, n_post=15, n_prod=6, med_delay=0.8, ls=1.2):
    rng = np.random.default_rng(seed)
    f = 10 ** rng.uniform(5, 7, n_auth)
    prod = rng.integers(0, n_prod, n_auth)
    a_fx = rng.normal(0, 0.5, n_auth); p_fx = rng.normal(0, 0.3, n_prod)
    c0 = np.log(0.02)
    rows = []
    hours_by_prod = {k: [] for k in range(n_prod)}; delays_by_prod = {k: [] for k in range(n_prod)}
    true_prof = profile([0.12, 21.5, 2.2, 0.45, 1.8])
    for i in range(n_auth):
        lam_base = np.exp(c0 + p_fx[prod[i]] + a_fx[i]) * (f[i] / 1e5) ** (1 - true_beta)
        for _ in range(n_post):
            mu = lam_base * np.exp(rng.normal(0, 0.6))
            y = rng.poisson(mu)
            rows.append((prod[i], i, f[i], y))
            if y:
                d = np.exp(np.log(med_delay) + ls * rng.standard_normal(y))
                t0 = rng.uniform(0, 24); t = t0 + d
                keep = rng.random(y) < (true_prof[(t % 24).astype(int)] * 24) / (true_prof.max() * 24)
                hours_by_prod[prod[i]] += list(t[keep] % 24); delays_by_prod[prod[i]] += list(d[keep])
    a = np.array(rows)
    return a[:, 0].astype(int), a[:, 1].astype(int), a[:, 2], a[:, 3], hours_by_prod, delays_by_prod


def run_pipeline(product, author, f, y, hours_by_prod, delays_by_prod, label, calib_prods=None):
    res = dict(label=label, n_posts=int(len(y)))
    res["ppml"] = estimate_beta(y, f, product, author)
    res["ols_ln1p"] = ols_beta(y, f, product)
    res["per_product"] = {}
    for k in np.unique(product):
        m = product == k
        if m.sum() > 30 and len(np.unique(author[m])) > 2:
            res["per_product"][str(k)] = estimate_beta(y[m], f[m], product[m], author[m])["beta"]
    keys = sorted(hours_by_prod)
    calib = calib_prods or keys[: len(keys) // 2]
    held = [k for k in keys if k not in calib]
    hc = lambda ks: np.bincount(np.floor(np.concatenate([hours_by_prod[k] for k in ks])).astype(int) % 24, minlength=24).astype(float)
    p = fit_profile(hc(calib))
    res["profile_params"] = dict(zip(["floor", "evening_peak_h", "evening_sd", "midday_w", "midday_sd"], map(float, p)))
    res["heldout_profile"] = eval_profile(p, hc(held))
    dc = np.concatenate([delays_by_prod[k] for k in calib]); dh = np.concatenate([delays_by_prod[k] for k in held])
    m, s = fit_delay(dc)
    res["delay"] = dict(mu=float(m), sigma=float(s), median_h=float(np.exp(m)), heldout_ks=ks_delay(dh, m, s))
    return res, p


def plot_fig3(f, y, hc_obs, p, path):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.6))
    bins = np.quantile(f, np.linspace(0, 1, 11)); idx = np.clip(np.digitize(f, bins) - 1, 0, 9)
    xs = [np.exp(np.log(f[idx == i]).mean()) for i in range(10)]
    ys = [(y[idx == i] / f[idx == i]).mean() for i in range(10)]
    ax[0].loglog(xs, ys, "o-"); ax[0].set_xlabel("followers"); ax[0].set_ylabel("interactions per follower")
    ax[0].set_title("(a) binned elasticity")
    ax[1].bar(H, hc_obs / hc_obs.sum(), width=0.9, alpha=.5, label="observed"); ax[1].plot(H, profile(p), "k-", label="fitted")
    ax[1].set_xlabel("hour"); ax[1].set_title("(b) held-out daily profile"); ax[1].legend()
    fig.tight_layout(); fig.savefig(path, dpi=200); plt.close(fig)


def load_sagraph(posts_csv, inter_csv):
    P = list(csv.DictReader(open(posts_csv)))
    prods = {k: i for i, k in enumerate(sorted({r["product"] for r in P}))}
    product = np.array([prods[r["product"]] for r in P]); auth = {a: i for i, a in enumerate({r["author"] for r in P})}
    author = np.array([auth[r["author"]] for r in P])
    f = np.array([float(r["followers"]) for r in P]); y = np.array([float(r["n_inter"]) for r in P])
    ok = f > 0
    hb = {i: [] for i in prods.values()}; db = {i: [] for i in prods.values()}
    if inter_csv:
        for r in csv.DictReader(open(inter_csv)):
            k = prods[r["product"]]; hb[k].append(float(r["hour_of_day"]) % 24); db[k].append(float(r["delay_h"]))
    return product[ok], author[ok], f[ok], y[ok], hb, db


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--posts"); ap.add_argument("--interactions")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    out = {}
    if a.synthetic:
        for tb in (0.0, 0.35):
            prod, auth, f, y, hb, db = synth(tb)
            r, _ = run_pipeline(prod, auth, f, y, hb, db, f"synthetic beta={tb}")
            r["true_beta"] = tb; out[f"synthetic_{tb}"] = r
            print(json.dumps(r, indent=1))
    if a.posts:
        prod, auth, f, y, hb, db = load_sagraph(a.posts, a.interactions)
        r, p = run_pipeline(prod, auth, f, y, hb, db, "SAGraph")
        out["sagraph"] = r; print(json.dumps(r, indent=1))
        if a.interactions:
            keys = sorted(hb); held = keys[len(keys) // 2:]
            hc = np.bincount(np.floor(np.concatenate([hb[k] for k in held])).astype(int) % 24, minlength=24).astype(float)
            plot_fig3(f, y, hc, p, f"{OUT}/fig3_sagraph.png")
        b = r["ppml"]
        print("\nRe-run Section 5.5 at beta =", [round(max(b['ci'][0], 0), 3), round(b['beta'], 3), round(b['ci'][1], 3)],
              "(thresholds: 0.1 / 0.25)")
    json.dump(out, open(f"{OUT}/sagraph_elasticity.json", "w"), indent=1)


if __name__ == "__main__":
    main()
