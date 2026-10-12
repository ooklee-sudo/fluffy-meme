"""Specification (c) for RQ1 and the non-bug-issue control for RQ3.

Input: a weekly panel CSV with one row per repository-week and columns
    repo      repository name
    week      week start date (any parseable date), sorted within repo
    issues    total issues created that week (pull requests excluded)
    bugs      bug reports among them (label/keyword rule of Section 4.2)
    release   1 if a non-draft, non-prerelease release appeared that week
Optional: age (weeks since last release). If absent it is rebuilt from `release`.

RQ1 (Section 4.3, spec c): per repository, Poisson QMLE of weekly bug counts on
age, a linear trend and log(1 + non-bug issues); cycle-bootstrap SE; DerSimonian-Laird pooling.
Specs (a) no adjustment and (b) log(total issues) offset are run alongside.
RQ3: release logit on the standardized log(1+bugs) in t-1, with the control being
total issues (as in the manuscript) or non-bug issues (the fix); repo FE,
repository-clustered SE, and a Webb wild-cluster bootstrap on the linear probability model.

Spec (d) = (c) plus dummies for ages 1-3, which absorbs the post-release burst flexibly.
Synthetic check (--demo, true gamma = +0.03 with a release-week attention burst): (b) +0.019 and
(d) +0.016 detect the planted rise, attenuated; (a) -0.13 and (c) -0.04 miss it, because non-bug
issues are a noisy proxy for the burst. Primary tests of H1 are therefore (b) and (d); (a)/(c) nulls are uninformative.

Usage: python spec_c.py panel.csv [--boot 999] [--out results/spec_c.json]
       python spec_c.py --demo      # synthetic data, checks the code recovers a known gamma
"""
import argparse
import json
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

warnings.filterwarnings("ignore")
AGE_CAP = 8


# ---------------------------------------------------------------- data prep
def prepare(df):
    df = df.copy()
    df["week"] = pd.to_datetime(df["week"])
    df = df.sort_values(["repo", "week"]).reset_index(drop=True)
    df["nonbug"] = (df["issues"] - df["bugs"]).clip(lower=0)
    if (df["bugs"] > df["issues"]).any():
        print("warning: some weeks have bugs > issues; non-bug issues clipped at 0")
    g = df.groupby("repo", group_keys=False)
    if "age" not in df:
        def age_of(s):  # weeks since the last release, through the previous week
            out, a = [], 1
            for r in s:
                out.append(a)
                a = 1 if r else a + 1
            return pd.Series(out, index=s.index)
        df["age"] = g["release"].apply(age_of)
    df["t"] = g.cumcount() / 52.0                      # linear trend in years
    df["cycle"] = g["release"].transform(lambda s: s.shift(1, fill_value=0).cumsum())
    for c in ("bugs", "nonbug", "issues"):
        df[f"lag_{c}"] = g[c].shift(1)
    return df


# ---------------------------------------------------------------- RQ1
def design(d, spec):
    X = pd.DataFrame({"const": 1.0, "age": d["age"].astype(float), "t": d["t"]}, index=d.index)
    off = None
    if spec in ("c", "d"):
        X["log_nonbug"] = np.log1p(d["nonbug"])
    if spec == "d":  # absorb the post-release burst with flexible early-age dummies
        for k in (1, 2, 3):
            X[f"age_eq{k}"] = (d["age"] == k).astype(float)
    elif spec == "b":
        off = np.log(d["issues"].clip(lower=1))
    return X, off


def poisson_slope(d, spec):
    X, off = design(d, spec)
    m = sm.GLM(d["bugs"], X, family=sm.families.Poisson(), offset=off).fit()
    return m.params["age"]


def cycle_boot_se(d, spec, B, rng):
    """Resample whole release cycles with replacement, keep each row's calendar time."""
    cyc = [g for _, g in d.groupby("cycle")]
    est = []
    for _ in range(B):
        pick = rng.integers(0, len(cyc), len(cyc))
        try:
            est.append(poisson_slope(pd.concat([cyc[i] for i in pick]), spec))
        except Exception:
            pass
    return float(np.std(est, ddof=1)) if len(est) > 10 else np.nan


def dersimonian_laird(b, se):
    b, se = np.asarray(b), np.asarray(se)
    ok = np.isfinite(b) & np.isfinite(se) & (se > 0)
    b, se = b[ok], se[ok]
    w = 1 / se**2
    fixed = (w * b).sum() / w.sum()
    Q = (w * (b - fixed) ** 2).sum()
    tau2 = max(0.0, (Q - (len(b) - 1)) / (w.sum() - (w**2).sum() / w.sum()))
    ws = 1 / (se**2 + tau2)
    est = (ws * b).sum() / ws.sum()
    s = np.sqrt(1 / ws.sum())
    return dict(est=est, se=s, lo=est - 1.96 * s, hi=est + 1.96 * s, tau2=tau2, k=int(len(b)))


def rq1(df, B, seed):
    rng = np.random.default_rng(seed)
    out = {}
    for spec in ("a", "b", "c", "d"):
        rows = []
        for repo, d in df.groupby("repo"):
            d = d.dropna(subset=["age"])
            if d["bugs"].sum() == 0:
                continue
            b = poisson_slope(d, spec)
            se = cycle_boot_se(d, spec, B, rng)
            rows.append(dict(repo=repo, slope=b, se=se, z=b / se if se else np.nan))
        t = pd.DataFrame(rows)
        pooled = dersimonian_laird(t["slope"], t["se"])
        pooled.update(
            n_positive=int((t["slope"] > 0).sum()),
            n_sig_positive=int((t["z"] > 1.96).sum()),
            n_sig_negative=int((t["z"] < -1.96).sum()),
            max_weekly_increase_ruled_out_pct=100 * (np.exp(pooled["hi"]) - 1),
        )
        out[spec] = dict(pooled=pooled, by_repo=t.round(4).to_dict("records"))
    return out


# ---------------------------------------------------------------- RQ3
def zscore_within(s, repo):
    return (s - s.groupby(repo).transform("mean")) / s.groupby(repo).transform("std")


def rq3_data(df, control):
    d = df.dropna(subset=["lag_bugs", "lag_issues", "lag_nonbug"]).copy()
    d["z_bug"] = zscore_within(np.log1p(d["lag_bugs"]), d["repo"])
    col = "lag_issues" if control == "total" else "lag_nonbug"
    d["z_ctl"] = zscore_within(np.log1p(d[col]), d["repo"])
    d["age_c"] = d["age"].clip(upper=AGE_CAP)
    X = pd.get_dummies(d["repo"], prefix="fe", drop_first=True, dtype=float)
    X = pd.concat([d[["z_bug", "z_ctl", "age_c", "t"]], X], axis=1)
    return d, sm.add_constant(X)


def webb_wild_p(y, X, groups, var, B, rng):
    """Wild cluster bootstrap-t, Webb 6-point weights, null imposed, on a linear probability model."""
    def fit(yv, Xv):
        m = sm.OLS(yv, Xv).fit(cov_type="cluster", cov_kwds={"groups": groups})
        return m.params[var], m.bse[var], m
    b, se, _ = fit(y, X)
    t0 = b / se
    Xr = X.drop(columns=var)
    mr = sm.OLS(y, Xr).fit()
    yhat, u = mr.fittedvalues.values, mr.resid.values
    ids, inv = np.unique(groups, return_inverse=True)
    vals = np.array([-np.sqrt(1.5), -1, -np.sqrt(.5), np.sqrt(.5), 1, np.sqrt(1.5)])
    ts = []
    for _ in range(B):
        w = rng.choice(vals, len(ids))[inv]
        bb, ss, _ = fit(yhat + u * w, X)
        ts.append(bb / ss)
    return float(np.mean(np.abs(ts) >= abs(t0)))


def rq3(df, B, seed):
    rng = np.random.default_rng(seed)
    out = {}
    for control in ("total", "nonbug"):
        d, X = rq3_data(df, control)
        y = d["release"].astype(float)
        logit = sm.Logit(y, X).fit(disp=0, cov_type="cluster", cov_kwds={"groups": d["repo"].astype("category").cat.codes})
        lo, hi = logit.conf_int().loc["z_bug"]
        p_wild = webb_wild_p(y, X, d["repo"].astype("category").cat.codes.values, "z_bug", B, rng)
        out[control] = dict(
            coef_bug=float(logit.params["z_bug"]), se=float(logit.bse["z_bug"]),
            p=float(logit.pvalues["z_bug"]), ci=[float(lo), float(hi)],
            odds_ratio_upper=float(np.exp(hi)), wild_cluster_p=p_wild,
            coef_control=float(logit.params["z_ctl"]), se_control=float(logit.bse["z_ctl"]),
            n=int(len(d)), n_repos=int(d["repo"].nunique()),
        )
    return out


# ---------------------------------------------------------------- demo
def demo(gamma=0.03, repos=19, weeks=180, seed=1):
    """Synthetic panel in which bugs rise with age at a known rate (gamma on the log scale)
    and in which a release-week attention burst raises all issue types."""
    rng = np.random.default_rng(seed)
    rows = []
    for r in range(repos):
        a, base, p = 1, rng.uniform(2, 6), rng.uniform(.15, .4)
        for w in range(weeks):
            burst = 1 + 2.0 * np.exp(-(a - 1))
            nonbug = rng.poisson(base * 3 * burst)
            bugs = rng.poisson(base * burst * np.exp(gamma * a))
            rel = int(rng.random() < p)
            rows.append(dict(repo=f"r{r}", week=pd.Timestamp("2023-01-02") + pd.Timedelta(weeks=w),
                             issues=bugs + nonbug, bugs=bugs, release=rel))
            a = 1 if rel else a + 1
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("panel", nargs="?")
    ap.add_argument("--boot", type=int, default=999)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="results/spec_c.json")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        raw, a.boot = demo(), min(a.boot, 200)
    else:
        raw = pd.read_csv(a.panel)
    df = prepare(raw)
    res = dict(rq1=rq1(df, a.boot, a.seed), rq3=rq3(df, a.boot, a.seed))
    for s, name in (("a", "no adjustment"), ("b", "offset: total issues  <-- primary"), ("c", "control: log non-bug issues"), ("d", "(c) + dummies for ages 1-3  <-- primary")):
        p = res["rq1"][s]["pooled"]
        print(f"RQ1 ({s}) {name}: slope {p['est']:+.4f}  95% CI [{p['lo']:+.4f}, {p['hi']:+.4f}]  "
              f"+/sig+/sig-: {p['n_positive']}/{p['n_sig_positive']}/{p['n_sig_negative']} of {p['k']}  "
              f"rules out > {p['max_weekly_increase_ruled_out_pct']:.2f}%/week")
    d = res["rq1"]["d"]["pooled"]
    print(f"\nFor the manuscript placeholders: (c) {res['rq1']['c']['pooled']['est']:+.4f} "
          f"[{res['rq1']['c']['pooled']['lo']:+.4f}, {res['rq1']['c']['pooled']['hi']:+.4f}]; (d) {d['est']:+.4f} "
          f"[{d['lo']:+.4f}, {d['hi']:+.4f}], {d['n_positive']} positive / {d['n_sig_positive']} significantly positive of {d['k']}, "
          f"rules out > {d['max_weekly_increase_ruled_out_pct']:.1f}% per week\n")
    for c, v in res["rq3"].items():
        print(f"RQ3 control={c}: coef {v['coef_bug']:+.3f} (SE {v['se']:.3f}, p={v['p']:.2f}, wild p={v['wild_cluster_p']:.2f}); "
              f"upper OR {v['odds_ratio_upper']:.2f}")
    if not a.demo:
        with open(a.out, "w") as f:
            json.dump(res, f, indent=2, default=float)
        print("saved", a.out)


if __name__ == "__main__":
    main()
