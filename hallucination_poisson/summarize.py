"""Collect everything the paper needs from runs/*/ into runs/summary.json."""
import json
import numpy as np
from analysis import evaluate_cascade, load_arrays, marginal_clearance, layer_dependence

def auc_good_vs_hallu(recs, layer="L2"):
    """AUC of the layer score for separating good (high) from hallucinated (low) non-abstained answers."""
    rr = [x for x in recs if not x["abstained"] and x[layer]["score"] is not None]
    h = np.array([x["hallucinated"] for x in rr]); p = np.array([x[layer]["score"] for x in rr])
    g, b = p[~h], p[h]
    return float(np.mean((g[:, None] > b[None, :]) + 0.5 * (g[:, None] == b[None, :])))


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
        "false_block_share_of_good": {L: float(np.mean(a[f"{L}_flag"][~a["hallu"]])) for L in ("L1", "L2", "L3")},
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
json.dump(out, open("runs/summary.json", "w"), indent=1, default=float)
