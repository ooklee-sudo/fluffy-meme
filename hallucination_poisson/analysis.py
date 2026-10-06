"""Cascade evaluation and the multi-objective guardrail-stack optimisation of Section 3.

Every layer is run on every example during `collect`, so any subset/cascade can be evaluated offline
from the per-example flags, without assuming independence between layers."""
import itertools
from dataclasses import dataclass

import numpy as np

from stats_model import capacity

LAYERS = ["L1", "L2", "L3"]


@dataclass
class Weights:
    w_capacity: float = 1.0   # per unit of k*  (events/day of on-call capacity)
    w_latency: float = 0.02   # per ms of added latency
    w_sysfail: float = 1.0    # per daily system-failure event
    w_fp: float = 0.0         # per daily false block (not in the paper; 0 = ignore)


def load_arrays(records):
    """records -> dict of numpy arrays used by every function below."""
    n = len(records)
    a = {"hallu": np.array([r["hallucinated"] for r in records], bool)}
    for L in LAYERS:
        a[f"{L}_flag"] = np.array([r[L]["flag"] for r in records], bool)
        a[f"{L}_lat"] = np.array([r[L]["latency_ms"] for r in records], float)
        a[f"{L}_err"] = np.array([bool(r[L]["error"]) for r in records], bool)
    a["abstain"] = np.array([r["abstained"] for r in records], bool)
    a["p_entail"] = np.array([np.nan if r["L2"]["score"] is None else r["L2"]["score"] for r in records], float)
    # abstentions bypass the guardrails (nothing to verify): never blocked, no latency
    for L in LAYERS:
        a[f"{L}_flag"] &= ~a["abstain"]
        a[f"{L}_lat"] = np.where(a["abstain"], 0.0, a[f"{L}_lat"])
    a["n"] = n
    return a


def evaluate_cascade(a, layers, route_thr=0.9, timeout_ms=2000.0, route=True):
    """Run the examples through `layers` (ordered subset of L1,L2,L3) with short-circuit on block.
    The judge (L3) is only invoked if routed: i.e. the L2 score < route_thr (or no L2 in the stack)."""
    n = a["n"]
    alive = np.ones(n, bool)       # still unblocked
    latency = np.zeros(n)
    blocked = np.zeros(n, bool)
    sys_fail = np.zeros(n, bool)
    calls = {}
    for L in layers:
        run = alive.copy()
        if L == "L3" and route and "L2" in layers:
            ps = a["p_entail"]
            run &= np.where(np.isnan(ps), True, ps < route_thr)
        run &= ~a["abstain"]
        calls[L] = run
        latency += np.where(run, a[f"{L}_lat"], 0.0)
        sys_fail |= run & (a[f"{L}_err"] | (a[f"{L}_lat"] > timeout_ms))
        flag = run & a[f"{L}_flag"]
        blocked |= flag
        alive &= ~flag
    h = a["hallu"]
    return {
        "layers": list(layers),
        "residual_rate": float(np.mean(h & alive)),            # critical failures that get through
        "baseline_rate": float(np.mean(h)),
        "false_block_rate": float(np.mean(blocked & ~h)),      # good outputs that were blocked
        "sys_fail_rate": float(np.mean(sys_fail)),
        "mean_latency_ms": float(latency.mean()),
        "p95_latency_ms": float(np.percentile(latency, 95)),
        "sum_layer_mean_ms": float(sum(a[f"{L}_lat"][calls[L]].mean() if calls[L].any() else 0.0 for L in layers)),
        "judge_route_rate": float(np.mean(calls["L3"])) if "L3" in layers else 0.0,
        "per_layer_calls": {L: float(np.mean(calls[L])) for L in layers},
    }


def marginal_clearance(a):
    """c_i of the paper: share of baseline hallucinations that layer i catches on its own."""
    h = a["hallu"]
    return {L: float(np.mean(a[f"{L}_flag"][h])) if h.any() else 0.0 for L in LAYERS}


def conditional_clearance(a, layers, **kw):
    """c_i conditional on the earlier layers of the cascade (what really multiplies in lambda_N)."""
    out, prev = {}, []
    h = a["hallu"]
    for L in layers:
        before = evaluate_cascade(a, prev, **kw)["residual_rate"] if prev else float(np.mean(h))
        prev = prev + [L]
        after = evaluate_cascade(a, prev, **kw)["residual_rate"]
        out[L] = 0.0 if before == 0 else 1.0 - after / before
    return out


def optimise(a, daily_queries, alpha, weights, sla_ms, sla_metric="mean", route_thr=0.9, timeout_ms=2000.0):
    """Enumerate cascades (canonical order L1<L2<L3, all subsets incl. 'no guardrail') and score with
         w1*k*(alpha; lambda_N) + w2*latency + w3*lambda_sys_fail   s.t. latency <= SLA."""
    c_marg = marginal_clearance(a)
    rows = []
    for r in range(0, len(LAYERS) + 1):
        for subset in itertools.combinations(LAYERS, r):
            e = evaluate_cascade(a, subset, route_thr=route_thr, timeout_ms=timeout_ms)
            lam = daily_queries * e["residual_rate"]
            lam0 = daily_queries * e["baseline_rate"]
            lam_indep = lam0 * float(np.prod([1 - c_marg[L] for L in subset])) if subset else lam0
            lat = {"mean": e["mean_latency_ms"], "p95": e["p95_latency_ms"], "sum": e["sum_layer_mean_ms"]}[sla_metric]
            lam_sys = daily_queries * e["sys_fail_rate"]
            lam_fp = daily_queries * e["false_block_rate"]
            k = capacity(lam, alpha)
            e.update(
                config="+".join(subset) or "none",
                lambda_per_day=lam, lambda_independent_formula=lam_indep, lambda_baseline=lam0,
                lambda_sys_fail=lam_sys, lambda_false_block=lam_fp, k_star=k, latency_for_sla=lat,
                feasible=bool(lat <= sla_ms),
                objective=weights.w_capacity * k + weights.w_latency * lat + weights.w_sysfail * lam_sys + weights.w_fp * lam_fp,
                conditional_clearance=conditional_clearance(a, subset, route_thr=route_thr, timeout_ms=timeout_ms) if subset else {},
            )
            rows.append(e)
    feas = [r for r in rows if r["feasible"]]
    best = min(feas, key=lambda r: r["objective"]) if feas else None
    return rows, best, c_marg
