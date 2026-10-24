"""Analyse execution results: pass rates, count-model fit, heterogeneity, detection curve S(e) and its tail index k.

Defect proxy: distinct failure signatures per sample. Detection: tests are run in uniformly random order, so a defect that
fails f of M tests is still undetected after e tests with probability C(M-f, e) / C(M, e).
"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd
from scipy.optimize import least_squares
from scipy.special import gammaln

from analysis import dispersion_tests, fit_models

HERE = pathlib.Path(__file__).parent
RES = HERE / "data" / "results.jsonl"


def load(path=RES):
    rows = [json.loads(l) for l in open(path)]
    df = pd.DataFrame(rows)
    df["y"] = df.fails.map(len)
    df["passed"] = df.y == 0
    df["has_timeout"] = df.fails.map(lambda d: any(k.startswith("TIMEOUT") or k == "PARENT_TIMEOUT" for k in d))
    df["load_err"] = df.fails.map(lambda d: any(k.startswith("LOAD") or k.startswith("HARNESS") for k in d))
    return df


def log_comb(n, k):
    return gammaln(n + 1) - gammaln(k + 1) - gammaln(n - k + 1)


def survival_curve(df, fractions):
    """Mean P(defect undetected) at effort u = e/M for each u, over all (sample, signature) defects."""
    recs = [(r.n, len(ix)) for r in df.itertuples() for ix in r.fails.values()]
    if not recs:
        return None, 0
    M = np.array([m for m, _ in recs], float)
    f = np.array([k for _, k in recs], float)
    out = []
    for u in fractions:
        e = np.maximum(1, np.round(u * M)).astype(float)
        ok = (M - f) >= e
        lp = np.where(ok, log_comb(M - f, np.minimum(e, M - f)) - log_comb(M, e), -np.inf)
        out.append(np.exp(lp).mean())
    return np.array(out), len(recs)


def fit_tail(u, S):
    """Fit S(u)=exp(-t u) (exponential) and S(u)=(1+t u/k)^-k (heavy tail) on the log scale."""
    ok = S > 1e-6
    u, y = u[ok], np.log(S[ok])
    exp_fit = least_squares(lambda p: -p[0] * u - y, [10.0], bounds=(1e-6, 1e6))
    heavy = least_squares(lambda p: -p[1] * np.log1p(p[0] * u / p[1]) - y, [10.0, 1.0],
                          bounds=([1e-6, 0.02], [1e6, 200]))
    return {"exp_theta": exp_fit.x[0], "exp_sse": 2 * exp_fit.cost,
            "heavy_theta": heavy.x[0], "heavy_k": heavy.x[1], "heavy_sse": 2 * heavy.cost}


def main(path=RES):
    df = load(path)
    print(f"{len(df):,} samples, {df.task_id.nunique()} tasks, {df.model.nunique()} models\n")
    g = df.groupby("model")
    tab = pd.DataFrame({"n": g.size(), "pass": g.passed.mean(), "mean_y": g.y.mean(), "var_y": g.y.var(),
                        "timeout": g.has_timeout.mean(), "load_err": g.load_err.mean(), "cost$": g.cost.mean()})
    tab["var/mean"] = tab.var_y / tab.mean_y
    print("1) Per model (y = failure signatures per sample):")
    print(tab.sort_values("pass").round(4).to_string())

    print("\n2) Count-model fit, sample level (ignores task effect):")
    for name, sub in [("ALL", df)] + [(m.split("/")[-1], d) for m, d in df.groupby("model")]:
        y = sub.y.values
        if y.sum() < 20:
            print(f"  {name:32s} too few defects"); continue
        d = dispersion_tests(y)
        best = fit_models(y).iloc[0]
        print(f"  {name:32s} pearson={d['pearson_ratio']:.2f}  CT p={d['ct_p_one_sided']:.3g}  AIC best={best['model']}")

    print("\n3) Task heterogeneity: dispersion after removing (model, task) cell means")
    cell = df.groupby(["model", "task_id"]).y
    mu = cell.transform("mean")
    cnt = cell.transform("size")
    keep = (mu > 0) & (cnt > 1)
    ss = (((df.y - mu) ** 2)[keep] / mu[keep]).sum()
    dof = keep.sum() - df[keep].groupby(["model", "task_id"]).ngroups
    print(f"  within-cell Pearson dispersion (cells with mean>0) = {ss / dof:.3f}   (1 = Poisson)")
    cm = df.groupby(["model", "task_id"]).y.agg(["mean", "size"])
    for m, d in cm.groupby(level=0):
        z = d["mean"].values
        print(f"  {m.split('/')[-1]:32s} task-mean: mean={z.mean():.3f}  var={z.var():.3f}  "
              f"share of tasks never failing={(z == 0).mean():.2f}  tasks failing every sample={(d['mean'] >= 1).mean():.2f}")

    print("\n4) Detection curve S(u), u = fraction of tests executed (random order):")
    fr = np.array([0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5, 0.8, 1.0])
    S, nd = survival_curve(df, fr)
    if S is None:
        print("  no defects"); return
    print("  defects (sample x signature):", f"{nd:,}")
    print("  " + "  ".join(f"u={u:g}:{s:.3f}" for u, s in zip(fr, S)))
    ft = fit_tail(fr, S)
    print(f"  exponential: theta={ft['exp_theta']:.2f}  SSE={ft['exp_sse']:.4f}")
    print(f"  heavy tail:  theta={ft['heavy_theta']:.2f}  k={ft['heavy_k']:.3f}  SSE={ft['heavy_sse']:.4f}")
    print(f"  => theory (linear cost): eps = 1/(1+k) = {1 / (1 + ft['heavy_k']):.3f}")
    fm = np.array([len(ix) / r.n for r in df.itertuples() for ix in r.fails.values()])
    print("  failing-share f/M per defect: quantiles 10/25/50/75/90% =", np.round(np.quantile(fm, [.1, .25, .5, .75, .9]), 4))

    print("\n5) Detection curve by model (heavy-tail k):")
    for m, d in df.groupby("model"):
        s, n_def = survival_curve(d, fr)
        if s is None or n_def < 50:
            continue
        t = fit_tail(fr, s)
        print(f"  {m.split('/')[-1]:32s} defects={n_def:6,}  k={t['heavy_k']:.3f}  1/(1+k)={1 / (1 + t['heavy_k']):.3f}  S(0.01)={s[3]:.3f}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else RES)
