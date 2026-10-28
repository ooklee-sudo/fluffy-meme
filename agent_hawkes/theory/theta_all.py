"""Derailment probability by agent, task domain and error type, and the count thresholds of Proposition 6.
theta = 1 - success(injected arm) / success(control), task-clustered bootstrap. 'transient' = the 503 message (single arm),
'misleading' = the "<argument> '<value>' not found" message (blame arm). Writes theta_all.json."""
import json
from pathlib import Path
import numpy as np
from derail import solve, n_star, never_cost, H
HERE = Path(__file__).resolve().parent
SRC = {"service": HERE.parent / "inject" / "results", "coding": HERE.parent / "inject_code" / "results"}
MAXREP = {("service", "deepseek"): 2, ("service", "gpt61terra"): 2, ("service", "sonnet55"): 2}
MODELS = ["llama8b", "llama70b", "deepseek", "gpt61terra", "sonnet55"]


def load(dom, m):
    out = {}
    for l in open(SRC[dom] / f"{m}.jsonl"):
        r = json.loads(l)
        if r.get("ok") and r["rep"] < MAXREP.get((dom, m), 99): out[r["key"]] = r
    for r in out.values():
        r["tid"] = r.get("bug") or (r["domain"] + ":" + r["task"])
    return list(out.values())


def est(dom, m, B=2000):
    R = load(dom, m); tasks = sorted({r["tid"] for r in R})
    by = {t: {a: [] for a in ("control", "single", "blame")} for t in tasks}
    for r in R:
        if r["arm"] in by[r["tid"]]: by[r["tid"]][r["arm"]].append(r["reward"] or 0.0)
    def th(ts):
        s = {a: np.mean([v for t in ts for v in by[t][a]]) for a in ("control", "single", "blame")}
        if s["control"] <= 0: return {"transient": np.nan, "misleading": np.nan, "control": 0.0}
        return {"transient": 1 - s["single"] / s["control"], "misleading": 1 - s["blame"] / s["control"], "control": s["control"]}
    e = th(tasks); rng = np.random.default_rng(1)
    bs = [th([tasks[i] for i in rng.integers(0, len(tasks), len(tasks))]) for _ in range(B)]
    out = {"control_success": float(e["control"])}
    for k in ("transient", "misleading"):
        v = [b[k] for b in bs if not np.isnan(b[k])]
        out[k] = dict(theta=None if np.isnan(e[k]) else float(e[k]), ci=[float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if v else None)
    return out


if __name__ == "__main__":
    res = {}
    for dom in ("service", "coding"):
        for m in MODELS:
            r = est(dom, m)
            for k in ("transient", "misleading"):
                t = r[k]["theta"]
                if t is None or r["control_success"] < 0.05:
                    r[k]["n_star"] = None; continue
                th = max(0.0, t)
                r[k]["n_star"] = {str(int(F)): (None if th == 0 else n_star(th, F)) for F in (40.0, 60.0, 100.0)}
                r[k]["value_F60"] = round(min(H, never_cost(th, 60.0)) - solve(th, 60.0)["W0"], 3)
            res[f"{dom}|{m}"] = r
    json.dump(res, open(HERE / "theta_all.json", "w"), indent=1)
    for k, v in res.items():
        print(k, round(v["control_success"], 3), {e: (None if v[e]["theta"] is None else round(v[e]["theta"], 3), v[e]["ci"] and [round(c, 3) for c in v[e]["ci"]], v[e].get("n_star")) for e in ("transient", "misleading")})
