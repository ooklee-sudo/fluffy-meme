"""Summaries of results/migrations.jsonl from mine_migrations.py.
Per model: files, share migrated (the model string was removed) by the shutdown date, share migrated within the notice window, median lag among migrated files,
share of migrations in the last third of the notice window, and the Kaplan-Meier share still unmigrated at the shutdown date.
With repository metadata (newer runs) the same table is repeated for active, non-fork, non-archived repositories (pushed within 180 days before the shutdown).
usage: python analyze_migrations.py results\\migrations.jsonl [--md out.md] ; python analyze_migrations.py --selftest
"""
import argparse, sys
import numpy as np, pandas as pd


def km_unmigrated_at(lag, event, t):
    """Kaplan-Meier survival (share not yet migrated) at time t; lag in days, event=1 migrated, 0 censored."""
    lag, event = np.asarray(lag, float), np.asarray(event, int)
    s = 1.0
    for u in np.unique(lag[(event == 1) & (lag <= t)]):
        at_risk = (lag >= u).sum(); d = ((lag == u) & (event == 1)).sum()
        s *= 1 - d / at_risk
    return s


def table(d):
    rows = []
    for m, g in d.groupby("model"):
        ev = (~g.censored).astype(int).values; lag = g.lag_days.values; notice = g.notice_days.values
        mig = g[~g.censored]
        by_ship = ((ev == 1) & (lag <= notice)).mean()
        late = ((mig.lag_days / mig.notice_days) > 2 / 3).mean() if len(mig) else np.nan
        rows.append(dict(model=m, files=len(g), migrated_ever=round(ev.mean(), 2), migrated_within_notice=round(by_ship, 2),
                         median_lag_migrated=(mig.lag_days.median() if len(mig) else np.nan), last_third_share=(round(late, 2) if late == late else np.nan),
                         km_unmigrated_at_shutdown=round(km_unmigrated_at(lag, ev, notice[0]), 2)))
    return pd.DataFrame(rows)


def load(path):
    d = pd.read_json(path, lines=True)
    d["censored"] = d.censored.astype(bool)
    return d


def active_subset(d):
    need = {"repo_pushed_at", "repo_fork", "repo_archived"}
    if not need <= set(d.columns): return None
    pushed = pd.to_datetime(d.repo_pushed_at, utc=True, errors="coerce").dt.tz_localize(None)
    sd = pd.to_datetime(d.shutdown)
    ok = (pushed >= sd - pd.Timedelta(days=180)) & (~d.repo_fork.fillna(False).astype(bool)) & (~d.repo_archived.fillna(False).astype(bool))
    return d[ok]


def report(d):
    out = ["## All files\n", table(d).to_string(index=False)]
    a = active_subset(d)
    if a is not None:
        out += [f"\n## Active, non-fork, non-archived repositories ({len(a)} of {len(d)} files)\n", table(a).to_string(index=False) if len(a) else "(none)"]
    else:
        out += ["\n(no repository metadata in this file: run the newer mine_migrations.py to add the active-repository table)"]
    eff = [c for c in ("pr_additions", "pr_deletions", "pr_changed_files", "pr_hours_to_merge", "commit_additions", "commit_files") if c in d.columns]
    if eff:
        out += ["\n## Effort proxies of migration changes (migrated files only), medians and quartiles\n", d[~d.censored][eff].describe().loc[["count", "25%", "50%", "75%"]].round(1).to_string()]
    return "\n".join(out)


def selftest():
    d = pd.DataFrame(dict(model=["a"] * 4, repo=list("wxyz"), path=["p"] * 4, shutdown=["2026-10-01"] * 4, lag_days=[10, 100, 150, 150],
                          censored=[False, False, True, True], notice_days=[180] * 4, repo_pushed_at=["2026-09-01T00:00:00Z"] * 4,
                          repo_fork=[False] * 4, repo_archived=[False] * 4))
    t = table(d).iloc[0]
    assert t.files == 4 and t.migrated_ever == 0.5 and t.migrated_within_notice == 0.5 and t.median_lag_migrated == 55, t
    assert abs(t.km_unmigrated_at_shutdown - 0.5) < 1e-9, t       # events at 10 and 100: 3/4 * 2/3 = 0.5
    print("selftest ok"); 


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("path", nargs="?"); ap.add_argument("--md"); ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest: selftest(); sys.exit()
    r = report(load(a.path)); print(r)
    if a.md: open(a.md, "w").write(r + "\n")
