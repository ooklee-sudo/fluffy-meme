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
    print("selftest ok; rate ratio", round((O1 / E1) / (O0 / E0), 2))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("path", nargs="?"); ap.add_argument("--md"); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest: selftest(); sys.exit()
    r = report(pd.read_json(a.path, lines=True)); print(r)
    if a.md: open(a.md, "w").write(r + "\n")
