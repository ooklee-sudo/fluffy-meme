"""Preregistered analyses for Study 2 (see ../study2_preregistration_submitted.md).

  pip install numpy pandas scipy statsmodels
  python quant_cost/webapp/analysis_study2.py --csv ~/study2_main_data/main_wide.csv --out report.txt

Input: the wide CSV from export_csv.py (all columns, including the exclusion flags). Rows with excluded = 1 are
dropped. Written and checked on simulated data BEFORE it was ever run on the real data (simulate_study2.py).

Implementation choices that the preregistration leaves open (fixed here, before looking at the real data):
  * Mixed-effects logistic regression: random participant intercept, maximum likelihood with 15-point
    Gauss-Hermite quadrature (the same model as lme4::glmer), implemented directly in this file.
  * Covariates for the "with covariates" versions: numeracy, mean privacy concern (PC1-PC4), risk attitude (R1),
    personal discretion (P2).
  * H3b (the format is manipulated within persons): within-person mediation (Montoya and Hayes, 2017). Per
    participant, difference scores (accuracy plus cost minus accuracy only) of perceived quality disadvantage and of
    local choice; indirect effect = mean difference in the mediator times the slope of the outcome difference on the
    mediator difference; participant-level percentile bootstrap, 5,000 resamples.
  * Ranking item: "top three" means the security and privacy policy factor (item 3) is among the three chosen.
"""
import argparse
import math
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats, optimize
from statsmodels.tools.numdiff import approx_hess

CELLS = ["C1", "C2", "C3", "C4"]
OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    OUT.append(s)
    print(s)


def p_str(p):
    return "< .001" if p < 0.001 else f"{p:.3f}"


# ---------------------------------------------------------------- data
def load(path):
    df = pd.read_csv(path)
    say(f"rows in file: {len(df)}")
    df = df[(df["completed"] == True) & (df["eligible"] == True)]  # noqa: E712
    say(f"completed and eligible: {len(df)}")
    for k, lab in [("ex_attention", "failed an attention check"), ("ex_comprehension", "wrong on >= 2 comprehension checks"),
                   ("ex_c1", "job function group or level differs (C1)"), ("ex_speed", "finished in under 1/3 of the median time"),
                   ("ex_straightline", "identical WTP and choices in all four scenarios")]:
        say(f"  excluded by rule, {lab}: {int(df[k].sum())}")
    say(f"  excluded by any rule: {int(df['excluded'].sum())}")
    df = df[df["excluded"] == 0].copy()
    say(f"ANALYSABLE: {len(df)}  (incident {int((df.incident == 1).sum())}, neutral {int((df.incident == 0).sum())})")
    df["pc"] = df[["PC1", "PC2", "PC3", "PC4"]].mean(axis=1)
    df["top3sec"] = ((df[["P3_1", "P3_2", "P3_3"]] == 3).any(axis=1)).astype(int)
    return df.reset_index(drop=True)


def long_format(df):
    rows = []
    for _, r in df.iterrows():
        for c in CELLS:
            if pd.isna(r.get(f"lam_{c}")):
                continue
            rows.append(dict(pid=r["pid"], incident=r["incident"], lam6=int(r[f"lam_{c}"] == 6),
                             cost_shown=int(r[f"perf_{c}"] == 2), pos=int(r[f"pos_{c}"]), case=r[f"case_{c}"],
                             lnw=r[f"lnWTPL_{c}"], local=int(r[f"local_{c}"]), q5=r[f"Q5_{c}"], excess=r[f"excess_{c}"],
                             numeracy=r["numeracy"], pc=r["pc"], R1=r["R1"], P2=r["P2"], S8=r["S8"]))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- helpers
def welch(x, y, label):
    x, y = np.asarray(x, float), np.asarray(y, float)
    t, p = stats.ttest_ind(x, y, equal_var=False)
    n1, n2 = len(x), len(y)
    sp = math.sqrt(((n1 - 1) * x.var(ddof=1) + (n2 - 1) * y.var(ddof=1)) / (n1 + n2 - 2))
    d = (x.mean() - y.mean()) / sp
    se = math.sqrt((n1 + n2) / (n1 * n2) + d * d / (2 * (n1 + n2)))
    say(f"{label}: mean {x.mean():.3f} (n={n1}) vs {y.mean():.3f} (n={n2}); Welch t = {t:.2f}, p = {p_str(p)}; "
        f"d = {d:.2f}, 95% CI [{d - 1.96 * se:.2f}, {d + 1.96 * se:.2f}]")
    return p, d


def glmm_logit(y, X, groups, nq=15):
    """Random-intercept logistic regression by maximum likelihood (Gauss-Hermite). X is a DataFrame."""
    names = list(X.columns)
    Xm, y = X.values.astype(float), np.asarray(y, float)
    ids, inv = np.unique(groups, return_inverse=True)
    nodes, w = np.polynomial.hermite_e.hermegauss(nq)
    w = w / math.sqrt(2 * math.pi)
    k = Xm.shape[1]

    def nll(p):
        eta = Xm @ p[:k]
        e = eta[:, None] + math.exp(p[k]) * nodes[None, :]
        ll = y[:, None] * e - np.logaddexp(0, e)
        s = np.zeros((len(ids), nq))
        np.add.at(s, inv, ll)
        m = s.max(axis=1, keepdims=True)
        lg = m[:, 0] + np.log((np.exp(s - m) * w[None, :]).sum(axis=1))
        return -lg.sum()

    try:
        b0 = sm.Logit(y, Xm).fit(disp=0).params
    except Exception:
        b0 = np.zeros(k)
    res = optimize.minimize(nll, np.r_[b0, 0.0], method="BFGS")
    H = approx_hess(res.x, nll)
    cov = np.linalg.pinv(H)
    se = np.sqrt(np.clip(np.diag(cov), 0, None))
    z = res.x / se
    pv = 2 * (1 - stats.norm.cdf(np.abs(z)))
    out = pd.DataFrame({"coef": res.x[:k], "se": se[:k], "z": z[:k], "p": pv[:k]}, index=names)
    return out, math.exp(res.x[k]), -res.fun


def design(formula, d):
    import patsy
    return patsy.dmatrix(formula, d, return_type="dataframe")


def report_glmm(L, formula, key, label):
    d = L.dropna(subset=["local"]).copy()
    X = design(formula, d)
    tab, sd, ll = glmm_logit(d["local"].values, X, d["pid"].values)
    r = tab.loc[key]
    say(f"{label}: coefficient {key} = {r.coef:.3f} (SE {r.se:.3f}), z = {r.z:.2f}, p = {p_str(r.p)}; "
        f"odds ratio {math.exp(r.coef):.2f}; random-intercept SD {sd:.2f}")
    return r.p, r.coef


def holm(ps):
    order = np.argsort(ps)
    m, adj, run = len(ps), [None] * len(ps), 0.0
    for rank, i in enumerate(order):
        run = max(run, (m - rank) * ps[i])
        adj[i] = min(1.0, run)
    return adj


def boot_ci(fn, data, B=5000, seed=1):
    rng = np.random.default_rng(seed)
    n = len(data)
    est = [fn(data[rng.integers(0, n, n)]) for _ in range(B)]
    return np.percentile(est, [2.5, 97.5])


def ols_slope(x, y):
    X = np.c_[np.ones(len(x)), x]
    return np.linalg.lstsq(X, y, rcond=None)[0]


# ---------------------------------------------------------------- analyses
def core(df, L, tag=""):
    inc, neu = df[df.incident == 1], df[df.incident == 0]
    say(f"\n--- Confirmatory tests{tag} ---")
    pS, dS = welch(inc["S"], neu["S"], "H2c (primary): S, incident vs neutral")
    X = design("incident*lam6 + cost_shown + C(pos) + C(case)", L.dropna(subset=["lnw"]))
    m = sm.MixedLM(L.dropna(subset=["lnw"])["lnw"].values, X, groups=L.dropna(subset=["lnw"])["pid"].values).fit(reml=True)
    say(f"H2c robustness (mixed model, ln(WTP/L)): incident x lambda 6% = {m.params['incident:lam6']:.3f} "
        f"(SE {m.bse['incident:lam6']:.3f}), p = {p_str(m.pvalues['incident:lam6'])}")
    p2a, _ = welch(inc["meanLnWTPL"], neu["meanLnWTPL"], "H2a: mean ln(WTP/L), incident vs neutral")
    p3a, _ = report_glmm(L, "cost_shown + lam6 + incident + C(pos) + C(case)", "cost_shown",
                         "H3a: local choice, format (accuracy plus cost shown vs. accuracy only)")
    adj = holm([p2a, p3a])
    say(f"Holm family (H2a, H3a): adjusted p = {p_str(adj[0])} and {p_str(adj[1])}")
    return pS


def covariate_versions(df, L):
    say("\n--- With covariates (numeracy, privacy concern, risk attitude, discretion) ---")
    d = df.dropna(subset=["S", "numeracy", "pc", "R1", "P2"])
    r = smf.ols("S ~ incident + numeracy + pc + R1 + P2", d).fit()
    say(f"H2c with covariates: incident coefficient on S = {r.params['incident']:.3f} (SE {r.bse['incident']:.3f}), p = {p_str(r.pvalues['incident'])}, n = {len(d)}")
    d = df.dropna(subset=["meanLnWTPL", "numeracy", "pc", "R1", "P2"])
    r = smf.ols("meanLnWTPL ~ incident + numeracy + pc + R1 + P2", d).fit()
    say(f"H2a with covariates: incident coefficient = {r.params['incident']:.3f} (SE {r.bse['incident']:.3f}), p = {p_str(r.pvalues['incident'])}")
    Ld = L.dropna(subset=["numeracy", "pc", "R1", "P2"])
    report_glmm(Ld, "cost_shown + lam6 + incident + numeracy + pc + R1 + P2 + C(pos) + C(case)", "cost_shown",
                "H3a with covariates")


def manipulation_checks(df, L):
    say("\n--- Manipulation checks (reported, not part of the test family) ---")
    report_glmm(L, "cost_shown + lam6 + incident + C(pos) + C(case)", "lam6", "local choice higher at lambda 6% than 2%")
    welch(df.loc[df.incident == 1, "GP"], df.loc[df.incident == 0, "GP"], "general 12-month exposure estimate (GP), incident vs neutral")


def mediation(df, L):
    say("\n--- Planned mediation (not interpreted confirmatorily) ---")
    d = df.copy()
    d["mex"] = d[[f"excess_{c}" for c in CELLS]].mean(axis=1)
    arr = d[["incident", "mex", "meanLnWTPL"]].dropna().values

    def ind(a):
        x, m, y = a[:, 0], a[:, 1], a[:, 2]
        a_ = ols_slope(x, m)[1]
        b_ = np.linalg.lstsq(np.c_[np.ones(len(x)), x, m], y, rcond=None)[0][2]
        return a_ * b_
    est = ind(arr)
    lo, hi = boot_ci(ind, arr)
    say(f"H2b: indirect effect of incident on mean ln(WTP/L) via mean excess probability = {est:.4f}, 95% bootstrap CI [{lo:.4f}, {hi:.4f}]")

    rows = []
    for pid, g in L.dropna(subset=["q5"]).groupby("pid"):
        a, b = g[g.cost_shown == 1], g[g.cost_shown == 0]
        if len(a) and len(b):
            rows.append([a["q5"].mean() - b["q5"].mean(), a["local"].mean() - b["local"].mean()])
    arr = np.array(rows)

    def ind2(a):
        dm, dy = a[:, 0], a[:, 1]
        slope = ols_slope(dm - dm.mean(), dy)[1]
        return dm.mean() * slope
    est = ind2(arr)
    lo, hi = boot_ci(ind2, arr)
    say(f"H3b: within-person indirect effect of format on local choice via perceived quality disadvantage = {est:.4f}, "
        f"95% bootstrap CI [{lo:.4f}, {hi:.4f}] (n = {len(arr)})")


def exploratory(df, L):
    say("\n--- Exploratory (labelled as such) ---")
    d = df.copy()
    d["strict"] = d["S8"].map({3: 0, 4: 0, 2: 1, 1: 2})
    dd = d.dropna(subset=["strict"])
    for dv in ["S", "meanLnWTPL"]:
        r = smf.ols(f"{dv} ~ incident*strict", dd).fit()
        say(f"H5, policy strictness: {dv} ~ incident x strictness: interaction = {r.params['incident:strict']:.3f} "
            f"(SE {r.bse['incident:strict']:.3f}), p = {p_str(r.pvalues['incident:strict'])}, n = {len(dd)}")
    d["P2z"] = (d["P2"] - d["P2"].mean()) / d["P2"].std(ddof=1)
    for dv in ["S", "meanLnWTPL"]:
        r = smf.ols(f"{dv} ~ incident*P2z", d.dropna(subset=["P2z", dv])).fit()
        say(f"H5, discretion: {dv} ~ incident x discretion (z): interaction = {r.params['incident:P2z']:.3f} "
            f"(SE {r.bse['incident:P2z']:.3f}), p = {p_str(r.pvalues['incident:P2z'])}")
    r = smf.logit("top3sec ~ incident", d).fit(disp=0)
    say(f"H2d: security and privacy policy ranked in the top three ~ incident: coefficient = {r.params['incident']:.3f}, "
        f"p = {p_str(r.pvalues['incident'])}; shares {d.loc[d.incident == 1, 'top3sec'].mean():.2f} vs {d.loc[d.incident == 0, 'top3sec'].mean():.2f}")
    report_glmm(L, "cost_shown*incident + lam6 + C(pos) + C(case)", "cost_shown:incident", "incident x format interaction (local choice)")
    L2 = L.assign(numz=(L["numeracy"] - L["numeracy"].mean()) / L["numeracy"].std(ddof=1))
    report_glmm(L2, "cost_shown*numz + lam6 + incident + C(pos) + C(case)", "cost_shown:numz", "format x numeracy (local choice)")


def prohibited(df):
    say("\n--- Respondents whose organization prohibits external AI services (S8 = 1) ---")
    g = df[df.S8 == 1]
    say(f"n = {len(g)}; share choosing the local model = {g['n_local'].mean() / 4:.2f}; mean ln(WTP/L) = {g['meanLnWTPL'].mean():.3f}; S = {g['S'].mean():.3f}"
        + ("  (descriptive only, n < 20)" if len(g) < 20 else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    np.random.seed(1)
    df = load(a.csv)
    L = long_format(df)
    core(df, L)
    covariate_versions(df, L)
    manipulation_checks(df, L)
    mediation(df, L)
    exploratory(df, L)
    prohibited(df)
    say("\n--- Sensitivity: excluding S8 = 1 ---")
    keep = df[df.S8 != 1].reset_index(drop=True)
    core(keep, long_format(keep), tag=" (S8 = 1 excluded)")
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write("\n".join(OUT) + "\n")
        print("\nreport written to", a.out)


if __name__ == "__main__":
    main()
