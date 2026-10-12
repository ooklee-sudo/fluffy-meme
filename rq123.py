"""Regenerate Table 1 and the RQ1-RQ3 estimates of the manuscript from one reproducible script.

The original code behind RQ1-RQ3 is not available, so every number that the manuscript reports for these
questions is re-estimated here from the kit's own panel. Run it, then take the numbers from its output.

Outputs
  Table 1   per repository: weeks, releases, median cycle (weeks), bug log-rate slope under specs (b) and (d)
            with cycle-bootstrap SE, and release-hazard logit slope (age capped at 8) with cycle-bootstrap SE
  RQ1       pooled bug slopes (DerSimonian-Laird) for specs (a)-(d), incl. counts of positive/significant slopes
  RQ2       pooled hazard slope, and the same excluding the weekly releasers
  RQ3       logit of a release on standardized log(1+bugs) at lag 1, at lags 1-3, and on the 3-week average,
            each with the total-issues control and with the non-bug-issues control; clustered SE, wild-bootstrap p

Usage (inside isr_analysis_kit next to analyze.py and spec_c.py):
    python rq123.py --end-week 2026-10-05 --boot 999       # final numbers
    python rq123.py --end-week 2026-10-05 --boot 200       # quick look
    python rq123.py --demo                                  # synthetic data, tests the code
Writes results/rq123.json and results/table1.csv.
"""
import argparse
import json
import os
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm

import spec_c

warnings.filterwarnings("ignore")
CAP = 8


# ------------------------------------------------------------------ release hazard
def hazard_slope(d):
    d = d.dropna(subset=["age"])
    x = d["age"].clip(upper=CAP).astype(float)
    if d["release"].sum() < 5 or x.nunique() < 3:
        return np.nan
    try:
        m = sm.GLM(d["release"].astype(float), sm.add_constant(x), family=sm.families.Binomial()).fit()
        return float(m.params.iloc[1]) if np.isfinite(m.params.iloc[1]) and abs(m.params.iloc[1]) < 10 else np.nan
    except Exception:
        return np.nan


def cycle_boot(d, fit, B, rng):
    cyc = [g for _, g in d.groupby("cycle")]
    est = []
    for _ in range(B):
        pick = rng.integers(0, len(cyc), len(cyc))
        e = fit(pd.concat([cyc[i] for i in pick]))
        if np.isfinite(e):
            est.append(e)
    return float(np.std(est, ddof=1)) if len(est) > 10 else np.nan


def table1(df, B, rng):
    rows = []
    for repo, d in df.groupby("repo"):
        d = d.dropna(subset=["age"])
        rw = np.sort(d.loc[d["release"] == 1, "week"].unique())
        med = float(np.median(np.diff(rw).astype("timedelta64[D]").astype(int) / 7)) if len(rw) > 2 else np.nan
        row = dict(repo=repo, weeks=int(len(d)), releases=int(d["release"].sum()), median_cycle_weeks=med)
        for s in ("b", "d"):
            b = spec_c.poisson_slope(d, s)
            row[f"bug_{s}"], row[f"bug_{s}_se"] = b, spec_c.cycle_boot_se(d, s, B, rng)
        h = hazard_slope(d)
        row["hazard"], row["hazard_se"] = h, cycle_boot(d, hazard_slope, B, rng) if np.isfinite(h) else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def pooled(t, col, mask=None):
    t = t if mask is None else t[mask]
    p = spec_c.dersimonian_laird(t[col], t[col + "_se"])
    z = t[col] / t[col + "_se"]
    p.update(n_positive=int((t[col] > 0).sum()), n_sig_positive=int((z > 1.96).sum()), n_sig_negative=int((z < -1.96).sum()))
    return p


# ------------------------------------------------------------------ RQ3 with lags
def zs(s, repo):
    lg = np.log1p(s)
    return (lg - lg.groupby(repo).transform("mean")) / lg.groupby(repo).transform("std")


def rq3_lags(df, control, B, rng):
    d = df.copy()
    g = d.groupby("repo")
    for k in (2, 3):
        d[f"lag{k}_bugs"] = g["bugs"].shift(k)
    d = d.dropna(subset=["lag_bugs", "lag2_bugs", "lag3_bugs", "lag_issues", "lag_nonbug"])
    d["z1"], d["z2"], d["z3"] = zs(d["lag_bugs"], d["repo"]), zs(d["lag2_bugs"], d["repo"]), zs(d["lag3_bugs"], d["repo"])
    d["z_avg"] = (d["z1"] + d["z2"] + d["z3"]) / 3
    d["z_ctl"] = zs(d["lag_issues" if control == "total" else "lag_nonbug"], d["repo"])
    d["age_c"] = d["age"].clip(upper=CAP)
    fe = pd.get_dummies(d["repo"], prefix="fe", drop_first=True, dtype=float)
    grp = pd.factorize(d["repo"])[0]
    y = d["release"].astype(float)
    out = {}

    def fit(cols):
        X = sm.add_constant(pd.concat([d[cols + ["z_ctl", "age_c", "t"]], fe], axis=1))
        return X, sm.Logit(y, X).fit(disp=0, cov_type="cluster", cov_kwds={"groups": grp})

    X, m = fit(["z1"])
    out["lag1"] = dict(coef=float(m.params["z1"]), se=float(m.bse["z1"]), p=float(m.pvalues["z1"]),
                       wild_p=spec_c.webb_wild_p(y, X, grp, "z1", B, rng))
    X, m = fit(["z1", "z2", "z3"])
    out["lags123"] = {k: dict(coef=float(m.params[k]), se=float(m.bse[k])) for k in ("z1", "z2", "z3")}
    X, m = fit(["z_avg"])
    out["avg3"] = dict(coef=float(m.params["z_avg"]), se=float(m.bse["z_avg"]), p=float(m.pvalues["z_avg"]),
                       wild_p=spec_c.webb_wild_p(y, X, grp, "z_avg", B, rng))
    out["control_coef"] = float(m.params["z_ctl"])
    out["n"], out["n_repos"] = int(len(d)), int(d["repo"].nunique())
    return out


# ------------------------------------------------------------------ main
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
        raw, a.boot = spec_c.demo(), min(a.boot, 60)
    else:
        from extra_analyses import build, raw_panel
        P, _ = build(a.data, a.end_week)
        raw = raw_panel(P)
    df = spec_c.prepare(raw)
    print(f"panel: {df['repo'].nunique()} repositories, {len(df)} repository-weeks, {int(df['release'].sum())} release-weeks")

    res = {}
    t = table1(df, a.boot, rng)
    os.makedirs("results", exist_ok=True)
    t.round(4).to_csv("results/table1.csv", index=False)
    print("\nTable 1 -> results/table1.csv")
    print(t.round(3).to_string(index=False))

    weekly = t["median_cycle_weeks"] <= 1
    res["rq1"] = {s: pooled(t, f"bug_{s}") for s in ("b", "d")}
    res["rq2"] = dict(all=pooled(t, "hazard"), excluding_weekly_releasers=pooled(t, "hazard", ~weekly), n_weekly=int(weekly.sum()))
    print("\nRQ1 (pooled, from Table 1 repository slopes):")
    for s, p in res["rq1"].items():
        print(f"  spec ({s}): {p['est']:+.4f} [{p['lo']:+.4f}, {p['hi']:+.4f}]  +/sig+/sig-: {p['n_positive']}/{p['n_sig_positive']}/{p['n_sig_negative']}  tau2={p['tau2']:.5f}")
    print("RQ2 (pooled hazard slope per week of age):")
    for k in ("all", "excluding_weekly_releasers"):
        p = res["rq2"][k]
        print(f"  {k}: {p['est']:+.3f} [{p['lo']:+.3f}, {p['hi']:+.3f}]  +/sig+/sig-: {p['n_positive']}/{p['n_sig_positive']}/{p['n_sig_negative']}  tau2={p['tau2']:.3f}")

    res["rq3"] = {}
    print("RQ3 (logit of a release on standardized log(1+bugs); clustered SE; wild-cluster p, Webb):")
    for c in ("total", "nonbug"):
        r = rq3_lags(df, c, a.boot, rng)
        res["rq3"][c] = r
        l1, av = r["lag1"], r["avg3"]
        lg = r["lags123"]
        print(f"  control={c}: lag1 {l1['coef']:+.3f} (SE {l1['se']:.3f}, p={l1['p']:.2f}, wild p={l1['wild_p']:.2f}); "
              f"lags1-3 {lg['z1']['coef']:+.3f}/{lg['z2']['coef']:+.3f}/{lg['z3']['coef']:+.3f}; "
              f"3-week average {av['coef']:+.3f} (SE {av['se']:.3f}, p={av['p']:.2f}, wild p={av['wild_p']:.2f}); n={r['n']}")
    json.dump(res, open("results/rq123.json", "w"), indent=2, default=float)
    print("\nsaved results/rq123.json")


if __name__ == "__main__":
    main()
