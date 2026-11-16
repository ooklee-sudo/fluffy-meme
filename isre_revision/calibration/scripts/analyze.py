"""Calibration analysis for Section 6 of the manuscript.

Reads harness output (failure signatures with failing input indices) and produces every
number reported in Section 6 and Sections EC.4-EC.5:

  Table 1   pass rate and defects per sample by model
  Sec 6.3   gamma vs exponential fits to the survival curve, k with task-bootstrap CI,
            descriptive statistics of f/M, overdispersion tests
  Table 2   nonparametric survivor-CV estimates eps_hat(u), Hill estimates of lower-tail k
  Table 3   sensitivity of k to defect definition and test order
  Table EC.4 per-model k with bootstrap CI and mean detectability
  Sec 6.4   eta: elasticity of detectability with respect to defect intensity

usage: python3 -I analyze.py TASKS_JSON RESULTS_JSONL.gz OUT_DIR --core MODEL ... [--all]
"""
import argparse
import gzip
import json
import pickle as _pickle


def load_tasks(path):
    if path.endswith('.pkl'):
        return _pickle.load(open(path, 'rb'))
    return json.load(open(path))
import math
import os
from collections import defaultdict

import numpy as np
from scipy import optimize, special, stats

rng = np.random.default_rng(20261115)
U_GRID = np.array([0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 0.8])
U_NP = np.array([0.01, 0.05, 0.25, 1.0])


# ----------------------------------------------------------------------------- loading
def load(tasks_path, results_path, models):
    tasks = {t["task_id"]: t for t in load_tasks(tasks_path)}
    sols = []
    seen = set()
    with gzip.open(results_path, "rt") as f:
        for line in f:
            r = json.loads(line)
            key = (r["model"], r["task_id"], r["sample"])
            if key in seen or (models and r["model"] not in models):
                continue
            seen.add(key)
            sols.append(r)
    return tasks, sols


def input_orders(tasks):
    """Rank of each input under the dataset, short-first and long-first orders."""
    orders = {}
    for tid, t in tasks.items():
        L = np.array([len(repr(x)) for x in t["inputs"]])
        M = len(L)
        ds = np.arange(M)
        short = np.empty(M, int); short[np.argsort(L, kind="stable")] = np.arange(M)
        long_ = np.empty(M, int); long_[np.argsort(-L, kind="stable")] = np.arange(M)
        orders[tid] = dict(dataset=ds, short=short, long=long_)
    return orders


def defects(sols, variant="baseline"):
    """List of (model, task, sample, f, M, failing_idx) under a defect definition."""
    out = []
    for s in sols:
        fails = s["fails"]
        if not fails:
            continue
        M = s["M"]
        if variant == "whole":
            idx = sorted(set(i for v in fails.values() for i in v))
            out.append((s["model"], s["task_id"], s["sample"], len(idx), M, idx))
            continue
        if variant == "drop_timeout_load" and any(k.startswith(("TIMEOUT", "LOAD", "KILLED", "CRASH")) for k in fails):
            continue
        for sig, idx in fails.items():
            f = len(idx)
            if variant == "subtle" and (f / M >= 0.5 or sig.startswith(("LOAD", "KILLED", "CRASH"))):
                continue
            out.append((s["model"], s["task_id"], s["sample"], f, M, idx))
    return out


# ----------------------------------------------------------------------------- survival
def surv_random(f, M, u):
    """P(defect undetected after e = u*M tests in random order) = C(M-f,e)/C(M,e), real e."""
    f, M = np.asarray(f, float), np.asarray(M, float)
    e = np.multiply.outer(u, M)                       # (len(u), n)
    ok = (M - f - e) > -1 + 1e-12
    with np.errstate(invalid="ignore"):
        val = (special.gammaln(M - f + 1) + special.gammaln(M - e + 1)
               - special.gammaln(np.where(ok, M - f - e + 1, 1.0)) - special.gammaln(M + 1))
    return np.where(ok, np.exp(val), 0.0)


def surv_order(first_rank, M, u):
    """Fixed order: undetected after e tests iff first failing rank >= e."""
    e = np.multiply.outer(u, np.asarray(M, float))
    return (np.asarray(first_rank, float)[None, :] >= np.ceil(e - 1e-9)).astype(float)


def task_sums(dfs, S):
    """Aggregate survival per task for fast task bootstrap: A[t,u] and n[t]."""
    tids = sorted(set(d[1] for d in dfs))
    pos = {t: i for i, t in enumerate(tids)}
    A = np.zeros((len(tids), S.shape[0]))
    n = np.zeros(len(tids))
    ti = np.array([pos[d[1]] for d in dfs])
    np.add.at(n, ti, 1)
    for j in range(S.shape[0]):
        np.add.at(A[:, j], ti, S[j])
    return tids, A, n


def fit_curves(Sobs, u=U_GRID, x0=None):
    y = np.log(np.clip(Sobs, 1e-12, None))

    def sse_gamma(p):
        th, k = np.exp(p)
        return np.sum((y + k * np.log1p(th * u / k)) ** 2)

    def sse_exp(p):
        return np.sum((y + np.exp(p[0]) * u) ** 2)

    best = None
    starts = [x0] if x0 is not None else [np.log([th0, k0]) for k0 in (0.3, 0.6, 1.0, 2.0)
                                          for th0 in (3.0, 10.0, 30.0, 100.0)]
    for st in starts:
        if True:
            r = optimize.minimize(sse_gamma, st, method="Nelder-Mead",
                                  options=dict(xatol=1e-9, fatol=1e-12, maxiter=4000))
            if best is None or r.fun < best.fun:
                best = r
    th, k = np.exp(best.x)
    re = optimize.minimize(sse_exp, [np.log(5.0)], method="Nelder-Mead")
    return dict(k=float(k), theta=float(th), sse_gamma=float(best.fun),
                theta_exp=float(np.exp(re.x[0])), sse_exp=float(re.fun))


def k_with_ci(A, n, B):
    est = fit_curves(A.sum(0) / n.sum())
    T = len(n)
    ks = []
    for _ in range(B):
        w = rng.multinomial(T, np.ones(T) / T)
        Sb = (w[:, None] * A).sum(0) / (w * n).sum()
        ks.append(fit_curves(Sb, x0=np.log([est["theta"], est["k"]]))["k"])
    lo, hi = np.quantile(ks, [0.025, 0.975])
    eps = 1 / (1 + np.array(ks))
    return est, (float(lo), float(hi)), tuple(float(x) for x in np.quantile(eps, [0.025, 0.975]))


# ----------------------------------------------------------------------------- nonparametric
def rho_hat(f, M):
    f, M = np.asarray(f, float), np.asarray(M, float)
    with np.errstate(divide="ignore"):
        return np.where(f < M, -M * np.log1p(-f / M), np.inf)


def np_eps(dfs, B):
    """Survivor CV^2 and eps_hat(u) with task bootstrap."""
    f = np.array([d[3] for d in dfs]); M = np.array([d[4] for d in dfs])
    r = rho_hat(f, M)
    fin = np.isfinite(r)
    tids = sorted(set(d[1] for d in dfs)); pos = {t: i for i, t in enumerate(tids)}
    ti = np.array([pos[d[1]] for d in dfs])
    T = len(tids)
    sums = np.zeros((len(U_NP), T, 3))
    for a, u in enumerate(U_NP):
        w = np.where(fin, np.exp(-np.where(fin, r, 0) * u), 0.0)
        rr = np.where(fin, r, 0.0)
        for c, val in enumerate((w, w * rr, w * rr * rr)):
            np.add.at(sums[a, :, c], ti, val)

    def cv2(S):
        m0, m1, m2 = S[..., 0], S[..., 1], S[..., 2]
        mean = m1 / m0
        var = m2 / m0 - mean ** 2
        return var / mean ** 2

    est = cv2(sums.sum(1))
    boots = []
    for _ in range(B):
        w = rng.multinomial(T, np.ones(T) / T)
        boots.append(cv2((sums * w[None, :, None]).sum(1)))
    boots = np.array(boots)
    eps = est / (1 + est)
    eps_b = boots / (1 + boots)
    return [dict(u=float(u), cv2=float(est[a]), eps=float(eps[a]),
                 eps_ci=tuple(float(x) for x in np.quantile(eps_b[:, a], [0.025, 0.975])),
                 cv2_ci=tuple(float(x) for x in np.quantile(boots[:, a], [0.025, 0.975])))
            for a, u in enumerate(U_NP)]


def hill_lower(dfs, fracs=(0.025, 0.05, 0.10), B=300):
    """Hill estimator of the lower-tail index k of p = f/M (P(p <= x) ~ x^k near 0)."""
    p = np.array([d[3] / d[4] for d in dfs])
    tids = np.array([d[1] for d in dfs])
    utid = np.unique(tids)
    idx_by_t = {t: np.where(tids == t)[0] for t in utid}

    def hill(pp, m):
        s = np.sort(pp)
        m = max(5, min(m, len(s) - 1))
        return 1.0 / np.mean(np.log(s[m] / s[:m]))

    out = []
    for fr in fracs:
        m = int(fr * len(p))
        est = hill(p, m)
        bs = []
        for _ in range(B):
            pick = rng.choice(utid, len(utid))
            ii = np.concatenate([idx_by_t[t] for t in pick])
            bs.append(hill(p[ii], int(fr * len(ii))))
        out.append(dict(frac=fr, m=m, k=float(est), ci=tuple(float(x) for x in np.quantile(bs, [0.025, 0.975]))))
    return out


# ----------------------------------------------------------------------------- eta
def eta_regression(dfs, lam_by_model, B=400):
    """ln rho_hat_j = alpha_task + eta * ln lambda_model; f = M continuity-corrected to M - 0.5."""
    f = np.array([d[3] for d in dfs], float); M = np.array([d[4] for d in dfs], float)
    f = np.where(f >= M, M - 0.5, f)
    y = np.log(-M * np.log1p(-f / M))
    x = np.log(np.array([lam_by_model[d[0]] for d in dfs]))
    tids = np.array([d[1] for d in dfs])
    ut, ti = np.unique(tids, return_inverse=True)

    def fe_slope(yv, xv, tv):
        nT = tv.max() + 1
        cnt = np.bincount(tv, minlength=nT)
        ym = np.bincount(tv, yv, nT) / np.maximum(cnt, 1)
        xm = np.bincount(tv, xv, nT) / np.maximum(cnt, 1)
        yd, xd = yv - ym[tv], xv - xm[tv]
        return float((xd @ yd) / (xd @ xd))

    est = fe_slope(y, x, ti)
    idx_by_t = [np.where(ti == t)[0] for t in range(len(ut))]
    bs = []
    for _ in range(B):
        pick = rng.integers(0, len(ut), len(ut))
        ii = np.concatenate([idx_by_t[t] for t in pick])
        # relabel tasks so duplicated tasks are distinct fixed effects
        lab = np.concatenate([np.full(len(idx_by_t[t]), j) for j, t in enumerate(pick)])
        bs.append(fe_slope(y[ii], x[ii], lab))
    # model-level means of task-demeaned ln rho, for the scatter plot
    nT = len(ut)
    cnt = np.bincount(ti, minlength=nT)
    ym = np.bincount(ti, y, nT) / cnt
    resid = y - ym[ti]
    models = sorted(lam_by_model)
    mdl = np.array([d[0] for d in dfs])
    per_model = {m: dict(lam=lam_by_model[m], ln_theta_dm=float(resid[mdl == m].mean()) if (mdl == m).any() else None,
                         n=int((mdl == m).sum())) for m in models}
    return dict(eta=est, ci=tuple(float(v) for v in np.quantile(bs, [0.025, 0.975])),
                se=float(np.std(bs)), n_defects=len(dfs), per_model=per_model)


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tasks"); ap.add_argument("results"); ap.add_argument("out")
    ap.add_argument("--core", nargs="+", required=True)
    ap.add_argument("--boot", type=int, default=300)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    tasks, sols_all = load(args.tasks, args.results, None)
    core = set(args.core)
    sols = [s for s in sols_all if s["model"] in core]
    orders = input_orders(tasks)
    R = {}

    # Table 1 ---------------------------------------------------------------
    by_model = defaultdict(list)
    for s in sols_all:
        by_model[s["model"]].append(s)
    t1 = {}
    for m, ss in by_model.items():
        nd = [len(s["fails"]) for s in ss]
        t1[m] = dict(samples=len(ss), pass_rate=float(np.mean([n == 0 for n in nd])),
                     defects_per_sample=float(np.mean(nd)), defects=int(np.sum(nd)))
    R["table1"] = t1

    # Baseline fit ----------------------------------------------------------
    dfs = defects(sols, "baseline")
    f = np.array([d[3] for d in dfs]); M = np.array([d[4] for d in dfs])
    S = surv_random(f, M, U_GRID)
    tids, A, n = task_sums(dfs, S)
    est, kci, eci = k_with_ci(A, n, args.boot)
    R["baseline"] = dict(n_defects=len(dfs), n_solutions=len(sols), n_tasks=len(tids), **est,
                         k_ci=kci, eps=1 / (1 + est["k"]), eps_ci=eci,
                         offset=est["k"] / (1 + est["k"]),
                         offset_ci=(1 - eci[1], 1 - eci[0]),
                         S_obs=dict(zip(map(float, U_GRID), map(float, A.sum(0) / n.sum()))))
    p = f / M
    R["fm_stats"] = dict(median=float(np.median(p)), q25=float(np.quantile(p, .25)), q75=float(np.quantile(p, .75)),
                         share_ge_085=float(np.mean(p >= 0.85)), share_lt_0005=float(np.mean(p < 0.005)),
                         share_eq_1=float(np.mean(p >= 1)))

    # Overdispersion ----------------------------------------------------------
    y = np.array([len(s["fails"]) for s in sols], float)
    mu = y.mean()
    pearson_pooled = float(np.sum((y - mu) ** 2 / mu) / (len(y) - 1))
    # Cameron-Trivedi (1990) auxiliary regression for NB2 alternative, no-covariate model
    z = ((y - mu) ** 2 - y) / (mu * np.sqrt(2))
    xx = mu / np.sqrt(2)
    alpha = np.sum(z * xx) / np.sum(xx * xx)
    resid = z - alpha * xx
    se = np.sqrt(np.sum(resid ** 2) / (len(y) - 1) / np.sum(xx * xx))
    ct_t = float(alpha / se)
    cells = defaultdict(list)
    for s in sols:
        cells[(s["model"], s["task_id"])].append(len(s["fails"]))
    num = den = 0.0
    for v in cells.values():
        v = np.array(v, float); m_ = v.mean()
        if m_ > 0:
            num += np.sum((v - m_) ** 2 / m_); den += len(v) - 1
    R["overdispersion"] = dict(pearson_pooled=pearson_pooled, ct_t=ct_t,
                               ct_p=float(stats.norm.sf(ct_t)), pearson_within=float(num / den))

    # Nonparametric and Hill --------------------------------------------------
    R["nonparametric"] = np_eps(dfs, args.boot)
    R["hill"] = hill_lower(dfs, B=args.boot)

    # Sensitivity (Table 3) ----------------------------------------------------
    sens = {}
    for name, variant, order in (("Baseline (random order)", "baseline", None),
                                 ("Whole sample counted as one defect", "whole", None),
                                 ("Subtle defects only (fail < 50% of tests)", "subtle", None),
                                 ("Drop samples with timeouts or load errors", "drop_timeout_load", None),
                                 ("Dataset order", "baseline", "dataset"),
                                 ("Short inputs first", "baseline", "short"),
                                 ("Long inputs first", "baseline", "long")):
        dv = defects(sols, variant)
        fv = np.array([d[3] for d in dv]); Mv = np.array([d[4] for d in dv])
        if order is None:
            Sv = surv_random(fv, Mv, U_GRID)
        else:
            first = np.array([min(orders[d[1]][order][d[5]]) for d in dv])
            Sv = surv_order(first, Mv, U_GRID)
        tv, Av, nv = task_sums(dv, Sv)
        e2, kc2, ec2 = k_with_ci(Av, nv, args.boot)
        sens[name] = dict(defects=len(dv), k=e2["k"], k_ci=kc2, eps=1 / (1 + e2["k"]), eps_ci=ec2,
                          sse_gamma=e2["sse_gamma"], sse_exp=e2["sse_exp"])
    R["sensitivity"] = sens

    # Per-model k (Table EC.4), all models -------------------------------------
    pm = {}
    all_dfs = defects(sols_all, "baseline")
    for m in sorted(by_model):
        dm = [d for d in all_dfs if d[0] == m]
        if len(dm) < 30:
            pm[m] = dict(defects=len(dm), k=None)
            continue
        fm = np.array([d[3] for d in dm]); Mm = np.array([d[4] for d in dm])
        tm, Am, nm = task_sums(dm, surv_random(fm, Mm, U_GRID))
        e3, kc3, ec3 = k_with_ci(Am, nm, 400)
        pm[m] = dict(defects=len(dm), k=e3["k"], k_ci=kc3, eps=1 / (1 + e3["k"]), eps_ci=ec3,
                     median_fm=float(np.median(fm / Mm)))
    R["per_model"] = pm
    lam = {m: t1[m]["defects_per_sample"] for m in t1}
    ks = [(lam[m], pm[m]["k"]) for m in core if pm[m]["k"] is not None]
    rho_s = stats.spearmanr([a for a, _ in ks], [b for _, b in ks]).statistic
    R["rank_corr_core"] = float(rho_s)
    ks_all = [(lam[m], pm[m]["k"]) for m in pm if pm[m]["k"] is not None]
    R["rank_corr_all"] = float(stats.spearmanr([a for a, _ in ks_all], [b for _, b in ks_all]).statistic)

    # eta ------------------------------------------------------------------------
    R["core_models"] = sorted(core)
    R["eta_core"] = eta_regression(dfs, {m: lam[m] for m in core})
    R["eta_all"] = eta_regression(all_dfs, lam)

    json.dump(R, open(os.path.join(args.out, "calibration_results.json"), "w"), indent=1)
    print(json.dumps({k: R[k] for k in ("baseline", "fm_stats", "overdispersion", "nonparametric", "hill")}, indent=1))
    print("sensitivity:", json.dumps({k: (v["defects"], round(v["k"], 3), [round(x, 2) for x in v["k_ci"]],
                                         round(v["eps"], 3)) for k, v in sens.items()}, indent=1))
    print("rank corr core/all:", R["rank_corr_core"], R["rank_corr_all"])
    for key in ("eta_core", "eta_all"):
        e = R[key]
        print(key, round(e["eta"], 3), [round(x, 3) for x in e["ci"]], "n=", e["n_defects"])


if __name__ == "__main__":
    main()
