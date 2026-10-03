"""Notice length, flexibility and time to migration, identified within repositories.
The notice (announcement to shutdown) is constant within a model, so a model fixed effect would absorb it. The same repository, however, often faces several
retirements with different notice lengths; stratifying the Cox model by repository compares the SAME repository across retirements and keeps the notice effect.
Time runs from the announcement; follow-up is cut at the shutdown (a migration after the shutdown is forced and is censored at the notice length), so the
analysis concerns voluntary migration before the deadline. Standard errors are clustered by repository (sandwich). Breslow ties; implemented in numpy.
Real options reading: a longer notice lengthens the option to wait, so the hazard per day should be lower (coefficient on log notice < 0), and migrations should bunch
near the deadline (late share above the uniform expectation).
usage: python analyze_notice.py results\\history_enriched.jsonl [--md out.md] ; python analyze_notice.py --selftest
"""
import argparse, math, sys
import numpy as np, pandas as pd


def cox(t, e, X, strata, cluster, iters=50):
    """Stratified Cox, Breslow. Returns beta, cluster-robust covariance, model-based covariance, loglik."""
    n, p = X.shape; beta = np.zeros(p)
    groups = [np.where(strata == s)[0] for s in np.unique(strata)]
    def pieces(b, want_resid=False):
        ll = 0.0; g = np.zeros(p); H = np.zeros((p, p)); resid = np.zeros((n, p))
        w = np.exp(np.clip(X @ b, -30, 30))
        for idx in groups:
            ts, es, Xs, ws = t[idx], e[idx], X[idx], w[idx]
            for u in np.unique(ts[es == 1]):
                R = ts >= u; D = (ts == u) & (es == 1); d = D.sum()
                S0 = ws[R].sum(); S1 = (ws[R, None] * Xs[R]).sum(0); xbar = S1 / S0
                S2 = (ws[R, None, None] * Xs[R][:, :, None] * Xs[R][:, None, :]).sum(0)
                ll += (Xs[D] @ b).sum() - d * math.log(S0)
                g += Xs[D].sum(0) - d * xbar
                H += d * (S2 / S0 - np.outer(xbar, xbar))
                if want_resid:
                    ri = idx[D]; resid[ri] += Xs[D] - xbar
                    rr = idx[R]; resid[rr] -= (d * ws[R] / S0)[:, None] * (Xs[R] - xbar)
        return ll, g, H, resid
    for _ in range(iters):
        ll, g, H, _ = pieces(beta)
        step = np.linalg.solve(H + 1e-9 * np.eye(p), g); beta = beta + step
        if np.abs(step).max() < 1e-8: break
    ll, g, H, resid = pieces(beta, True); Hi = np.linalg.inv(H + 1e-9 * np.eye(p))
    B = np.zeros((p, p))
    for c in np.unique(cluster):
        s = resid[cluster == c].sum(0); B += np.outer(s, s)
    return beta, Hi @ B @ Hi, Hi, ll


def fit(d, cols, stratify, label, L):
    d = d.dropna(subset=cols + ["lag_c", "event"])
    X = d[cols].to_numpy(float); strata = d.repo.to_numpy() if stratify else np.zeros(len(d), int)
    if stratify:                                     # a repository with a single pair carries no information
        keep = d.groupby("repo").repo.transform("size").to_numpy() > 1; d, X, strata = d[keep], X[keep], strata[keep]
    beta, Vr, Vm, ll = cox(d.lag_c.to_numpy(float), d.event.to_numpy(int), X, strata, d.repo.to_numpy())
    L.append(f"{label}: {len(d)} pairs, {d.repo.nunique()} repos, {int(d.event.sum())} voluntary migrations before shutdown")
    for j, c in enumerate(cols):
        se = math.sqrt(Vr[j, j]); z = beta[j] / se if se > 0 else float("nan"); p = math.erfc(abs(z) / math.sqrt(2))
        L.append(f"   {c:28s} HR {math.exp(beta[j]):6.2f}  95% CI [{math.exp(beta[j] - 1.96 * se):.2f}, {math.exp(beta[j] + 1.96 * se):.2f}]  p = {p:.3f}")
    return beta


def prepare(d):
    d = d.copy(); d["censored"] = d.censored.astype(bool)
    d["event"] = ((~d.censored) & (d.lag_days <= d.notice_days)).astype(int)            # voluntary migration before the shutdown
    d["lag_c"] = np.maximum(np.where(d.event == 1, d.lag_days, d.notice_days).astype(float), 0.5)   # others censored at the shutdown
    d["log_notice"] = np.log(d.notice_days); d["flex_layer"] = d.flex_layer.astype(int)
    d["announce_year"] = pd.to_datetime(d.announced).dt.year + pd.to_datetime(d.announced).dt.dayofyear / 366
    d["log_age"] = np.log1p(d.repo_age_days_at_announcement.clip(lower=0)); d["log_commits90"] = np.log1p(d.commits_prior90)
    return d


def report(d, selftest=False):
    d = prepare(d); L = ["## Notice length and flexibility: voluntary migration before the shutdown (follow-up cut at the deadline)\n",
                         "Hazard ratios per unit of the covariate; log_notice: per one-unit increase in log(days), i.e. doubling the notice multiplies the hazard by HR^0.693.\n"]
    fit(d, ["log_notice"], True, "1. Within repository (strata = repository): notice only", L)
    fit(d, ["log_notice", "flex_layer"], True, "2. Within repository: notice + provider-agnostic layer", L)
    if "flex_level" in d.columns and d.flex_level.notna().any():
        d["flex_cfg"] = (d.flex_level == 1).astype(int); d["flex_lay"] = (d.flex_level == 2).astype(int)
        fit(d, ["log_notice", "flex_cfg", "flex_lay"], True, "3. Within repository: notice + config-only + layer (vs hard-coded)", L)
    fit(d, ["log_notice", "flex_layer", "announce_year"], True, "4. Within repository, adding calendar time of the announcement (retirements get later and notices shorter)", L)
    fit(d, ["log_notice", "flex_layer", "announce_year", "log_age", "log_commits90"], False, "5. Between repositories (no strata), repository age and activity as controls, clustered by repository", L)
    # deadline bunching
    v = d[d.event == 1].copy(); v["pos"] = v.lag_days / v.notice_days
    if len(v):
        v["tercile"] = pd.qcut(v.notice_days.rank(method="first"), 3, labels=["short notice", "medium", "long notice"])
        L.append("\n## Where in the notice window do voluntary migrations happen?\n")
        L.append("Share in the last 20% of the window (uniform timing would give 0.20); a share above 0.20 means migrations bunch toward the deadline.")
        t = v.groupby("tercile", observed=True).agg(n=("pos", "size"), median_notice_days=("notice_days", "median"), median_position=("pos", "median"), share_last20=("pos", lambda x: (x > 0.8).mean()))
        L.append(t.round(2).to_string()); L.append(f"all: n={len(v)}, share in last 20% = {(v.pos > 0.8).mean():.2f}, median position = {v.pos.median():.2f}")
        L.append(f"Hazard per window overall is low: voluntary migration before the shutdown in {d.event.mean():.3f} of pairs.")
    return "\n".join(L)


def selftest():
    rng = np.random.default_rng(3); rows = []
    for r in range(220):
        u = rng.normal(0, 0.7)                                       # repository frailty (shared across its pairs)
        for k, notice in enumerate(rng.choice([91, 182, 365, 458], 3, replace=False)):
            flex = int(rng.random() < 0.3); rate = math.exp(-5.2 + u - 0.8 * math.log(notice / 180) + 0.4 * flex)   # true HR(notice) = exp(-0.8) per log unit
            tt = rng.exponential(1 / rate); ev = tt <= notice + 200
            rows.append(dict(repo=f"r{r}", model=f"m{k}", notice_days=notice, flex_layer=bool(flex), flex_level=2 if flex else 0, censored=not ev, lag_days=min(tt, notice + 200),
                             announced=f"202{3 + k}-0{1 + k}-15", repo_age_days_at_announcement=500, commits_prior90=10, migrated_before_shutdown=ev and tt <= notice))
    d = prepare(pd.DataFrame(rows)); L = []
    b = fit(d, ["log_notice", "flex_layer"], True, "selftest", L)
    print("\n".join(L)); assert abs(b[0] + 0.8) < 0.3 and abs(b[1] - 0.4) < 0.35, b
    assert "Share in the last 20%" in report(pd.DataFrame(rows)); print("selftest ok; true -0.8/0.4, estimated", b.round(2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("path", nargs="?"); ap.add_argument("--md"); ap.add_argument("--selftest", action="store_true"); a = ap.parse_args()
    if a.selftest: selftest(); sys.exit()
    r = report(pd.read_json(a.path, lines=True)); print(r)
    if a.md: open(a.md, "w").write(r + "\n")
