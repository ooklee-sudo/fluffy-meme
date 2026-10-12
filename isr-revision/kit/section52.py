"""Regenerate the Section 5.2 numbers that the original code produced: hot-fix shares, the hazard of regular
releases, the frailty (random-intercept) hazard model, and the coefficients of variation of release intervals.

Usage (inside isr_analysis_kit next to analyze.py, spec_c.py, extra_analyses.py, data/):
    python section52.py --end-week 2026-10-05 --boot 200
    python section52.py --demo                      # synthetic data, tests the code
Writes results/section52.json. Paste the printed output back into the conversation.

Definitions follow Section 4.3 of the manuscript:
  hot-fix       patch-only version change vs. the previous release with the same tag prefix, within 7 days (analyze.py);
  age           weeks since the previous release (all releases) or since the previous regular release, capped at 8;
  frailty       pooled logit with a normal repository intercept, integrated by 24-point Gauss-Hermite quadrature;
  weekly releaser  median gap between release weeks of at most one week.
"""
import argparse
import json
import os
import re
import warnings

import numpy as np
import pandas as pd
from scipy import optimize
from scipy.special import expit, logsumexp

import spec_c

warnings.filterwarnings("ignore")
CAP = 8
VER = re.compile(r"v?(\d+)\.(\d+)(?:\.(\d+))?")


# ----------------------------------------------------------------------------- hot-fix facts
def hotfix_facts(P, R):
    out = {}
    out["releases_collected"] = int(len(R))
    out["share_hotfix_7day_rule"] = float(R["hot_time"].mean())
    out["share_hotfix_by_repo"] = R.groupby("repo")["hot_time"].mean().round(3).to_dict()
    # age profile of hot-fix weeks (age = weeks since previous release of any kind)
    a = P.dropna(subset=["age_any"]).copy()
    a["age"] = a["age_any"].clip(upper=CAP).astype(int)
    out["share_weeks_with_hotfix_by_age"] = a.groupby("age")["n_hot"].apply(lambda s: float((s > 0).mean())).round(3).to_dict()
    # version-only rule and its timing
    days = []
    for repo, g in R.sort_values("published_at").groupby("repo"):
        last = {}
        for r in g.itertuples():
            m = VER.search(r.tag)
            if not m:
                continue
            pre, v = r.tag[:m.start()], (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))
            if pre in last and v[:2] == last[pre][0][:2] and v[2] > last[pre][0][2]:
                days.append((r.ts - last[pre][1]).days)
            last[pre] = (v, r.ts)
    days = np.array(days)
    out["share_patch_only_version_rule"] = float(R["hot_ver"].mean())
    out["share_of_patch_only_within_7_days"] = float((days < 7).mean()) if len(days) else None
    out["median_days_patch_only_within_7_days"] = float(np.median(days[days < 7])) if (days < 7).any() else None
    return out


# ----------------------------------------------------------------------------- regular-release hazard
def logit_slope(d, ycol, agecol):
    d = d.dropna(subset=[agecol])
    x = d[agecol].clip(upper=CAP).astype(float).values
    y = d[ycol].astype(float).values
    if y.sum() < 5 or len(np.unique(x)) < 3:
        return np.nan
    X = np.column_stack([np.ones(len(x)), x])
    b = np.zeros(2)
    for _ in range(50):
        p = expit(X @ b)
        H = (X * (p * (1 - p))[:, None]).T @ X + 1e-6 * np.eye(2)
        step = np.linalg.solve(H, X.T @ (y - p))
        b += step
        if np.max(np.abs(step)) < 1e-8:
            break
    return float(b[1]) if np.isfinite(b[1]) and abs(b[1]) < 10 else np.nan


def regular_hazard(P, B, rng):
    rows = []
    for repo, g in P.groupby("repo"):
        g = g.dropna(subset=["age_reg"])
        b = logit_slope(g, "any_reg", "age_reg")
        cyc = [c for _, c in g.groupby("cycle")]
        est = []
        for _ in range(B if np.isfinite(b) else 0):
            pick = rng.integers(0, len(cyc), len(cyc))
            e = logit_slope(pd.concat([cyc[i] for i in pick]), "any_reg", "age_reg")
            if np.isfinite(e):
                est.append(e)
        rows.append(dict(repo=repo, slope=b, se=float(np.std(est, ddof=1)) if len(est) > 10 else np.nan))
    t = pd.DataFrame(rows)
    p = spec_c.dersimonian_laird(t["slope"], t["se"])
    z = t["slope"] / t["se"]
    p.update(n_sig_positive=int((z > 1.96).sum()), n_sig_negative=int((z < -1.96).sum()), n_repos=int(t["slope"].notna().sum()))
    a = P.dropna(subset=["age_reg"]).copy()
    a["age"] = a["age_reg"].clip(upper=CAP).astype(int)
    share = a.groupby("age")["any_reg"].mean()
    p["pooled_share_regular_release_at_age"] = {int(k): round(float(v), 3) for k, v in share.items()}
    return p


# ----------------------------------------------------------------------------- frailty
def frailty_fit(d, ycol, agecol, K=24):
    d = d.dropna(subset=[agecol])
    x = d[agecol].clip(upper=CAP).astype(float).values
    y = d[ycol].astype(float).values
    g = pd.factorize(d["repo"])[0]
    nodes, w = np.polynomial.hermite.hermgauss(K)
    logw = np.log(w) - 0.5 * np.log(np.pi)
    idx = [np.where(g == k)[0] for k in range(g.max() + 1)]

    def nll(th):
        a, b, ls = th
        s = np.exp(ls)
        tot = 0.0
        for ix in idx:
            eta = a + b * x[ix][None, :] + (np.sqrt(2) * s * nodes)[:, None]
            ll = (y[ix][None, :] * -np.logaddexp(0, -eta) + (1 - y[ix][None, :]) * -np.logaddexp(0, eta)).sum(1)
            tot += logsumexp(ll + logw)
        return -tot

    r = optimize.minimize(nll, [-1.0, 0.0, 0.0], method="BFGS")
    th, h, k = r.x, 1e-3, len(r.x)
    H = np.zeros((k, k))
    for i in range(k):
        for j in range(k):
            e_i, e_j = np.eye(k)[i] * h, np.eye(k)[j] * h
            H[i, j] = (nll(th + e_i + e_j) - nll(th + e_i - e_j) - nll(th - e_i + e_j) + nll(th - e_i - e_j)) / (4 * h * h)
    try:
        cov = np.linalg.inv(H)
        se = float(np.sqrt(cov[1, 1]))
    except Exception:
        se = np.nan
    return dict(slope=float(th[1]), se=se, sd_intercept=float(np.exp(th[2])), n=int(len(y)))


def frailty_block(P, weekly):
    out = {}
    out["all releases, age"] = frailty_fit(P.assign(y=P["any_rel"]), "y", "age_any")
    out["all releases, excluding weekly releasers"] = frailty_fit(P[~P["repo"].isin(weekly)].assign(y=P["any_rel"]), "y", "age_any")
    out["all releases, ages 2 and above"] = frailty_fit(P[P["age_any"] >= 2].assign(y=P["any_rel"]), "y", "age_any")
    out["regular releases, age since last regular"] = frailty_fit(P.assign(y=P["any_reg"]), "y", "age_reg")
    out["regular releases, excluding weekly releasers"] = frailty_fit(P[~P["repo"].isin(weekly)].assign(y=P["any_reg"]), "y", "age_reg")
    return out


# ----------------------------------------------------------------------------- CV of intervals
def cv_block(R):
    rows = []
    for repo, g in R[R["published_at"] >= "2023-01-01"].groupby("repo"):
        for label, s in (("any", g), ("regular", g[~g["hot_time"]])):
            d = np.diff(np.sort(s["ts"].values)).astype("timedelta64[s]").astype(float) / 86400
            if len(d) >= 5 and d.mean() > 0:
                rows.append(dict(repo=repo, kind=label, cv=float(d.std(ddof=1) / d.mean())))
    t = pd.DataFrame(rows)
    out = {}
    for kind, s in t.groupby("kind"):
        out[kind] = dict(median=float(s["cv"].median()), min=float(s["cv"].min()), max=float(s["cv"].max()),
                         n_above_one=int((s["cv"] > 1).sum()), n_below_one=int((s["cv"] < 1).sum()), n=int(len(s)))
    return out


# ----------------------------------------------------------------------------- demo data
def demo_panel():
    rng = np.random.default_rng(5)
    Ps, Rs = [], []
    for r in range(8):
        weeks = pd.date_range("2023-01-02", periods=150, freq="7D")
        any_rel, age, last = [], [], None
        tag_v = 0
        rel_rows = []
        for i, w in enumerate(weeks):
            rel = rng.random() < (0.5 if r < 3 else 0.2)
            age.append(np.nan if last is None else i - last)
            if rel:
                tag_v += 1
                hot = rng.random() < 0.4
                ts = pd.Timestamp(w) + pd.Timedelta(days=int(rng.integers(0, 6)))
                rel_rows.append(dict(repo=f"r{r}", tag=f"v1.{tag_v}.0", published_at=ts.isoformat(), ts=ts, week=w, hot_time=hot, hot_ver=hot))
                last = i
            any_rel.append(int(rel))
        P = pd.DataFrame(dict(repo=f"r{r}", week=weeks, any_rel=any_rel, age_any=age))
        # regular = not hot: crude
        hw = {x["week"] for x in rel_rows if x["hot_time"]}
        P["n_hot"] = P["week"].isin(hw).astype(int)
        P["any_reg"] = ((P["any_rel"] == 1) & (P["n_hot"] == 0)).astype(int)
        a2, lr = [], None
        for i, v in enumerate(P["any_reg"]):
            a2.append(np.nan if lr is None else i - lr)
            if v:
                lr = i
        P["age_reg"] = a2
        P["cycle"] = P["any_reg"].shift(1, fill_value=0).cumsum()
        Ps.append(P); Rs.append(pd.DataFrame(rel_rows))
    return pd.concat(Ps, ignore_index=True), pd.concat(Rs, ignore_index=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--end-week", default=None)
    ap.add_argument("--boot", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    if a.demo:
        P, R = demo_panel()
        a.boot = min(a.boot, 40)
    else:
        from extra_analyses import build
        P, R = build(a.data, a.end_week)
    R = R.copy()
    if "ts" not in R:
        R["ts"] = pd.to_datetime(R["published_at"], utc=True)
    res = {}

    res["hotfix"] = hotfix_facts(P, R)
    print("HOT-FIX FACTS")
    for k, v in res["hotfix"].items():
        print(f"  {k}: {v}")

    res["regular_hazard"] = regular_hazard(P, a.boot, rng)
    h = res["regular_hazard"]
    print(f"\nREGULAR-RELEASE HAZARD (age since last regular, no trend): pooled {h['est']:+.3f} [{h['lo']:+.3f}, {h['hi']:+.3f}] "
          f"tau2={h['tau2']:.3f}; significantly positive {h['n_sig_positive']}, negative {h['n_sig_negative']} of {h['n_repos']}")
    print("  pooled share of repository-weeks with a regular release, by age:", h["pooled_share_regular_release_at_age"])

    g = P.groupby("repo")["any_rel"].apply(lambda s: s)  # placeholder to keep index logic simple
    gaps = {}
    for repo, d in P.groupby("repo"):
        rw = np.sort(d.loc[d["any_rel"] == 1, "week"].values)
        gaps[repo] = np.median(np.diff(rw).astype("timedelta64[D]").astype(int) / 7) if len(rw) > 2 else np.nan
    weekly = [r for r, v in gaps.items() if v <= 1]
    res["weekly_releasers"] = weekly
    print(f"\nWEEKLY RELEASERS ({len(weekly)}): {weekly}")

    res["frailty"] = frailty_block(P, weekly)
    print("\nFRAILTY MODELS (slope per week of age, SE, SD of repository intercept):")
    for k, v in res["frailty"].items():
        print(f"  {k}: {v['slope']:+.3f} (SE {v['se']:.3f}); SD {v['sd_intercept']:.2f}; n={v['n']}")

    res["cv"] = cv_block(R)
    print("\nCOEFFICIENT OF VARIATION OF RELEASE INTERVALS (days):")
    for k, v in res["cv"].items():
        print(f"  {k}: median {v['median']:.2f} (range {v['min']:.2f} to {v['max']:.2f}); above one in {v['n_above_one']}, below one in {v['n_below_one']} of {v['n']}")

    os.makedirs("results", exist_ok=True)
    json.dump(res, open("results/section52.json", "w"), indent=2, default=float)
    print("\nsaved results/section52.json")


if __name__ == "__main__":
    main()
