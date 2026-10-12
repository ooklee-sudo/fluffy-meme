"""Three add-on analyses for the manuscript, run on the kit's own data.

 1. CONTENT: does what a release contains respond to bug reports even though its timing does not?
    Release-level OLS of the share of release-note items that are fixes on the bug reports of the
    preceding four weeks, controlling for non-bug issues, time since the previous release, a trend and
    repository fixed effects; repository-clustered SE and Webb wild-cluster bootstrap p.
 2. EQUIVALENCE: for each null (RQ1 slope, RQ3 bug-surge coefficient, launch event study) a TOST p-value
    against a stated smallest effect of interest, the smallest bound that equivalence would hold for,
    and the minimum detectable effect at 80% power. Needs results/spec_c.json from spec_c.py.
 3. HETEROGENEITY: RQ1 (specs b and d) and the RQ3 coefficient re-estimated without the automated-release
    repositories, for weekly versus slower releasers, and by repository category.

Usage (inside isr_analysis_kit, next to analyze.py, spec_c.py, data/, repo_relevance.csv):
    python spec_c.py --end-week 2026-10-05 --boot 999        # first, to create results/spec_c.json
    python extra_analyses.py --end-week 2026-10-05 --boot 499
Writes results/extra.json and prints a block you can paste back into the conversation.
Check a sample of the fix-item classifier by hand (printed at the end), as the README does for model mentions.
"""
import argparse
import glob
import json
import os
import re
import warnings

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

import spec_c

warnings.filterwarnings("ignore")
AUTO = ["anthropics/anthropic-sdk-python", "openai/openai-python"]  # release-please / Stainless pipelines (Section 5.2)
BULLET = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+(.*\S)")
HEAD = re.compile(r"^\s*#{1,6}\s*(.*\S)")
FIXWORD = re.compile(r"\b(fix(?:es|ed|ing)?|bug\s?fix(?:es)?|hot\s?fix|regression|crash(?:es)?|resolve[sd]?|workaround|patch(?:ed)?)\b", re.I)
FIXHEAD = re.compile(r"\b(fix|bug|patch)", re.I)


# --------------------------------------------------------------------------- data
def build(data, end_week):
    from analyze import build_panel
    dirs = sorted(glob.glob(f"{data}/*__*"))
    if not dirs:
        raise SystemExit(f"no repository folders in {data}/")
    pairs = [build_panel(d, end_week) for d in dirs]
    P = pd.concat([p for p, _ in pairs], ignore_index=True)
    R = pd.concat([r for _, r in pairs], ignore_index=True)
    return P, R


def raw_panel(P):
    return P[["repo", "week", "issues", "bugs", "any_rel", "age_any"]].rename(columns={"any_rel": "release", "age_any": "age"})


# --------------------------------------------------------------------------- 1. content
def fix_share(body):
    """(n_items, n_fix) over bullet items of one release note. Items under a fix/bug heading count as fixes."""
    n = nf = 0
    in_fix = False
    skip = False
    for line in (body or "").splitlines():
        h = HEAD.match(line)
        if h:
            in_fix = bool(FIXHEAD.search(h.group(1)))
            skip = bool(re.search(r"contributor|acknowledg|thank", h.group(1), re.I))  # name lists are not changes
            continue
        b = BULLET.match(line)
        if b and not skip and not re.fullmatch(r"@[\w-]+|\**full changelog.*", b.group(1).strip(), re.I):
            n += 1
            nf += int(in_fix or bool(FIXWORD.search(b.group(1))))
    return n, nf


def content_analysis(P, R, B, seed, min_items=3, window=4):
    rng = np.random.default_rng(seed)
    P = P.sort_values(["repo", "week"]).copy()
    P["nonbug"] = (P["issues"] - P["bugs"]).clip(lower=0)
    g = P.groupby("repo")
    P["bug_w"] = g["bugs"].transform(lambda s: s.shift(1).rolling(window, min_periods=window).sum())
    P["non_w"] = g["nonbug"].transform(lambda s: s.shift(1).rolling(window, min_periods=window).sum())
    for c in ("bug_w", "non_w"):
        lg = np.log1p(P[c])
        P["z_" + c] = (lg - lg.groupby(P["repo"]).transform("mean")) / lg.groupby(P["repo"]).transform("std")
    P["trend_y"] = (P["week"] - P["week"].min()).dt.days / 365.25
    R = R.copy()
    R[["n_items", "n_fix"]] = R["body"].apply(lambda b: pd.Series(fix_share(b)))
    R = R[R["n_items"] >= min_items]
    R["share"] = R["n_fix"] / R["n_items"]
    d = R.merge(P[["repo", "week", "z_bug_w", "z_non_w", "age_any", "trend_y"]], on=["repo", "week"], how="inner")
    d = d.dropna(subset=["z_bug_w", "z_non_w", "age_any"])
    d["log_gap"] = np.log1p(d["age_any"])
    out = dict(n_releases=int(len(d)), n_repos=int(d["repo"].nunique()), mean_fix_share=float(d["share"].mean()))
    if len(d) < 50 or d["repo"].nunique() < 4:
        return dict(out, note="too few releases with itemised notes"), d
    X = pd.concat([d[["z_bug_w", "z_non_w", "log_gap", "trend_y"]],
                   pd.get_dummies(d["repo"], prefix="fe", drop_first=True, dtype=float)], axis=1)
    X = sm.add_constant(X)
    y = d["share"].astype(float)
    grp = pd.factorize(d["repo"])[0]
    m = sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": grp})
    lo, hi = m.conf_int().loc["z_bug_w"]
    out.update(coef_bugs=float(m.params["z_bug_w"]), se=float(m.bse["z_bug_w"]), ci=[float(lo), float(hi)], p=float(m.pvalues["z_bug_w"]),
               coef_nonbug=float(m.params["z_non_w"]), coef_gap=float(m.params["log_gap"]),
               wild_p=spec_c.webb_wild_p(y, X, grp, "z_bug_w", B, rng))
    return out, d


# --------------------------------------------------------------------------- 2. equivalence
def tost(est, se, bound):
    p_lo = 1 - stats.norm.cdf((est + bound) / se)
    p_hi = 1 - stats.norm.cdf((bound - est) / se)
    return float(max(p_lo, p_hi))


def equiv_row(name, est, se, bound, unit):
    return dict(test=name, est=float(est), se=float(se), bound=bound, unit=unit, tost_p=tost(est, se, bound),
                equivalent_at_bound=bool(tost(est, se, bound) < 0.05),
                smallest_bound_for_equivalence=float(abs(est) + 1.645 * se),
                min_detectable_effect_80pct=float((1.96 + 0.84) * se))


def equivalence(spec_json, b_rq1, b_rq3, ev_est, ev_se, b_ev):
    r = json.load(open(spec_json))
    rows = []
    for s in ("b", "d"):
        if s in r["rq1"]:
            p = r["rq1"][s]["pooled"]
            rows.append(equiv_row(f"RQ1 age slope, spec ({s})", p["est"], p["se"], b_rq1, "log bug rate per week"))
    for c, v in r["rq3"].items():
        rows.append(equiv_row(f"RQ3 bug surge, control={c}", v["coef_bug"], v["se"], b_rq3, "log-odds per SD"))
    rows.append(equiv_row("Launch event study, weeks 0-4", ev_est, ev_se, b_ev, "release probability"))
    return rows


# --------------------------------------------------------------------------- 3. heterogeneity
def rq3_logit(df):
    try:
        d, X = spec_c.rq3_data(df, "nonbug")
        y = d["release"].astype(float)
        m = sm.Logit(y, X).fit(disp=0, cov_type="cluster", cov_kwds={"groups": pd.factorize(d["repo"])[0]})
        lo, hi = m.conf_int().loc["z_bug"]
        return dict(coef=float(m.params["z_bug"]), se=float(m.bse["z_bug"]), ci=[float(lo), float(hi)], n_repos=int(d["repo"].nunique()))
    except Exception as e:
        return dict(error=str(e)[:100])


def heterogeneity(df, rel_pairs, cats, B, seed, auto):
    # Weekly releasers: median gap between release weeks of at most one week, measured on the panel weeks (same rule
    # as section52.py and the median release cycle of Table 1; selects the same seven repositories). An earlier version
    # measured the gap on all collected releases, including those before the panel starts, which selected six.
    gaps = df[df["release"] == 1].groupby("repo")["week"].apply(
        lambda s: np.median(np.diff(np.sort(s.unique())).astype("timedelta64[D]").astype(int) / 7) if s.nunique() > 2 else np.nan)
    weekly = set(gaps.index[gaps <= 1])
    groups = {"all": set(df["repo"]), "excluding automated-release": set(df["repo"]) - set(auto),
              "weekly releasers": set(df["repo"]) & weekly, "slower releasers": set(df["repo"]) - weekly}
    for c, rs in cats.groupby("category"):
        rs = set(rs["repo"]) & set(df["repo"])
        if len(rs) >= 3:
            groups[f"category: {c}"] = rs
    out = {}
    for name, rs in groups.items():
        sub = df[df["repo"].isin(rs)]
        if sub["repo"].nunique() < 3:
            continue
        try:
            r1 = spec_c.rq1(sub, B, seed, specs=("b", "d"))
        except TypeError:  # older spec_c.py without the specs argument: run all four, use b and d
            r1 = spec_c.rq1(sub, B, seed)
        out[name] = dict(n_repos=int(sub["repo"].nunique()),
                         rq1={s: {k: float(r1[s]["pooled"][k]) for k in ("est", "lo", "hi")} for s in r1},
                         rq3_nonbug=rq3_logit(sub))
    return out


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data")
    ap.add_argument("--end-week", default=None)
    ap.add_argument("--boot", type=int, default=499)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--spec-json", default="results/spec_c.json")
    ap.add_argument("--relevance", default="repo_relevance.csv")
    ap.add_argument("--bound-rq1", type=float, default=0.02, help="smallest effect of interest: 2%% per week in the bug rate")
    ap.add_argument("--bound-rq3", type=float, default=0.25, help="log-odds per SD; the size of the response to total issues that the data do detect")
    ap.add_argument("--event-est", type=float, default=-0.002)
    ap.add_argument("--event-se", type=float, default=0.018)
    ap.add_argument("--bound-event", type=float, default=0.05, help="release probability, about 12%% of the 0.42 pre-launch rate")
    ap.add_argument("--out", default="results/extra.json")
    ap.add_argument("--only-heterogeneity", action="store_true", help="rerun Section 3 only and update it in --out")
    a = ap.parse_args()

    P, R = build(a.data, a.end_week)
    res = {}

    if a.only_heterogeneity and os.path.exists(a.out):
        res = json.load(open(a.out))
    else:
        print("== 1. Release content ==")
        res["content"], d = content_analysis(P, R, a.boot, a.seed)
        print(json.dumps(res["content"], indent=1))

        print("== 2. Equivalence ==")
        if os.path.exists(a.spec_json):
            res["equivalence"] = equivalence(a.spec_json, a.bound_rq1, a.bound_rq3, a.event_est, a.event_se, a.bound_event)
            for r in res["equivalence"]:
                print(f"{r['test']}: est {r['est']:+.4f} (SE {r['se']:.4f}); TOST p={r['tost_p']:.3f} for +/-{r['bound']} {r['unit']}; "
                      f"equivalence holds for any bound >= {r['smallest_bound_for_equivalence']:.3f}; MDE(80%) {r['min_detectable_effect_80pct']:.3f}")
        else:
            print(f"skipped: {a.spec_json} not found; run spec_c.py first")

    print("== 3. Heterogeneity ==")
    cats = pd.read_csv(a.relevance)[["repo", "category"]] if os.path.exists(a.relevance) else pd.DataFrame(columns=["repo", "category"])
    df = spec_c.prepare(raw_panel(P))
    res["heterogeneity"] = heterogeneity(df, R, cats, a.boot, a.seed, AUTO)
    for k, v in res["heterogeneity"].items():
        b, dd = v["rq1"].get("b"), v["rq1"].get("d")
        fmt = lambda x: f"{x['est']:+.4f} [{x['lo']:+.4f}, {x['hi']:+.4f}]" if x else "n/a"
        r3 = v["rq3_nonbug"]
        print(f"{k} ({v['n_repos']} repos): RQ1(b) {fmt(b)}  RQ1(d) {fmt(dd)}  RQ3 coef " +
              (f"{r3['coef']:+.3f} (SE {r3['se']:.3f})" if "coef" in r3 else r3.get("error", "")))

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump(res, open(a.out, "w"), indent=2, default=float)
    print("saved", a.out)
    print("\nCheck by hand: 12 random release items and how they were classified")
    rng = np.random.default_rng(a.seed)
    items = [(r.repo, line.strip()[:110]) for r in R.itertuples() for line in (r.body or "").splitlines() if BULLET.match(line)]
    for i in rng.choice(len(items), min(12, len(items)), replace=False) if items else []:
        repo, t = items[i]
        print(f"  [{'FIX' if FIXWORD.search(t) else '   '}] {repo}: {t}")


if __name__ == "__main__":
    main()
