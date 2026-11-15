"""Supplementary estimates added to calibration_results.json:

* Cameron-Trivedi (1990) overdispersion test (corrected implementation): regress
  ((y - mu)^2 - y)/mu on mu with no intercept, mu = fitted Poisson mean. Reported for
  the pooled constant-mean model and for a model-by-task mean model.
* Lower-tail index from the log-log slope of the survival curve. By Proposition 2(c),
  S(u) ~ C u^{-k} at high effort when G(rho) ~ rho^k near zero; the slope over
  u in [0.01, 0.1] estimates -k (task bootstrap). The Hill estimator is unreliable here
  because the smallest failure shares tie at f = 1.
* eta: main panel excludes Qwen 2.5 Coder 32B (systematic syntax errors from the served
  endpoint); robustness: all 26 models; excluding load errors; core panel only.

usage: python3 -I analyze_extra.py TASKS RESULTS RESULTS_JSON
"""
import json
import os
import sys

import numpy as np
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze as A  # noqa: E402

tasks_p, res_p, out_p = sys.argv[1:4]
R = json.load(open(out_p))
core = set(R["core_models"])
tasks, sols_all = A.load(tasks_p, res_p, None)
sols = [s for s in sols_all if s["model"] in core]

# Cameron-Trivedi -------------------------------------------------------------------
def ct(y, mu):
    z = ((y - mu) ** 2 - y) / mu
    x = mu
    a = np.sum(z * x) / np.sum(x * x)
    e = z - a * x
    se = np.sqrt(np.sum(e ** 2) / (len(y) - 1) / np.sum(x * x))
    return float(a), float(a / se), float(stats.norm.sf(a / se))

y = np.array([len(s["fails"]) for s in sols], float)
mu_pool = np.full_like(y, y.mean())
cell = {}
for s in sols:
    cell.setdefault((s["model"], s["task_id"]), []).append(len(s["fails"]))
cm = {k: np.mean(v) for k, v in cell.items()}
mu_cell = np.array([cm[(s["model"], s["task_id"])] for s in sols])
keep = mu_cell > 0
R["overdispersion"]["ct_pooled"] = dict(zip(("alpha", "t", "p"), ct(y, mu_pool)))
R["overdispersion"]["ct_cell"] = dict(zip(("alpha", "t", "p"), ct(y[keep], mu_cell[keep])))
R["overdispersion"].pop("ct_t", None); R["overdispersion"].pop("ct_p", None)

# Tail slope ---------------------------------------------------------------------------
dfs = A.defects(sols, "baseline")
f = np.array([d[3] for d in dfs]); M = np.array([d[4] for d in dfs])
U = np.array([0.01, 0.02, 0.05, 0.1])
S = A.surv_random(f, M, U)
tids, Ats, n = A.task_sums(dfs, S)
lu = np.log(U)

def slope(Sv):
    return float(-np.polyfit(lu, np.log(Sv), 1)[0])

est = slope(Ats.sum(0) / n.sum())
T = len(n)
bs = []
for _ in range(1000):
    w = A.rng.multinomial(T, np.ones(T) / T)
    bs.append(slope((w[:, None] * Ats).sum(0) / (w * n).sum()))
R["tail_slope"] = dict(u=U.tolist(), k=est, ci=[float(x) for x in np.quantile(bs, [0.025, 0.975])],
                       eps=1 / (1 + est), eps_ci=[1 / (1 + float(x)) for x in np.quantile(bs, [0.975, 0.025])])
R.pop("hill", None)

# eta variants ----------------------------------------------------------------------------
EXCL = "qwen/qwen-2.5-coder-32b-instruct"
lam = {m: R["table1"][m]["defects_per_sample"] for m in R["table1"]}
all_dfs = A.defects(sols_all, "baseline")
sig_of = {}
for s in sols_all:
    for sig, idx in s["fails"].items():
        sig_of[(s["model"], s["task_id"], s["sample"], len(idx))] = sig
main = [d for d in all_dfs if d[0] != EXCL]
lam_main = {m: v for m, v in lam.items() if m != EXCL}
no_load = [d for d in main if not sig_of.get((d[0], d[1], d[2], d[3]), "").startswith(("LOAD", "KILLED", "CRASH"))]
R["eta_main"] = A.eta_regression(main, lam_main, B=1000)
R["eta_robust"] = {
    "all_26_models": {k: v for k, v in A.eta_regression(all_dfs, lam, B=500).items() if k != "per_model"},
    "excluding_load_errors": {k: v for k, v in A.eta_regression(no_load, lam_main, B=500).items() if k != "per_model"},
    "core_panel": {k: v for k, v in R["eta_core"].items() if k != "per_model"},
}
R["eta_excluded_model"] = EXCL
json.dump(R, open(out_p, "w"), indent=1)
print(json.dumps({"overdispersion": R["overdispersion"], "tail_slope": R["tail_slope"],
                  "eta_main": {k: v for k, v in R["eta_main"].items() if k != "per_model"},
                  "eta_robust": R["eta_robust"]}, indent=1))
