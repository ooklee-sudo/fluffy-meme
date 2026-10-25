"""NHPP fits of post-release bug discovery curves from the Public Jira Dataset (human-only baseline).

Input: bugs.csv produced by jira_extract_bugs.py.
Attribution: each bug is attributed to the affected version with the latest release date that is <= the bug's
creation date (the version in use when it was found). Event time s = days since that release.
Unit of analysis: (repo, project, version) with >= MIN_BUGS bugs inside the observation horizon.
Horizon: min(HMAX days, days from release to the repo's last observed issue creation); bins of 30 days.
Models (Poisson likelihood on 30-day bin counts):
  HPP  m(s)=lam*s               (1 parameter)
  GO   m(s)=a(1-exp(-b s))      (finite total a)
  MO   m(s)=a ln(1+b s)         (no finite total; Musa-Okumoto)
Usage: python3 -I jira_nhpp.py <bugs.csv> [out.csv]
"""
import sys
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import gammaln

MIN_BUGS, HMAX, BIN, MIN_H = 25, 360, 30, 180
bugs = pd.read_csv(sys.argv[1], dtype=str).fillna("")
out_csv = sys.argv[2] if len(sys.argv) > 2 else "jira_nhpp_results.csv"
bugs["created"] = pd.to_datetime(bugs.created, utc=True, errors="coerce").dt.tz_localize(None)


def parse_versions(s):
    res = []
    for item in s.split(";"):
        if "|" not in item:
            continue
        name, date = item.rsplit("|", 1)
        d = pd.to_datetime(date, errors="coerce")
        if pd.notna(d):
            res.append((name, d))
    return res


rows = []
for r in bugs.itertuples(index=False):
    if pd.isna(r.created):
        continue
    vs = [(n, d) for n, d in parse_versions(r.affects) if d <= r.created]
    if not vs:
        continue
    name, rel = max(vs, key=lambda x: x[1])
    rows.append((r.repo, r.project, name, rel, (r.created - rel).days, r.priority, r.created))
ev = pd.DataFrame(rows, columns=["repo", "project", "version", "release", "s", "priority", "created"])
print(f"bugs: {len(bugs)} | attributable to a dated, already-released affected version: {len(ev)} ({len(ev)/max(len(bugs),1):.0%})")
last_obs = bugs.groupby("repo").created.max()

HIGH = {"blocker", "critical", "highest", "high", "major (p2)", "p1", "p0", "critical - p2", "blocker - p1"}
res = []
for (repo, proj, ver, rel), g in ev.groupby(["repo", "project", "version", "release"]):
    H = min(HMAX, (last_obs[repo] - rel).days)
    if H < MIN_H:
        continue
    K = H // BIN
    s = g.s.values
    s = s[s < K * BIN]
    if len(s) < MIN_BUGS:
        continue
    n = np.histogram(s, bins=np.arange(0, (K + 1) * BIN, BIN))[0].astype(float)
    t = np.arange(0, K + 1) * BIN
    N = n.sum()

    def nll(mu):
        mu = np.nan_to_num(np.maximum(mu, 1e-12), nan=1e-12, posinf=1e12)
        return -(n * np.log(mu) - mu - gammaln(n + 1)).sum()

    def fit(kind):
        best = None
        for a0, b0 in ((N * 1.5, 0.02), (N * 3, 0.005), (N, 0.1)):
            if kind == "HPP":
                x0 = [np.log(N / t[-1])]
                f = lambda x: nll(np.exp(x[0]) * np.diff(t))
            elif kind == "GO":
                x0 = [np.log(a0), np.log(b0)]
                f = lambda x: nll(np.exp(x[0]) * (np.exp(-np.exp(x[1]) * t[:-1]) - np.exp(-np.exp(x[1]) * t[1:])))
            else:
                x0 = [np.log(max(N / 3, 1)), np.log(0.05)]
                f = lambda x: nll(np.exp(x[0]) * (np.log1p(np.exp(x[1]) * t[1:]) - np.log1p(np.exp(x[1]) * t[:-1])))
            if kind == "HPP":
                r = minimize(f, x0, method="Nelder-Mead")
            else:                                     # bounded: b per day in [1e-4, 1], total a in [N/10, 100 N]
                bnds = [(np.log(N / 10), np.log(N * 100)), (np.log(1e-4), np.log(1.0))]
                with np.errstate(all="ignore"):
                    r = minimize(f, np.clip(x0, [b[0] for b in bnds], [b[1] for b in bnds]), method="L-BFGS-B", bounds=bnds)
            if best is None or r.fun < best.fun:
                best = r
            if kind == "HPP":
                break
        return best

    fits = {k: fit(k) for k in ("HPP", "GO", "MO")}
    aic = {k: 2 * len(v.x) + 2 * v.fun for k, v in fits.items()}
    go, mo = fits["GO"].x, fits["MO"].x
    pri = g.priority.str.lower()
    res.append(dict(repo=repo, project=proj, version=ver, release=rel.date(), horizon=K * BIN, bugs=int(N),
                    a_GO=np.exp(go[0]), b_GO_per30d=np.exp(go[1]) * BIN, a_MO=np.exp(mo[0]), b_MO_per30d=np.exp(mo[1]) * BIN,
                    aic_HPP=aic["HPP"], aic_GO=aic["GO"], aic_MO=aic["MO"], best=min(aic, key=aic.get),
                    share_high=pri.isin(HIGH).mean(), first_bin_share=n[0] / N))
R = pd.DataFrame(res)
R.to_csv(out_csv, index=False)
print(f"versions fitted: {len(R)} (projects {R.project.nunique() if len(R) else 0}, repos {R.repo.nunique() if len(R) else 0})")
if len(R):
    print("best model by AIC:", R.best.value_counts().to_dict())
    d_go_mo = R.aic_GO - R.aic_MO
    print(f"AIC(GO) - AIC(MO): median {d_go_mo.median():.2f}; MO better by >2 in {(d_go_mo > 2).mean():.0%}, GO better by >2 in {(d_go_mo < -2).mean():.0%}")
    print("GO fit: median total a %.0f (IQR %.0f-%.0f), median b per 30 days %.3f (IQR %.3f-%.3f)" % (
        R.a_GO.median(), R.a_GO.quantile(.25), R.a_GO.quantile(.75), R.b_GO_per30d.median(), R.b_GO_per30d.quantile(.25), R.b_GO_per30d.quantile(.75)))
    ratio = R.a_GO / R.bugs
    print("ratio a_GO / observed bugs: median %.2f; share with ratio > 3 (no saturation within the horizon): %.0f%%" % (ratio.median(), 100 * (ratio > 3).mean()))
    sat = R[ratio <= 3]
    print(f"saturating fits (a_GO <= 3 x observed): {len(sat)} of {len(R)}; median b per 30 days {sat.b_GO_per30d.median():.3f}")
    print("share of bugs found in the first 30 days: median %.2f" % R.first_bin_share.median())
    lr = np.log(sat[["a_GO", "b_GO_per30d"]]); sh = sat.share_high; print("(on saturating fits)", end=" "); print("log a vs log b correlation: %.2f; sd log a %.2f, sd log b %.2f" % (lr.a_GO.corr(lr.b_GO_per30d), lr.a_GO.std(), lr.b_GO_per30d.std()))
    print("correlation of share_high with log a: %.2f, with log b: %.2f" % (sh.corr(lr.a_GO), sh.corr(lr.b_GO_per30d)))
