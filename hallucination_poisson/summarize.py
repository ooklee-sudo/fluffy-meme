"""Collect everything the paper needs from runs/*/ into runs/summary.json."""
import json
import numpy as np
from analysis import Costs, daily_cost, evaluate_cascade, load_arrays, marginal_clearance, layer_dependence, optimise, Weights
from scipy import stats as sps
from stats_model import capacity

def auc_good_vs_hallu(recs, layer="L2"):
    """AUC of the layer score for separating good (high) from hallucinated (low) non-abstained answers."""
    rr = [x for x in recs if not x["abstained"] and x[layer]["score"] is not None]
    h = np.array([x["hallucinated"] for x in rr]); p = np.array([x[layer]["score"] for x in rr])
    g, b = p[~h], p[h]
    return float(np.mean((g[:, None] > b[None, :]) + 0.5 * (g[:, None] == b[None, :])))


def _resid_share(a, layers, route):
    return evaluate_cascade(a, layers, route=route, route_thr=0.9)["residual_rate"] / max(a["hallu"].mean(), 1e-12)


def _ind(a, layers):
    c = marginal_clearance(a)
    return float(np.prod([1 - c[L] for L in layers]))


def dependence_stats(a, reps=1000, seed=0):
    """L2-L3 dependence among hallucinated answers (2x2 table, phi, chi-square p) and the observed/independent ratio of the residual share with 95% pool-bootstrap CIs."""
    h = a["hallu"]
    x, y = a["L2_flag"][h], a["L3_flag"][h]
    tab = np.array([[np.sum(x & y), np.sum(x & ~y)], [np.sum(~x & y), np.sum(~x & ~y)]])
    chi2, p, _, _ = sps.chi2_contingency(tab, correction=False)
    phi = float(np.sqrt(chi2 / tab.sum()) * np.sign(tab[0, 0] * tab[1, 1] - tab[0, 1] * tab[1, 0]))
    out = {"table_L2xL3_among_hallucinated": tab.tolist(), "phi": phi, "chi2_p": float(p)}
    rng = np.random.default_rng(seed); n = a["n"]; keys = [k for k in a if k != "n"]
    phis, r_nr, r_r = [], [], []
    for _ in range(reps):
        idx = rng.integers(0, n, n); b = {k: a[k][idx] for k in keys}; b["n"] = n
        hb = b["hallu"]; xb, yb = b["L2_flag"][hb], b["L3_flag"][hb]
        if xb.std() > 0 and yb.std() > 0:
            phis.append(float(np.corrcoef(xb, yb)[0, 1]))
        ib = _ind(b, ["L2", "L3"])
        if ib > 0:
            r_nr.append(_resid_share(b, ["L2", "L3"], False) / ib); r_r.append(_resid_share(b, ["L2", "L3"], True) / ib)
    q = lambda v: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]
    out["phi_ci"] = q(phis)
    out["ratio_no_routing"] = {"point": _resid_share(a, ["L2", "L3"], False) / _ind(a, ["L2", "L3"]), "ci": q(r_nr)}
    out["ratio_with_routing"] = {"point": _resid_share(a, ["L2", "L3"], True) / _ind(a, ["L2", "L3"]), "ci": q(r_r)}
    out["n_pass_no_routing"] = int(round(_resid_share(a, ["L2", "L3"], False) * h.sum()))
    out["n_pass_with_routing"] = int(round(_resid_share(a, ["L2", "L3"], True) * h.sum()))
    return out


COSTS = Costs(150.0, (0.0, 0.0001, 0.002), 1.0, 100.0)


def _cfg_cost(b, layers, daily_queries=200, alpha=0.95):
    e = evaluate_cascade(b, layers, route_thr=0.9)
    lam = daily_queries * e["residual_rate"]
    row = {"layers": layers, "k_star": capacity(lam, alpha), "lambda_false_block": daily_queries * e["false_block_rate"], "lambda_per_day": lam, "per_layer_calls": e["per_layer_calls"]}
    return daily_cost(row, daily_queries, COSTS)["total"]


def cost_saving_ci(a, reps=500, seed=0):
    """Paired pool-bootstrap CI of the daily cost saving of adding layers (scenario costs: C_h $150/unit, $1 per false block, $100 per residual hallucination)."""
    rng = np.random.default_rng(seed); n = a["n"]; keys = [k for k in a if k != "n"]
    pairs = {"L1+L2+L3 vs L1+L2": (["L1", "L2", "L3"], ["L1", "L2"]), "L2+L3 vs L2": (["L2", "L3"], ["L2"]), "L1+L2 vs none": (["L1", "L2"], [])}
    out = {}
    pt = {k: _cfg_cost(a, v[1]) - _cfg_cost(a, v[0]) for k, v in pairs.items()}
    draws = {k: [] for k in pairs}
    for _ in range(reps):
        idx = rng.integers(0, n, n); b = {k: a[k][idx] for k in keys}; b["n"] = n
        for k, v in pairs.items():
            draws[k].append(_cfg_cost(b, v[1]) - _cfg_cost(b, v[0]))
    for k in pairs:
        out[k] = {"saving_point": float(pt[k]), "ci": [float(np.percentile(draws[k], 2.5)), float(np.percentile(draws[k], 97.5))]}
    return out


out = {}
for r in ("qwen05", "smol360", "qwen15"):
    recs = [json.loads(l) for l in open(f"runs/{r}/records.jsonl", encoding="utf-8")]
    a = load_arrays(recs)
    meta = json.load(open(f"runs/{r}/meta.json"))
    c = marginal_clearance(a)
    ind = lambda ls: float(np.prod([1 - c[L] for L in ls]))
    rows = {}
    for ls in (["L2"], ["L2", "L3"], ["L1", "L2", "L3"]):
        no_route = evaluate_cascade(a, ls, route=False)["residual_rate"] / a["hallu"].mean()
        route = evaluate_cascade(a, ls, route_thr=0.9)["residual_rate"] / a["hallu"].mean()
        rows["+".join(ls)] = {"independent": ind(ls), "observed_no_routing": no_route, "observed_with_routing": route}
    nli = [json.loads(l) for l in open(f"runs/{r}/records_nli.jsonl", encoding="utf-8")]
    out[r] = {
        "auc_l2": auc_good_vs_hallu(recs), "auc_nli_negative_result": auc_good_vs_hallu(nli),
        "nli_catch_and_falseblock_at_0.5": [float(np.mean([x["L2"]["flag"] for x in nli if x["hallucinated"]])), float(np.mean([x["L2"]["flag"] for x in nli if not x["hallucinated"] and not x["abstained"]]))],
        "generator": meta["generator"], "n": a["n"], "p_halluc": float(a["hallu"].mean()),
        "abstain_rate": float(a["abstain"].mean()),
        "gen_latency_ms_mean": float(np.mean([x["gen_latency_ms"] for x in recs])),
        "marginal_clearance": c, "dependence": layer_dependence(a), "residual_share": rows,
        "layer_latency_ms": {L: {"mean": float(a[f"{L}_lat"][~a["abstain"]].mean()), "p95": float(np.percentile(a[f"{L}_lat"][~a["abstain"]], 95))} for L in ("L1", "L2", "L3")},
        "layer_timeouts_share": {L: float(np.mean((a[f"{L}_lat"] > 2000)[~a["abstain"]])) for L in ("L1", "L2", "L3")},
        "false_block_share_of_good": {L: float(np.mean(a[f"{L}_flag"][~a["hallu"] & ~a["abstain"]])) for L in ("L1", "L2", "L3")},
        "n_good_non_abstained": int((~a["hallu"] & ~a["abstain"]).sum()), "n_abstained": int(a["abstain"].sum()), "n_hallucinated": int(a["hallu"].sum()),
        "dependence_stats": dependence_stats(a), "cost_saving_ci": cost_saving_ci(a),
        "sla500": json.load(open(f"runs/{r}/analysis_sla500.json")),
        "sla100": json.load(open(f"runs/{r}/analysis.json")) if False else None,
        "burst": json.load(open(f"runs/{r}/analysis_burst.json")),
        "burst044": json.load(open(f"runs/{r}/analysis_burst044.json")),
    }
json.dump(out, open("runs/summary.json", "w"), indent=1, default=float)
for r, d in out.items():
    print(r, round(d["p_halluc"], 3), {k: round(v, 3) for k, v in d["marginal_clearance"].items()})
    print("  residual share", {k: {kk: round(vv, 3) for kk, vv in v.items()} for k, v in d["residual_share"].items()})
    print("  latency", {k: round(v["mean"], 1) for k, v in d["layer_latency_ms"].items()}, "timeouts", d["layer_timeouts_share"], "FP of good", {k: round(v, 3) for k, v in d["false_block_share_of_good"].items()})

out["real_data"] = json.load(open("runs/real_data.json"))
out["triage"] = json.load(open("runs/triage_data.json"))
out["failure"] = json.load(open("runs/failure_models.json"))
out["cases"] = json.load(open("runs/hallucination_cases.json"))
json.dump(out, open("runs/summary.json", "w"), indent=1, default=float)
