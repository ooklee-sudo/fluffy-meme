"""Analysis of the history-persona experiment (stage 1). No API calls.

  python history_analysis.py --runs runs_history --boot 500            # real data
  python history_analysis.py --runs /tmp/rh --mock-data --boot 50      # pipeline test with synthetic data

Computes baselines (NBD posterior mean from earlier windows, previous-window count, training mean, gradient boosting with
structured features and with TF-IDF category text), and the pre-registered quantities:
  P1 c^2 of lambda by information level; P2 Spearman rho with the real count; P3 capability x information interaction
  (primary); P4 incremental value of log(lambda) over log(NBD posterior mean) in a Poisson regression (primary);
  P5 alpha_w from Proposition 2 and the variance reproduced by the hybrid. All intervals: household-cluster bootstrap.
"""
import argparse, glob, json, os, re
import numpy as np, pandas as pd
from scipy import optimize, special, stats
import statsmodels.api as sm
import history_data as hd

CAPS = ("small", "large")


# ------------------------------------------------------------------ baselines
def nbd_fit(y):
    """y: households x k prior windows. Gamma-Poisson with shape r and rate b: marginal likelihood of the sums."""
    S = y.sum(1); k = y.shape[1]
    def nll(p):
        r, b = np.exp(p)
        return -(special.gammaln(r + S) - special.gammaln(r) + r * np.log(b) - (r + S) * np.log(b + k)).sum()
    res = optimize.minimize(nll, [0.0, -1.0], method="Nelder-Mead")
    return np.exp(res.x)


def nbd_posterior(counts, h, t):
    prior = counts[:, :t]
    r, b = nbd_fit(prior)
    return (r + prior[h].sum()) / (b + t)


def text_of(cats, h, t):
    cn = sum((cats[h][k] for k in range(max(0, t - 3), t)), start=type(cats[h][0])())
    return " ".join(c.replace(" ", "_") for c, _ in cn.most_common(8))


def gbm_oof(demo, counts, recency, cats, text=False, seed=0):
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.model_selection import GroupKFold
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import TruncatedSVD
    rows = [(h, t) for h in range(counts.shape[0]) for t in range(3, 13)]
    D = demo.drop(columns=["household_id"]).astype("category").apply(lambda c: c.cat.codes).values
    X = np.array([[counts[h, t-1], counts[h, t-2], counts[h, t-3], counts[h, :t].sum(), np.nan_to_num(recency[h, t], nan=400.0), t, *D[h]] for h, t in rows], float)
    if text:
        docs = [text_of(cats, h, t) for h, t in rows]
        tf = TfidfVectorizer(min_df=2).fit_transform(docs)
        k = max(1, min(20, tf.shape[1] - 1))
        X = np.hstack([X, TruncatedSVD(k, random_state=seed).fit_transform(tf)])
    y = np.array([counts[h, t] for h, t in rows], float); g = np.array([h for h, _ in rows])
    pred = np.zeros(len(rows))
    for tr, te in GroupKFold(5).split(X, y, g):
        pred[te] = HistGradientBoostingRegressor(loss="poisson", max_iter=150, random_state=seed).fit(X[tr], y[tr]).predict(X[te])
    return {(h, t): p for (h, t), p in zip(rows, pred)}


def pdev(y, mu):
    mu = np.maximum(mu, 1e-6); y = np.asarray(y, float)
    return 2 * np.mean(np.where(y > 0, y * np.log(np.where(y > 0, y, 1) / mu), 0) - (y - mu))


# ------------------------------------------------------------------ bootstrap
def cluster_boot(df, f, B, rng):
    ids = df.hh.unique(); idx = {h: g.index.values for h, g in df.groupby("hh")}
    est = f(df); out = []
    for _ in range(B):
        pick = rng.choice(ids, len(ids))
        out.append(f(df.loc[np.concatenate([idx[h] for h in pick])]))
    out = np.array(out, float)
    return est, np.nanpercentile(out, [2.5, 97.5], axis=0)


def fmt(e, ci):
    e = np.atleast_1d(e); lo, hi = np.atleast_2d(ci)[0] if np.ndim(ci) == 1 else ci
    return ", ".join(f"{x:+.3f} [{l:+.3f},{h:+.3f}]" for x, l, h in zip(e, np.atleast_1d(lo), np.atleast_1d(hi)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs_history"); ap.add_argument("--boot", type=int, default=500)
    ap.add_argument("--mock-data", action="store_true")
    a = ap.parse_args()
    rng = np.random.default_rng(0)
    demo, counts, recency, cats = hd.load(a.mock_data)
    samples = pd.concat([pd.read_csv(f).assign(seed=int(re.search(r"_s(\d+)\.csv", f).group(1))) for f in glob.glob(os.path.join(a.runs, "sample_s*.csv"))])
    raw = pd.concat([pd.read_csv(f) for f in glob.glob(os.path.join(a.runs, "*_L*_s*.csv"))])
    D = raw[raw.design == "D"].merge(samples, on=["seed", "i"])
    D = D.dropna(subset=["value"]).reset_index(drop=True)
    D["cell"] = D.model + "|" + D.wording + "|" + D.level.astype(str)
    # baselines
    nbd_cache = {}
    def nbd(h, t):
        if t not in nbd_cache:
            nbd_cache[t] = nbd_fit(counts[:, :t])
        r, b = nbd_cache[t]; return (r + counts[h, :t].sum()) / (b + t)
    g1 = gbm_oof(demo, counts, recency, cats, False); g2 = gbm_oof(demo, counts, recency, cats, True)
    D["nbd"] = [nbd(h, t) for h, t in zip(D.hh, D.win)]
    D["last"] = np.maximum(D.prev1, 0.05); D["gmean"] = [counts[:, :t].mean() for t in D.win]
    D["gbm"] = [g1[(h, t)] for h, t in zip(D.hh, D.win)]; D["gbm_text"] = [g2[(h, t)] for h, t in zip(D.hh, D.win)]
    D["lam"] = D.value
    # mean-calibrated lambda within cell (pre-specified comparison form)
    D["lam_cal"] = D.lam * D.groupby("cell").real.transform("mean") / D.groupby("cell").lam.transform("mean")
    print("rows", len(D), "households", D.hh.nunique(), "cells", D.cell.nunique())

    # ---- descriptive: baselines vs LLM at each level
    print("\nPoisson deviance (lower is better) and Spearman rho with the real count, by method")
    rows = []
    for name in ("gmean", "last", "nbd", "gbm", "gbm_text"):
        x = D.drop_duplicates(["seed", "i"])
        rows.append(dict(method=name, level="-", cap="-", dev=pdev(x.real, x[name]), rho=stats.spearmanr(x[name], x.real)[0] if x[name].nunique() > 1 else np.nan))
    for (cap, lv), g in D.groupby(["cap", "level"]):
        rows.append(dict(method="LLM raw", level=lv, cap=cap, dev=pdev(g.real, g.lam), rho=stats.spearmanr(g.lam, g.real)[0]))
        rows.append(dict(method="LLM mean-calibrated", level=lv, cap=cap, dev=pdev(g.real, g.lam_cal), rho=stats.spearmanr(g.lam_cal, g.real)[0]))
    print(pd.DataFrame(rows).round(3).to_string(index=False))

    # ---- P1, P2
    def c2(g): return g.lam.var() / g.lam.mean() ** 2
    def by_level(df, fn):
        return np.array([np.nanmean([fn(g) for _, g in df[df.level == lv].groupby("cell")]) for lv in (1, 2, 3, 4)])
    p1 = lambda df: by_level(df, c2)
    p2 = lambda df: by_level(df, lambda g: stats.spearmanr(g.lam, g.real)[0] if g.lam.nunique() > 1 else np.nan)
    for name, f in (("P1 mean c^2 of lambda by level L1..L4", p1), ("P2 mean Spearman rho(lambda, real) by level L1..L4", p2)):
        e, ci = cluster_boot(D, lambda d: np.append(f(d), f(d)[3] - f(d)[0]), a.boot, rng)
        print(f"\n{name}: " + " | ".join(f"{x:.3f} [{l:.3f},{h:.3f}]" for x, l, h in zip(e, ci[0], ci[1])) + "   (last = L4 minus L1)")

    # ---- P3 (primary): capability x information interaction on rho
    def rho_cl(df, cap, lv):
        v = [stats.spearmanr(g.lam, g.real)[0] for _, g in df[(df.cap == cap) & (df.level == lv)].groupby("cell") if g.lam.nunique() > 1]
        return np.mean(v) if v else np.nan
    p3 = lambda df: (rho_cl(df, "large", 4) - rho_cl(df, "small", 4)) - (rho_cl(df, "large", 1) - rho_cl(df, "small", 1))
    e, ci = cluster_boot(D, p3, a.boot, rng)
    print(f"\nP3 PRIMARY interaction [rho(large,L4)-rho(small,L4)] - [rho(large,L1)-rho(small,L1)]: {e:+.3f} [{ci[0]:+.3f},{ci[1]:+.3f}]  (two-sided 95% household-cluster bootstrap)")

    # ---- P4 (primary): incremental value of log(lambda) over log(NBD posterior mean)
    def p4(df, lv):
        d = df[df.level == lv]
        X = sm.add_constant(np.column_stack([np.log(np.maximum(d.nbd, 1e-3)), np.log(np.maximum(d.lam, 1e-3))]))
        try:
            return sm.GLM(d.real.values, X, family=sm.families.Poisson()).fit().params[2]
        except Exception:
            return np.nan
    print("\nP4 coefficient on log(lambda) controlling for log(NBD posterior mean); PRIMARY = level L4, all cells pooled")
    for lv in (1, 2, 3, 4):
        e, ci = cluster_boot(D, lambda d: p4(d, lv), a.boot, rng)
        print(f"  L{lv}: {e:+.3f} [{ci[0]:+.3f},{ci[1]:+.3f}]" + ("   <-- primary" if lv == 4 else ""))
    # ---- P5
    allr = np.array([counts[h, t] for h in range(counts.shape[0]) for t in range(3, 13)], float)
    a_ref = (allr.var() - allr.mean()) / allr.mean() ** 2; vm_ref = allr.var() / allr.mean()
    print(f"\nP5 reference over all household-windows t>=3: alpha={a_ref:.3f}, var/mean={vm_ref:.3f}")
    cell = D.groupby("cell").apply(lambda g: pd.Series(dict(level=g.level.iloc[0], c2=c2(g)))).reset_index()
    cell["alpha_w"] = np.maximum((1 + a_ref) / (1 + cell.c2) - 1, 0.01)
    print("  alpha_w by level:", cell.groupby("level").alpha_w.mean().round(3).to_dict(), " Spearman(level, alpha_w) =", round(stats.spearmanr(cell.level, cell.alpha_w)[0], 3))
    def hyb(df, lv):
        vals = []
        for _, g in df[df.level == lv].groupby("cell"):
            aw = max((1 + a_ref) / (1 + c2(g)) - 1, 0.01)
            r2 = np.random.default_rng(7); n = r2.poisson(g.lam.values * r2.gamma(1 / aw, aw, len(g)))
            vals.append(n.var() / n.mean() / vm_ref)
        return np.mean(vals)
    for lv in (1, 2, 3, 4):
        e, ci = cluster_boot(D, lambda d: hyb(d, lv), max(20, a.boot // 5), rng)
        print(f"  hybrid var/mean divided by reference, L{lv}: {e:.3f} [{ci[0]:.3f},{ci[1]:.3f}]")

    # ---- narrative branch (pre-specified rule), level L4, large models, mean-calibrated lambda
    g = D[(D.level == 4) & (D.cap == "large")]
    def dev_diff(d, other):
        dd = d[d.level == 4]
        dd = dd[dd.cap == "large"]
        return pdev(dd.real, dd.lam_cal) - pdev(dd.real, dd[other])
    print("\nBranch rule at L4 (large models, mean-calibrated lambda): deviance difference LLM minus baseline (negative = LLM better)")
    verdict = {}
    for other in ("nbd", "gbm_text"):
        e, ci = cluster_boot(D, lambda d: dev_diff(d, other), a.boot, rng)
        verdict[other] = (e, ci)
        print(f"  vs {other}: {e:+.4f} [{ci[0]:+.4f},{ci[1]:+.4f}]")
    (en, cn), (eg, cg) = verdict["nbd"], verdict["gbm_text"]
    if cn[1] < 0 and cg[1] < 0: print("  => LLM beats both NBD and GBM: central narrative = conditions under which the LLM contributes")
    elif cn[0] > 0: print("  => LLM worse than NBD: central narrative = the validation layer is the artifact's core")
    else: print("  => LLM similar to NBD: central narrative = the LLM rediscovers empirical Bayes")


if __name__ == "__main__":
    main()
