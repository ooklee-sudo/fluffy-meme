"""Staggered-adoption event study (Callaway-Sant'Anna with not-yet-treated controls), repository clusters.

Unit: repository. Periods: first 7 days of Feb..Sep 2025 (index 0..7). Treatment period g_i = first sampled week by whose end the
repository has had an agent PR (first agent PR date from AIDev). Controls for cohort g at time t: repositories not yet treated by
max(t, g-1) and not in cohort g. Base period g-1.
"""
import numpy as np, pandas as pd
rng = np.random.default_rng(3)
PER = ["2025-02", "2025-03", "2025-04", "2025-05", "2025-06", "2025-07", "2025-08", "2025-09"]; T = len(PER)
pr = pd.read_parquet("/tmp/gha/panel_prs.parquet")

# ---- treatment dates from AIDev (v4 curated): first agent PR per repository
a = pd.read_parquet("/tmp/aidev_data/pull_request.parquet", columns=["repo_url", "created_at"])
a["repo"] = a.repo_url.str.replace("https://api.github.com/repos/", "", regex=False).str.lower()
first = pd.to_datetime(a.created_at, utc=True).groupby(a.repo).min()
week_end = [pd.Timestamp(p + "-07 23:59:59", tz="UTC") for p in PER]
def gperiod(ts):
    for p in range(T):
        if ts <= week_end[p]: return p
    return T                                   # not treated within the sample
g_repo = first.map(gperiod)
pr["repo_l"] = pr.repo.str.lower(); pr["g"] = pr.repo_l.map(g_repo)
pr = pr[pr.g.notna()].copy(); pr["g"] = pr.g.astype(int)
print("cohort sizes (repositories with >=1 PR in the panel):"); print(pr.groupby("g").repo_l.nunique().rename(lambda g: f"g={g} ({PER[g] if g < T else 'after Sep'})").to_string())

def panel(d, y):
    m = d.groupby(["repo_l", "period"])[y].mean().unstack().reindex(columns=range(T))
    return m
repos_all = sorted(pr.repo_l.unique()); gi = g_repo.reindex(repos_all).values.astype(int)

def cs(Y, g, T=T):
    """Y: repos x T (NaN = no obs). returns dict e -> (weighted ATT, total weight), and cell table."""
    out = {}
    for gg in range(1, T):                                   # cohort needs a base period gg-1 >= 0
        tr = np.where(g == gg)[0]
        if len(tr) == 0: continue
        for t in range(T):
            if t == gg - 1: continue
            ctrl = np.where((g > max(t, gg - 1)) & (g != gg))[0]
            ok_t = tr[~np.isnan(Y[tr, t]) & ~np.isnan(Y[tr, gg - 1])]
            ok_c = ctrl[~np.isnan(Y[ctrl, t]) & ~np.isnan(Y[ctrl, gg - 1])]
            if len(ok_t) < 5 or len(ok_c) < 20: continue
            att = (Y[ok_t, t] - Y[ok_t, gg - 1]).mean() - (Y[ok_c, t] - Y[ok_c, gg - 1]).mean()
            out.setdefault(t - gg, []).append((att, len(ok_t)))
    res = {}
    for e, lst in out.items():
        w = np.array([n for _, n in lst], float); v = np.array([a for a, _ in lst]); res[e] = ((v * w).sum() / w.sum(), w.sum())
    return res

def run(y, d, label, B=400):
    Y = panel(d, y).reindex(repos_all).values
    pt = cs(Y, gi); es = sorted(pt)
    boots = []
    n = len(repos_all)
    for _ in range(B):
        idx = rng.integers(0, n, n); r = cs(Y[idx], gi[idx]); boots.append(r)
    se = {e: np.std([b[e][0] for b in boots if e in b]) for e in es}
    post = [e for e in es if e >= 0]; pre = [e for e in es if e <= -2]
    def agg(sel):
        if not sel: return np.nan, np.nan
        w = np.array([pt[e][1] for e in sel]); est = sum(pt[e][0] * pt[e][1] for e in sel) / w.sum()
        bs = []
        for b in boots:
            ss = [e for e in sel if e in b]
            if len(ss) == len(sel): bs.append(sum(b[e][0] * pt[e][1] for e in sel) / w.sum())
        return est, np.std(bs)
    po, pose = agg(post); pr_, prse = agg(pre)
    print(f"\n[{label}]  outcome mean (all repo-periods) = {np.nanmean(Y):.3f}")
    print("  event time e:  " + " ".join(f"{e:>8d}" for e in es))
    print("  ATT:           " + " ".join(f"{pt[e][0]:+8.3f}" for e in es))
    print("  s.e.:          " + " ".join(f"{se[e]:8.3f}" for e in es))
    print(f"  pre-period placebo (e<=-2): {pr_:+.3f} (se {prse:.3f});  post-adoption average (e>=0): {po:+.3f} (se {pose:.3f}), t = {po/pose:.1f}")
    return dict(label=label, pre=pr_, pre_se=prse, post=po, post_se=pose, es=es, att=[pt[e][0] for e in es], se=[se[e] for e in es])

hum = pr[pr.group == "human"]
pr["lnpr"] = 1  # placeholder for count outcome (computed below)
res = []
for y, lab in (("net_add", "net_add"), ("any_review", "any_review"), ("refactor", "refactor"), ("merged", "merged")):
    res.append(run(y, pr, f"{lab}, all PRs"))
    res.append(run(y, hum, f"{lab}, human PRs only"))
# activity: log(1+PR count) with zeros for repo-periods without PRs
cnt = pr.groupby(["repo_l", "period"]).size().unstack().reindex(index=repos_all, columns=range(T)).fillna(0)
cnt_h = hum.groupby(["repo_l", "period"]).size().unstack().reindex(index=repos_all, columns=range(T)).fillna(0)
for nm, c in (("log(1+PRs), all", cnt), ("log(1+PRs), human", cnt_h)):
    Yc = np.log1p(c.values); pt = cs(Yc, gi); es = sorted(pt)
    boots = []
    for _ in range(300):
        idx = rng.integers(0, len(repos_all), len(repos_all)); boots.append(cs(Yc[idx], gi[idx]))
    post = [e for e in es if e >= 0]; w = np.array([pt[e][1] for e in post]); est = sum(pt[e][0] * pt[e][1] for e in post) / w.sum()
    bs = [sum(b[e][0] * pt[e][1] for e in post) / w.sum() for b in boots if all(e in b for e in post)]
    print(f"\n[{nm}] ATT e: " + " ".join(f"{e}:{pt[e][0]:+.3f}" for e in es) + f"\n  post average {est:+.3f} (se {np.std(bs):.3f})")
pd.DataFrame(res).to_json("/tmp/gha/event_study_results.json", orient="records")
