"""Analysis of results/history.jsonl from mine_by_history.py.
Tables: (1) per model: repositories at risk, migrated before the shutdown, Kaplan-Meier share unmigrated at shutdown, median lag of migrated;
(2) H1: time to migration by flexibility proxy (provider-agnostic layer at the announcement date), stratified log-rank test and crude rate ratio;
(3) H5: size of the migration commit by flexibility proxy (migrated repositories only); (4) H4: lag against notice length.
Repositories can appear for several models, so p-values are indicative only; cluster by repository in a full model (Cox with robust errors).
usage: python analyze_history.py results\\history.jsonl [--md out.md] ; python analyze_history.py --selftest
"""
import argparse, math, sys
import numpy as np, pandas as pd


def km_at(lag, ev, t):
    lag, ev = np.asarray(lag, float), np.asarray(ev, int); s = 1.0
    for u in np.unique(lag[(ev == 1) & (lag <= t)]):
        s *= 1 - ((lag == u) & (ev == 1)).sum() / (lag >= u).sum()
    return s


def logrank_stratified(d, group_col):
    """Stratified (by model) log-rank test for two groups (True/False). Returns chi2, p, observed/expected for the True group and for the False group."""
    O1 = E1 = V = O0 = E0 = 0.0
    for _, g in d.groupby("model"):
        times = np.unique(g.loc[~g.censored, "lag_days"])
        for t in times:
            risk = g[g.lag_days >= t]; n = len(risk); n1 = risk[group_col].sum()
            dd = ((g.lag_days == t) & (~g.censored)).sum(); d1 = ((g.lag_days == t) & (~g.censored) & g[group_col]).sum()
            if n < 2: continue
            e1 = dd * n1 / n; E1 += e1; E0 += dd - e1; O1 += d1; O0 += dd - d1
            V += dd * (n1 / n) * (1 - n1 / n) * (n - dd) / (n - 1)
    chi2 = (O1 - E1) ** 2 / V if V > 0 else float("nan")
    return chi2, (math.erfc(math.sqrt(chi2 / 2)) if chi2 == chi2 else float("nan")), O1, E1, O0, E0


def _strata(d, lag, cens, grp, K):
    """Per model stratum: sorted arrays for the vectorised log-rank."""
    out = []
    for _, g in d.groupby("model"):
        out.append((g[lag].to_numpy(float), (~g[cens].to_numpy(bool)).astype(int), g[grp].to_numpy(int)))
    return out


def logrank_k(strata, K):
    """Stratified K-group log-rank: observed O, expected E (length K) and covariance V (K x K)."""
    O = np.zeros(K); E = np.zeros(K); V = np.zeros((K, K))
    for lag, ev, g in strata:
        for t in np.unique(lag[ev == 1]):
            at = lag >= t; n = at.sum()
            if n < 2: continue
            nk = np.array([(at & (g == k)).sum() for k in range(K)], float)
            dk = np.array([((lag == t) & (ev == 1) & (g == k)).sum() for k in range(K)], float); dd = dk.sum()
            O += dk; E += dd * nk / n
            V += dd * (n - dd) / (n - 1) * (np.diag(nk / n) - np.outer(nk, nk) / n ** 2)
    return O, E, V


def trend_test(strata, K):
    """Log-rank test for trend with scores 0..K-1 (a dose-response test); chi2 on 1 d.f."""
    O, E, V = logrank_k(strata, K); sc = np.arange(K, dtype=float)
    den = sc @ V @ sc
    chi2 = (sc @ (O - E)) ** 2 / den if den > 0 else float("nan")
    return chi2, math.erfc(math.sqrt(chi2 / 2)) if chi2 == chi2 else float("nan"), O, E


def rate_ratio(strata):
    O, E, _ = logrank_k(strata, 2)
    return (O[1] / E[1]) / (O[0] / E[0]) if min(O) > 0 and min(E) > 0 else float("nan")


def cluster_bootstrap_rr(d, lag, cens, grp, B=1000, seed=1):
    """Percentile CI for the rate ratio, resampling whole repositories (all their model rows), which removes the repeat-repository dependence."""
    rng = np.random.default_rng(seed); repos = d.repo.unique(); parts = {r: g for r, g in d.groupby("repo")}; est = []
    for _ in range(B):
        samp = pd.concat([parts[r] for r in rng.choice(repos, len(repos))], ignore_index=True)
        v = rate_ratio(_strata(samp, lag, cens, grp, 2))
        if v == v and v > 0: est.append(math.log(v))
    est = np.array(est)
    if len(est) < B * 0.9: return float("nan"), float("nan"), float("nan")
    p = 2 * min((est <= 0).mean(), (est >= 0).mean())
    return float(np.exp(np.percentile(est, 2.5))), float(np.exp(np.percentile(est, 97.5))), float(min(p, 1.0))


def sensitivity(d, B=1000):
    """Sensitivity analyses: repository-clustered CI, active-repositories subset, relaxed migration definition, three-level flexibility (trend)."""
    d = d.copy(); d["censored"] = d.censored.astype(bool); d["flex_layer"] = d.flex_layer.astype(int)
    L = ["\n## Sensitivity analyses\n"]
    def line(label, sub, lag="lag_days", cens="censored", grp="flex_layer"):
        st = _strata(sub, lag, cens, grp, 2); O, E, V = logrank_k(st, 2); rr = rate_ratio(st); lo, hi, p = cluster_bootstrap_rr(sub, lag, cens, grp, B)
        L.append(f"{label}: {len(sub)} pairs, {sub.repo.nunique()} repos, {int(O.sum())} migrations; rate ratio {rr:.2f}; repository-cluster bootstrap 95% CI [{lo:.2f}, {hi:.2f}], p = {p:.3f}")
    L.append("Rate ratio = migration hazard with a provider-agnostic layer relative to without (stratified by model). Clustering by repository.")
    line("A. All pairs, strict definition (identifier absent from the whole tree)", d)
    d["direct_only"] = (~d.direct_sdk.astype(bool)).astype(int) if "direct_sdk" in d else 0
    if "direct_sdk" in d: line("A2. No direct SDK call (vs direct SDK)", d, grp="direct_only")
    if "frame" in d.columns and d.frame.astype(str).nunique() > 1:
        d["frame"] = d.frame.astype(str)
        L.append("E. Sampling-frame check (the layer-targeted frame samples framework and SDK repositories, which may list model names as catalogue entries and migrate differently):")
        comp = d.groupby("frame").agg(pairs=("repo", "size"), repos=("repo", "nunique"), share_layer=("flex_layer", "mean"), migrated_before_shutdown=("migrated_before_shutdown", "mean"), migrations=("censored", lambda x: int((~x).sum())))
        L.append(comp.round(3).to_string())
        line("E1. Strata = model x frame, all pairs", d.assign(model=d.model + "|" + d.frame))
        for fr, g in d.groupby("frame"):
            if (~g.censored).sum() >= 20 and g.flex_layer.nunique() > 1: line(f"E2. Frame '{fr}' only", g)
    if "occ_base" in d.columns and d.occ_base.notna().any():
        d["occ_tercile"] = pd.qcut(d.occ_base.rank(method="first"), 3, labels=False).astype(str)
        q = d.groupby("occ_tercile").occ_base.agg(["min", "median", "max"])
        L.append("F. Number of occurrences of the identifier at the announcement date (the strict definition needs EVERY occurrence removed, so repositories with many occurrences cannot qualify):")
        L.append(q.to_string())
        L.append(d.groupby(["occ_tercile", "flex_layer"]).agg(pairs=("repo", "size"), migrated_before_shutdown=("migrated_before_shutdown", "mean")).round(3).to_string())
        line("F1. Strata = model x occurrence tercile", d.assign(model=d.model + "|" + d.occ_tercile))
        if "frame" in d.columns:
            line("F2. Strata = model x frame x occurrence tercile", d.assign(model=d.model + "|" + d.frame.astype(str) + "|" + d.occ_tercile))
            for fr, g in d.groupby(d.frame.astype(str)):
                if (~g.censored).sum() >= 20 and g.flex_layer.nunique() > 1: line(f"F3. Frame '{fr}', strata = model x occurrence tercile", g.assign(model=g.model + "|" + g.occ_tercile))
    if "commits_to_shutdown" in d.columns and d.commits_to_shutdown.notna().any():
        for k in (1, 5):
            act = d[d.commits_to_shutdown.fillna(0) >= k]
            L.append(f"B{k}. Active repositories (>= {k} commits between announcement and shutdown/today): {len(act)} of {len(d)} pairs; migrated before shutdown {act.migrated_before_shutdown.mean():.3f} (all pairs: {d.migrated_before_shutdown.mean():.3f})")
            if (~act.censored).sum() >= 10: line(f"B{k}. Rate ratio, active repositories", act)
    else:
        L.append("B. Activity filter: not available (run mine_by_history.py --enrich first).")
    if "lag_relaxed" in d.columns and d.lag_relaxed.notna().any():
        dr = d.assign(censored_r=d.censored_relaxed.astype(bool))
        L.append(f"C. Relaxed definition (identifier gone from code files or occurrences halved): migrations {int((~dr.censored_r).sum())} (strict: {int((~d.censored).sum())})")
        line("C. Rate ratio, relaxed definition", dr, lag="lag_relaxed", cens="censored_r")
        if "occ_base" in dr.columns and dr.occ_base.notna().any():
            dr["occ_t"] = pd.qcut(dr.occ_base.rank(method="first"), 3, labels=False).astype(str)
            L.append("C2. Relaxed definition, migrated by shutdown by number of occurrences at the announcement (tercile 0 = fewest):")
            L.append(dr.assign(done=((~dr.censored_r) & (dr.lag_relaxed <= dr.notice_days))).groupby(["occ_t", "flex_layer"]).agg(pairs=("repo", "size"), migrated_by_shutdown=("done", "mean")).round(3).to_string())
            line("C3. Relaxed definition, strata = model x occurrence tercile", dr.assign(model=dr.model + "|" + dr.occ_t), lag="lag_relaxed", cens="censored_r")
            if "frame" in dr.columns:
                line("C4. Relaxed definition, strata = model x frame x occurrence tercile", dr.assign(model=dr.model + "|" + dr.frame.astype(str) + "|" + dr.occ_t), lag="lag_relaxed", cens="censored_r")
                for fr, g in dr.groupby(dr.frame.astype(str)):
                    if (~g.censored_r).sum() >= 20 and g.flex_layer.nunique() > 1: line(f"C5. Relaxed definition, frame '{fr}' only, strata = model x occurrence tercile", g.assign(model=g.model + "|" + g.occ_t), lag="lag_relaxed", cens="censored_r")
        L.append(f"   share migrated by shutdown under the relaxed definition: {((~dr.censored_r) & (dr.lag_relaxed <= dr.notice_days)).mean():.3f}")
    else:
        L.append("C. Relaxed definition: not available (run mine_by_history.py --enrich first).")
    if "flex_level" in d.columns and d.flex_level.notna().any():
        d["flex_level"] = d.flex_level.astype(int); K = 3
        st = _strata(d, "lag_days", "censored", "flex_level", K); chi2, p, O, E = trend_test(st, K)
        L.append("D. Three-level flexibility (0 hard-coded in code, 1 model string only in configuration files, 2 provider-agnostic layer), log-rank trend test:")
        for k in range(K):
            g = d[d.flex_level == k]
            L.append(f"   level {k}: {len(g)} pairs, {int(O[k])} migrations (expected {E[k]:.1f}), migrated before shutdown {g.migrated_before_shutdown.mean():.3f}")
        L.append(f"   trend chi2 = {chi2:.2f}, p = {p:.3f} (pair-level; the repository-clustered version is in the bootstrap below)")
        rng = np.random.default_rng(2); repos = d.repo.unique(); parts = {r: g for r, g in d.groupby("repo")}; est = []
        for _ in range(B):
            samp = pd.concat([parts[r] for r in rng.choice(repos, len(repos))], ignore_index=True)
            O_, E_, V_ = logrank_k(_strata(samp, "lag_days", "censored", "flex_level", K), K); sc = np.arange(K); est.append(float(sc @ (O_ - E_)))
        est = np.array(est); obs = float(np.arange(K) @ (O - E))
        L.append(f"   repository-cluster bootstrap of the trend statistic: observed {obs:.1f}, 95% CI [{np.percentile(est, 2.5):.1f}, {np.percentile(est, 97.5):.1f}] (0 means no trend)")
    else:
        L.append("D. Three-level flexibility: not available (run mine_by_history.py --enrich first).")
    return "\n".join(L)


def report(d):
    d = d.copy(); d["censored"] = d.censored.astype(bool); d["flex_layer"] = d.flex_layer.astype(bool)
    L = [f"{len(d)} repository-model pairs at risk, {d.repo.nunique()} repositories, {d.model.nunique()} models\n", "## Per model\n"]
    rows = []
    for m, g in d.groupby("model"):
        ev = (~g.censored).astype(int).values; notice = g.notice_days.iloc[0]; mig = g[~g.censored]
        rows.append(dict(model=m, at_risk=len(g), migrated_before_shutdown=round(g.migrated_before_shutdown.mean(), 3), km_unmigrated_at_shutdown=round(km_at(g.lag_days, ev, notice), 3),
                         median_lag_migrated=(mig.lag_days.median() if len(mig) else np.nan), share_flex_layer=round(g.flex_layer.mean(), 2)))
    L.append(pd.DataFrame(rows).to_string(index=False))
    L.append("\n## H1: time to migration by provider-agnostic layer at the announcement date\n")
    chi2, p, O1, E1, O0, E0 = logrank_stratified(d, "flex_layer")
    L.append(f"with layer: {int(d.flex_layer.sum())} pairs, {int(O1)} migrations, expected {E1:.1f}; without: {int((~d.flex_layer).sum())} pairs, {int(O0)} migrations, expected {E0:.1f}")
    if E1 > 0 and E0 > 0 and O0 > 0:
        L.append(f"crude rate ratio (with layer vs without) = {(O1 / E1) / (O0 / E0):.2f}; stratified log-rank chi2 = {chi2:.2f}, p = {p:.3f} (indicative: repositories repeat across models)")
    if "direct_sdk" in d.columns:
        d["direct_sdk"] = d.direct_sdk.astype(bool)
        c2, p2, A1, B1, A0, B0 = logrank_stratified(d.assign(flex_layer=~d.direct_sdk), "flex_layer")
        L.append(f"\nAlternative split: no direct SDK call at the announcement date ({int((~d.direct_sdk).sum())} pairs, {int(A1)} migrations, expected {B1:.1f}) versus direct SDK ({int(d.direct_sdk.sum())} pairs, {int(A0)} migrations, expected {B0:.1f}); chi2 = {c2:.2f}, p = {p2:.3f}")
        L.append(f"Repositories with a layer and no direct SDK: {int((d.flex_layer & ~d.direct_sdk).sum())}; both: {int((d.flex_layer & d.direct_sdk).sum())}; direct only: {int((~d.flex_layer & d.direct_sdk).sum())}; neither: {int((~d.flex_layer & ~d.direct_sdk).sum())}")
    L.append(f"Power note: {int((~d.censored).sum())} migrations in {d.repo.nunique()} repositories; with fewer than about 100 migrations a rate ratio below about 1.5 cannot be separated from zero.")
    for flag, g in d.groupby("flex_layer"):
        ev = (~g.censored).astype(int).values
        L.append(f"  layer={flag}: migrated before shutdown {g.migrated_before_shutdown.mean():.3f}; median lag of migrated {g[~g.censored].lag_days.median()}")
    mig = d[~d.censored]
    if len(mig) and "commit_additions" in mig:
        mig = mig.assign(lines=mig.commit_additions + mig.commit_deletions)
        L.append("\n## H5: size of the migration commit by provider-agnostic layer (migrated only)\n")
        L.append(mig.groupby("flex_layer")[["lines", "commit_files"]].agg(["count", "median"]).to_string())
        L.append(f"share touching prompt files: " + ", ".join(f"layer={k}: {v:.2f}" for k, v in mig.groupby("flex_layer").commit_touches_prompt.mean().items()))
        L.append("\n## H4: lag against notice length (migrated only)\n")
        L.append(mig.groupby("notice_days").lag_days.agg(["count", "median"]).to_string())
    return "\n".join(L)


def selftest():
    rng = np.random.default_rng(0); rows = []
    for i in range(400):
        flex = i % 2 == 0; lag = rng.exponential(60 if flex else 180); cens = lag > 300
        rows.append(dict(model="m" + str((i // 2) % 2), repo=f"r{i}", notice_days=184, flex_layer=flex, direct_sdk=not flex, censored=cens, lag_days=min(lag, 300),
                         migrated_before_shutdown=(not cens) and lag <= 184, commit_additions=10, commit_deletions=5, commit_files=2, commit_touches_prompt=False))
    r = report(pd.DataFrame(rows)); assert "crude rate ratio" in r
    d = pd.DataFrame(rows); chi2, p, O1, E1, O0, E0 = logrank_stratified(d.assign(censored=d.censored.astype(bool)), "flex_layer")
    assert O1 / E1 > 1.5 and p < 0.001, (O1, E1, p)
    d["flex_level"] = np.where(d.flex_layer, 2, rng.integers(0, 2, len(d))); d["commits_to_shutdown"] = 3; d["lag_relaxed"] = d.lag_days * 0.8
    d["censored_relaxed"] = d.censored; d["flex_layer"] = d.flex_layer.astype(int)
    out = sensitivity(d, B=50); assert "trend chi2" in out and "Rate ratio, relaxed" in out, out
    st = _strata(d.assign(censored=d.censored.astype(bool)), "lag_days", "censored", "flex_layer", 2); lo, hi, p = cluster_bootstrap_rr(d.assign(censored=d.censored.astype(bool)), "lag_days", "censored", "flex_layer", 50)
    assert lo > 1.5 and abs(rate_ratio(st) - (O1 / E1) / (O0 / E0)) < 1e-9, (lo, hi)
    print("selftest ok; rate ratio", round((O1 / E1) / (O0 / E0), 2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("path", nargs="?"); ap.add_argument("--md"); ap.add_argument("--selftest", action="store_true"); ap.add_argument("--boot", type=int, default=1000)
    a = ap.parse_args()
    if a.selftest: selftest(); sys.exit()
    d = pd.read_json(a.path, lines=True); r = report(d) + "\n" + sensitivity(d, a.boot); print(r)
    if a.md: open(a.md, "w").write(r + "\n")
