"""Two new analyses for the ISR version.

  A. Accumulated changes as the state: does the stock of merged pull requests since the last
     regular release predict a regular release, and does age still matter once it is included?
  B. Upstream model launches as exogenous state shocks: stacked event study of release
     probabilities in repositories that are exposed to a launch versus repositories that are not,
     plus a direct measure (release notes that mention the new model).

Usage:  python analyze.py [--end-week 2026-09-28] [--boot 999]
Needs only numpy, pandas and scipy. Reads data/ (from collect.py), events.csv, repo_relevance.csv.
Writes results/results.md and CSV tables in results/.
"""
import argparse, glob, json, os, re
import numpy as np
import pandas as pd

BUG_KW = re.compile(r"\b(?:bug|error|crash|fail|wrong|incorrect|regression|broken|exception)", re.I)
BOT = re.compile(r"(?:\[bot\]$|^dependabot|^renovate|^github-actions|-bot$|^stainless)", re.I)
RELEASE_PR = re.compile(r"(?:^\s*\[?release\]?\b|chore\(release\)|release[: ]+v?\d|bump (?:the )?version|"
                        r"version bump|bump to v?\d|prepare (?:for )?(?:the )?release|^v?\d+\.\d+(?:\.\d+)?\s*$)", re.I)
VER = re.compile(r"v?(\d+)\.(\d+)(?:\.(\d+))?")
CAP = 8
RNG = np.random.default_rng(20261012)


# ----------------------------------------------------------------------------- helpers
def week(s):
    t = pd.to_datetime(pd.Series(s), utc=True).dt.tz_localize(None)
    return t.dt.to_period("W-SUN").dt.start_time


def parse_tag(tag):
    m = VER.search(tag)
    if not m:
        return None, None
    return tag[:m.start()], (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))


def logit(X, y, iters=50):
    b = np.zeros(X.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-np.clip(X @ b, -30, 30)))
        g = X.T @ (y - p)
        H = (X * (p * (1 - p))[:, None]).T @ X + 1e-6 * np.eye(X.shape[1])
        step = np.linalg.solve(H, g)
        b += step
        if np.max(np.abs(step)) < 1e-8:
            return b
    return b if np.all(np.isfinite(b)) else np.full(X.shape[1], np.nan)


def dersimonian_laird(est, se):
    est, se = np.asarray(est, float), np.asarray(se, float)
    ok = np.isfinite(est) & np.isfinite(se) & (se > 0)
    est, se = est[ok], se[ok]
    if len(est) < 2:
        return np.nan, np.nan, np.nan, np.nan
    w = 1 / se**2
    fe = np.sum(w * est) / np.sum(w)
    q = np.sum(w * (est - fe) ** 2)
    tau2 = max(0.0, (q - (len(est) - 1)) / (np.sum(w) - np.sum(w**2) / np.sum(w)))
    wr = 1 / (se**2 + tau2)
    m = np.sum(wr * est) / np.sum(wr)
    s = np.sqrt(1 / np.sum(wr))
    return m, m - 1.96 * s, m + 1.96 * s, tau2


def demean(cols, groups, tol=1e-10, iters=500):
    """Absorb several sets of fixed effects by alternating projections."""
    M = np.column_stack(cols).astype(float)
    codes = [pd.factorize(g)[0] for g in groups]
    for _ in range(iters):
        old = M.copy()
        for c in codes:
            n = np.bincount(c)
            for j in range(M.shape[1]):
                M[:, j] -= (np.bincount(c, M[:, j]) / n)[c]
        if np.max(np.abs(M - old)) < tol:
            break
    return M


def cluster_vcov(X, u, cl):
    XtX_inv = np.linalg.pinv(X.T @ X)
    G = pd.factorize(cl)[0]
    meat = np.zeros((X.shape[1], X.shape[1]))
    for g in range(G.max() + 1):
        s = X[G == g].T @ u[G == g]
        meat += np.outer(s, s)
    n, k, nG = X.shape[0], X.shape[1], G.max() + 1
    c = nG / (nG - 1) * (n - 1) / (n - k)
    return c * XtX_inv @ meat @ XtX_inv


def wild_cluster_p(y, X, j, cl, B):
    """Wild cluster restricted bootstrap-t (Webb weights) for H0: beta_j = 0. y and X already demeaned."""
    other = np.delete(X, j, axis=1)
    x = X[:, [j]]
    if other.shape[1]:
        proj = lambda v: v - other @ np.linalg.lstsq(other, v, rcond=None)[0]
    else:
        proj = lambda v: v
    xt = proj(x)[:, 0]
    er = proj(y)                       # restricted residuals (beta_j = 0)
    b = xt @ er / (xt @ xt)
    u = er - xt * b
    V = cluster_vcov(xt[:, None], u, cl)
    t0 = b / np.sqrt(V[0, 0])
    G = pd.factorize(cl)[0]
    nG = G.max() + 1
    webb = np.array([-np.sqrt(1.5), -1, -np.sqrt(.5), np.sqrt(.5), 1, np.sqrt(1.5)])
    ts = np.empty(B)
    for i in range(B):
        w = RNG.choice(webb, nG)[G]
        ys = proj(w * er)
        bs = xt @ ys / (xt @ xt)
        us = ys - xt * bs
        Vs = cluster_vcov(xt[:, None], us, cl)
        ts[i] = bs / np.sqrt(Vs[0, 0])
    return float(np.mean(np.abs(ts) >= abs(t0)))


# ----------------------------------------------------------------------------- panel
def build_panel(d, end_week):
    repo = os.path.basename(d).replace("__", "/")
    rel = pd.DataFrame(json.load(open(f"{d}/releases.json")))
    rel = rel.sort_values("published_at").reset_index(drop=True)
    rel["week"] = week(rel["published_at"])
    rel["ts"] = pd.to_datetime(rel["published_at"], utc=True)
    # hot-fix classification: patch-only change from the previous release with the same tag prefix
    last = {}
    hot_time, hot_ver = [], []
    for _, r in rel.iterrows():
        pre, v = parse_tag(r["tag"])
        ht = hv = False
        if v is not None and pre in last:
            pv, pts = last[pre]
            if v[:2] == pv[:2] and v[2] > pv[2]:
                hv = True
                ht = (r["ts"] - pts).days < 7
        if v is not None:
            last[pre] = (v, r["ts"])
        hot_time.append(ht); hot_ver.append(hv)
    rel["hot_time"], rel["hot_ver"] = hot_time, hot_ver

    start = rel.loc[rel["published_at"] >= "2023-01-01", "week"].min()
    if end_week is None:
        coll = pd.Timestamp(json.load(open(f"{d}/meta.json"))["collected_at"]).tz_localize(None)
        end = coll.to_period("W-SUN").start_time - pd.Timedelta(days=7)
    else:
        end = pd.Timestamp(end_week)
    weeks = pd.date_range(start, end, freq="7D")
    P = pd.DataFrame({"repo": repo, "week": weeks})

    def wcount(dates, mask=None):
        s = pd.Series(1, index=dates if mask is None else dates[mask]).groupby(level=0).sum()
        return P["week"].map(s).fillna(0).astype(int).values

    P["n_rel"] = wcount(rel["week"])
    P["n_reg"] = wcount(rel["week"], ~rel["hot_time"])
    P["n_hot"] = wcount(rel["week"], rel["hot_time"])
    for c in ["rel", "reg", "hot"]:
        P[f"any_{c}"] = (P[f"n_{c}"] > 0).astype(int)

    iss = pd.DataFrame(json.load(open(f"{d}/issues.json")))
    if len(iss):
        iss["week"] = week(iss["created_at"])
        bug = iss.apply(lambda r: any("bug" in l.lower() for l in r["labels"]) or bool(BUG_KW.search(r["title"])), axis=1)
        P["issues"] = wcount(iss["week"])
        P["bugs"] = wcount(iss["week"], bug.values)
    else:
        P["issues"] = P["bugs"] = 0

    meta = json.load(open(f"{d}/meta.json"))
    prs = pd.DataFrame(json.load(open(f"{d}/prs.json")))
    if len(prs):
        keep = (prs["base"] == meta["default_branch"]) & ~prs["user"].fillna("").str.contains(BOT) \
               & (prs["user_type"] != "Bot") & ~prs["title"].fillna("").str.contains(RELEASE_PR)
        prs = prs[keep]
        P["prs"] = wcount(week(prs["merged_at"]).values) if len(prs) else 0
    else:
        P["prs"] = 0
    com = pd.DataFrame(json.load(open(f"{d}/commits.json")))
    if len(com):
        com = com[~com["author"].fillna("").str.contains(BOT)]
        P["commits"] = wcount(week(com["date"]).values) if len(com) else 0
    else:
        P["commits"] = 0

    # ages and change stocks, measured through the end of the previous week
    age_any, age_reg, cyc, cum_pr, cum_com = [], [], [], [], []
    la = lr = None
    c_id, spr, scm = 0, 0, 0
    for i, r in P.iterrows():
        age_any.append(i - la if la is not None else np.nan)
        age_reg.append(i - lr if lr is not None else np.nan)
        cyc.append(c_id); cum_pr.append(spr); cum_com.append(scm)
        if r["any_rel"]:
            la = i
        if r["any_reg"]:
            lr, c_id, spr, scm = i, c_id + 1, 0, 0
        else:
            spr += r["prs"]; scm += r["commits"]
    P["age_any"], P["age_reg"], P["cycle"] = age_any, age_reg, cyc
    P["cum_pr"], P["cum_commits"] = cum_pr, cum_com
    P["trend"] = (P["week"] - P["week"].min()).dt.days / 365.25
    return P, rel.assign(repo=repo)


# ----------------------------------------------------------------------------- analysis A
def add_work_age(g):
    """Calendar age versus 'work age': merged PRs since the last regular release divided by the
    repository's mean weekly merges, so both are in weeks; both capped at CAP. They differ only
    when the pace of merging varies, which is the variation that separates the two rules."""
    g["age"] = g["age_reg"].clip(upper=CAP)
    rate = g["prs"].mean()
    g["work"] = (g["cum_pr"] / rate).clip(upper=CAP) if rate > 0 else np.nan
    return g


def change_state(P, boot):
    rows = []
    specs = {"age only": ["age"], "changes only": ["work"], "both": ["work", "age"]}
    for repo, g in P.groupby("repo"):
        g = add_work_age(g.dropna(subset=["age_reg"]).copy())
        y = g["any_reg"].values.astype(float)
        out = {"repo": repo, "weeks": len(g), "regular_releases": int(y.sum()),
               "corr_age_work": g["age"].corr(g["work"]),
               "cv_weekly_prs": g["prs"].std() / g["prs"].mean() if g["prs"].mean() > 0 else np.nan}
        cycles = g["cycle"].values
        uc = np.unique(cycles)
        for name, xs in specs.items():
            X = np.column_stack([np.ones(len(g))] + [g[c].values for c in xs] + [g["trend"].values])
            b = logit(X, y)
            bs = []
            for _ in range(boot):
                pick = RNG.choice(uc, len(uc))
                idx = np.concatenate([np.where(cycles == c)[0] for c in pick])
                bb = logit(X[idx], y[idx])
                if np.all(np.isfinite(bb)) and np.max(np.abs(bb)) < 25:
                    bs.append(bb)
            se = np.std(bs, axis=0, ddof=1) if len(bs) > 20 else np.full(len(b), np.nan)
            for k, c in enumerate(xs, start=1):
                out[f"{name}|{c}"], out[f"{name}|{c}|se"] = b[k], se[k]
        rows.append(out)
    R = pd.DataFrame(rows)
    pooled = {}
    for col in [c for c in R.columns if c.count("|") == 1]:
        pooled[col] = dersimonian_laird(R[col], R[col + "|se"])
    return R, pooled


def change_state_fe(P, boot):
    g = pd.concat([add_work_age(x.dropna(subset=["age_reg"]).copy()) for _, x in P.groupby("repo")])
    g = g.dropna(subset=["work"])
    cols = [g["any_reg"].values, g["work"].values, g["age"].values, g["trend"].values]
    M = demean(cols, [g["repo"].values])
    y, X = M[:, 0], M[:, 1:]
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    V = cluster_vcov(X, y - X @ b, g["repo"].values)
    res = {}
    for j, name in enumerate(["work age", "calendar age"]):
        res[name] = (b[j], np.sqrt(V[j, j]), wild_cluster_p(y, X, j, g["repo"].values, boot))
    return res


def hotfix_by_age(P, rel):
    """Share of releases that are patch-only (version-based definition, no time window) by age."""
    out = []
    for repo, g in P.groupby("repo"):
        r = rel[rel["repo"] == repo]
        wk = g.set_index("week")["age_any"]
        a = r["week"].map(wk).clip(upper=CAP)
        out.append(pd.DataFrame({"age": a, "hot_ver": r["hot_ver"].astype(int)}))
    D = pd.concat(out).dropna()
    return D.groupby("age")["hot_ver"].agg(["mean", "count"])


# ----------------------------------------------------------------------------- analysis B
def event_study(P, ev, relv, outcome, boot, pre=4, post=8):
    P = P.set_index(["repo", "week"])
    ev = ev.assign(w=week(ev["date"]).values)
    treat = {(r, e.event_id): int(relv.loc[r, e.type]) if r in relv.index else 0
             for r in P.index.get_level_values(0).unique() for e in ev.itertuples()}
    rows = []
    for e in ev.itertuples():
        for r in P.index.get_level_values(0).unique():
            T = treat[(r, e.event_id)]
            if not T:  # clean controls: not exposed to another launch within the window
                near = ev[(abs((ev["w"] - e.w).dt.days) <= 7 * post) & (ev["event_id"] != e.event_id)]
                if any(treat[(r, x)] for x in near["event_id"]):
                    continue
            for k in range(-pre, post + 1):
                wk = e.w + pd.Timedelta(days=7 * k)
                if (r, wk) in P.index:
                    rows.append((e.event_id, e.type, r, wk, k, T, P.loc[(r, wk), outcome]))
    S = pd.DataFrame(rows, columns=["event", "type", "repo", "week", "k", "T", "y"])
    # keep repo-event blocks with the full window
    full = S.groupby(["event", "repo"])["k"].transform("count") == pre + post + 1
    S = S[full].reset_index(drop=True)
    ks = [k for k in range(-pre, post + 1) if k != -1]
    D = np.column_stack([(S["T"] * (S["k"] == k)).values for k in ks])
    M = demean([S["y"].values] + list(D.T), [S["event"] + "|" + S["repo"], S["event"] + "|" + S["week"].astype(str)])
    y, X = M[:, 0], M[:, 1:]
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    V = cluster_vcov(X, y - X @ b, S["repo"].values)
    coefs = pd.DataFrame({"k": ks, "coef": b, "se": np.sqrt(np.diag(V))})
    pj = [ks.index(k) for k in range(-pre, -1)]
    bp, Vp = b[pj], V[np.ix_(pj, pj)]
    wald = float(bp @ np.linalg.pinv(Vp) @ bp)
    # summary difference-in-differences: weeks 0-4 and 5-8 against weeks -4 to -1
    D2 = np.column_stack([(S["T"] * S["k"].between(0, 4)).values, (S["T"] * S["k"].between(5, post)).values])
    M2 = demean([S["y"].values] + list(D2.T), [S["event"] + "|" + S["repo"], S["event"] + "|" + S["week"].astype(str)])
    y2, X2 = M2[:, 0], M2[:, 1:]
    b2 = np.linalg.lstsq(X2, y2, rcond=None)[0]
    V2 = cluster_vcov(X2, y2 - X2 @ b2, S["repo"].values)
    p_boot = wild_cluster_p(y2, X2, 0, S["repo"].values, boot)
    summ = {"did_0_4": b2[0], "se_0_4": np.sqrt(V2[0, 0]), "wcb_p_0_4": p_boot,
            "did_5_8": b2[1], "se_5_8": np.sqrt(V2[1, 1]), "pretrend_wald": wald, "pretrend_df": len(pj),
            "n_obs": len(S), "n_events": S["event"].nunique(), "treated_blocks": int(S.loc[S.k == 0, "T"].sum()),
            "control_blocks": int((S.loc[S.k == 0, "T"] == 0).sum()),
            "base_rate_treated_pre": S.loc[(S["T"] == 1) & (S["k"] < 0), "y"].mean()}
    return coefs, summ


def mentions(rel, ev, relv, window=8):
    ev = ev.assign(ts=pd.to_datetime(ev["date"]))
    rows = []
    for e in ev.itertuples():
        rx = re.compile(e.keywords, re.I)
        for r in relv.index[relv[e.type] == 1]:
            R = rel[rel["repo"] == r]
            if R.empty:
                continue
            t = R["ts"].dt.tz_localize(None)
            days = (t - e.ts).dt.days
            txt = (R["name"].fillna("") + " " + R["tag"] + " " + R["body"].fillna(""))
            hit = txt.apply(lambda s: bool(rx.search(s)))
            post_ = days.between(0, 7 * window - 1)
            pre_ = days.between(-7 * window, -1)
            first = days[post_ & hit].min()
            rows.append({"event": e.event_id, "type": e.type, "repo": r,
                         "releases_pre": int(pre_.sum()), "mention_pre": int((pre_ & hit).sum()),
                         "releases_post": int(post_.sum()), "mention_post": int((post_ & hit).sum()),
                         "days_to_first_mention": first if pd.notna(first) else np.nan})
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- main
def f(x, d=3):
    return "n/a" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:.{d}f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--end-week", default=None, help="Monday of the last week to include, e.g. 2026-09-28")
    ap.add_argument("--boot", type=int, default=999)
    ap.add_argument("--data", default="data")
    a = ap.parse_args()
    os.makedirs("results", exist_ok=True)
    panels, rels = zip(*[build_panel(d, a.end_week) for d in sorted(glob.glob(f"{a.data}/*__*"))])
    P, rel = pd.concat(panels, ignore_index=True), pd.concat(rels, ignore_index=True)
    P.to_csv("results/panel.csv", index=False)
    ev = pd.read_csv("events.csv")
    relv = pd.read_csv("repo_relevance.csv").set_index("repo")

    L = ["# Results of the new analyses", "",
         f"Panel: {P['repo'].nunique()} repositories, {len(P)} repository-weeks, {int(P['n_rel'].sum())} releases "
         f"({int(P['n_reg'].sum())} regular, {int(P['n_hot'].sum())} hot-fix under the 7-day rule).", ""]

    # A
    R, pooled = change_state(P, max(199, a.boot // 3))
    R.to_csv("results/change_state_by_repo.csv", index=False)
    L += ["## A. Accumulated changes as the state", "",
          "Discrete-time logit of a regular release on work age (merged PRs since the last regular release, through the previous week, "
          "divided by the repository's mean weekly merges) and calendar age since the last regular release, both in weeks and capped at "
          f"{CAP}, with a linear trend. Cycle-bootstrap SEs, DerSimonian-Laird pooling. A change-based state rule predicts that work age "
          "matters and calendar age does not once both are included; a Taylor cadence predicts the reverse.", "",
          "| Specification | Variable | Pooled | 95% CI | tau2 |", "|---|---|---|---|---|"]
    for k, (m, lo, hi, t2) in pooled.items():
        s, v = k.split("|")
        L.append(f"| {s} | {'work age' if v == 'work' else 'calendar age'} | {f(m)} | {f(lo)} to {f(hi)} | {f(t2)} |")
    L += ["", f"Median within-repository correlation between calendar and work age: {f(R['corr_age_work'].median(), 2)}; "
          f"median coefficient of variation of weekly merges: {f(R['cv_weekly_prs'].median(), 2)}. "
          "The higher the correlation, the less the data can separate the two rules.", ""]
    for name in ["both|work", "both|age"]:
        z = R[name] / R[name + "|se"]
        L.append(f"- {name}: {int((z > 1.96).sum())} repositories significantly positive, {int((z < -1.96).sum())} significantly negative.")
    fe = change_state_fe(P, a.boot)
    L += ["", "Linear probability model with repository fixed effects, work age and calendar age entered together, "
          "wild cluster restricted bootstrap p-values (Webb weights, clusters = repositories):", ""]
    for k, (b, se, p) in fe.items():
        L.append(f"- {k}: {f(b, 4)} (cluster SE {f(se, 4)}; wild bootstrap p = {f(p)})")
    hb = hotfix_by_age(P, rel)
    hb.to_csv("results/hotfix_share_by_age_version_rule.csv")
    L += ["", "Share of releases that are patch-only by the version rule alone (no 7-day window), by age of the previous release:", "",
          "| Age | Share patch-only | Releases |", "|---|---|---|"]
    L += [f"| {int(i)} | {f(r['mean'], 2)} | {int(r['count'])} |" for i, r in hb.iterrows()]

    # B
    L += ["", "## B. Upstream model launches as state shocks", ""]
    allc = []
    for outcome in ["any_rel", "any_reg"]:
        for typ in ["all", "open_weights", "api"]:
            e = ev if typ == "all" else ev[ev["type"].str.startswith(typ)]
            if e.empty:
                continue
            c, s = event_study(P.copy(), e, relv, outcome, a.boot)
            allc.append(c.assign(outcome=outcome, events=typ))
            L.append(f"- **{outcome}, {typ} events** ({s['n_events']} events, {s['treated_blocks']} treated and "
                     f"{s['control_blocks']} control repository-event blocks; treated pre-launch weekly rate {f(s['base_rate_treated_pre'], 2)}): "
                     f"weeks 0-4 {f(s['did_0_4'])} (SE {f(s['se_0_4'])}; wild bootstrap p = {f(s['wcb_p_0_4'])}), "
                     f"weeks 5-8 {f(s['did_5_8'])} (SE {f(s['se_5_8'])}); pre-trend Wald = {f(s['pretrend_wald'], 2)} on {s['pretrend_df']} df.")
    C = pd.concat(allc)
    C.to_csv("results/event_study_coefficients.csv", index=False)
    c0 = C[(C.outcome == "any_rel") & (C.events == "all")]
    L += ["", "Event-time coefficients (any release, all events; week -1 omitted):", "", "| Week | Coef | SE |", "|---|---|---|"]
    L += [f"| {int(r.k)} | {f(r.coef)} | {f(r.se)} |" for r in c0.itertuples()]

    Mn = mentions(rel, ev, relv)
    Mn.to_csv("results/release_note_mentions.csv", index=False)
    if len(Mn):
        L += ["", "## C. Release notes that mention the new model (exposed repositories, 8 weeks before vs after launch)", "",
              f"- Repository-event pairs: {len(Mn)}; with at least one mentioning release within 8 weeks after launch: "
              f"{int((Mn['mention_post'] > 0).sum())} ({f((Mn['mention_post'] > 0).mean() * 100, 1)}%).",
              f"- Mentioning releases before launch: {int(Mn['mention_pre'].sum())} of {int(Mn['releases_pre'].sum())}; "
              f"after launch: {int(Mn['mention_post'].sum())} of {int(Mn['releases_post'].sum())}.",
              f"- Days from launch to first mentioning release: median {f(Mn['days_to_first_mention'].median(), 0)}, "
              f"interquartile range {f(Mn['days_to_first_mention'].quantile(.25), 0)} to {f(Mn['days_to_first_mention'].quantile(.75), 0)}.",
              "", "Check a sample of matches by hand: keyword patterns such as 'thinking' or 'responses' can match unrelated text."]
    open("results/results.md", "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
