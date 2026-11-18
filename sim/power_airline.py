"""Power of the airline sample (50 tasks) to detect a wrong-output channel theta_w, and what more repetitions would buy.

Per (task, repetition) pair of a control run and a misleading-message run we compute the extra failures WITHOUT a transfer
call, y = [(1-rew) (1-tr)]_blame - [(1-rew)(1-tr)]_control; the additive estimate is theta_w = mean(y) / S_control.
With R repetitions per task, Var(task mean) = s_b^2 + s_w^2 / R (between-task and within-task components, one-way random
effects). More repetitions shrink only the within-task part: SE(R) = sqrt((s_b^2 + s_w^2/R) / n_tasks) / S_control.
"""
import json, math, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "replication/replication_agent_handoff/inject/results"
MAXR = {"deepseek": 2}
Z = 2.8                 # 80% power, two-sided 5%
TARGET = 0.12           # theta_w at which the airline threshold would be about 2 at the central airline cost (Table 8)


def load(m, dom):
    seen = {}
    for l in open(RES / f"{m}.jsonl"):
        r = json.loads(l)
        if r.get("ok") and r["domain"] == dom and r["rep"] < MAXR.get(m, 99): seen[r["key"]] = r
    return list(seen.values())


def analyse(m, dom="airline"):
    R = load(m, dom)
    cell = {}
    cost = []
    for r in R:
        tr = int(any(c["name"] == "transfer_to_human_agents" for c in r["calls"]))
        f_no = (1 - (r["reward"] or 0.0)) * (1 - tr)
        cell[(r["task"], r["rep"], r["arm"])] = (r["reward"] or 0.0, f_no)
        cost.append((r.get("agent_cost") or 0.0) + (r.get("user_cost") or 0.0))
    tasks = sorted({k[0] for k in cell}, key=lambda x: int(x)); ys = {}
    sc, n_ctrl = 0.0, 0
    for t in tasks:
        v = []
        for rep in range(10):
            b, c = cell.get((t, rep, "blame")), cell.get((t, rep, "control"))
            if b and c: v.append(b[1] - c[1])
        if v: ys[t] = v
    for (t, rep, arm), (rew, _) in cell.items():
        if arm == "control": sc += rew; n_ctrl += 1
    S = sc / n_ctrl
    n = len(ys); Rr = np.mean([len(v) for v in ys.values()])
    means = np.array([np.mean(v) for v in ys.values()])
    sw2 = float(np.mean([np.var(v, ddof=1) for v in ys.values() if len(v) > 1]))
    sb2 = max(float(np.var(means, ddof=1)) - sw2 / Rr, 0.0)
    se = lambda R_: math.sqrt((sb2 + sw2 / R_) / n) / S
    need = (TARGET / Z * S) ** 2 * n - sb2
    R_need = sw2 / need if need > 0 else float("inf")
    return dict(S_ctrl=S, n_tasks=n, reps_now=float(Rr), s_b2=sb2, s_w2=sw2, se_now=se(Rr), mde_now=Z * se(Rr),
                se_floor=math.sqrt(sb2 / n) / S, mde_floor=Z * math.sqrt(sb2 / n) / S,
                reps_needed_for_target=R_need, mde_by_reps={str(r_): Z * se(r_) for r_ in (2, 4, 6, 8, 10)},
                cost_per_run=float(np.mean(cost)), runs_per_extra_rep=2 * n)


if __name__ == "__main__":
    out = {m: analyse(m) for m in ("deepseek", "gpt61terra", "sonnet55")}
    (ROOT / "sim/power_airline.json").write_text(json.dumps(out, indent=1))
    print(f"Detectable theta_w (80% power, additive estimator) with {50} airline tasks; target theta_w = {TARGET}")
    for m, r in out.items():
        print(f"\n{m}: S_ctrl {r['S_ctrl']:.2f}, reps now {r['reps_now']:.1f}, between-task var {r['s_b2']:.4f}, within-task var {r['s_w2']:.4f}")
        print(f"   SE now {r['se_now']:.3f} -> detectable theta_w {r['mde_now']:.2f};  floor with unlimited repetitions: {r['mde_floor']:.2f}")
        print("   detectable theta_w by repetitions:", {k: round(v, 3) for k, v in r["mde_by_reps"].items()}, "| repetitions needed for the target:", "unreachable" if math.isinf(r["reps_needed_for_target"]) else f"{r['reps_needed_for_target']:.1f}")
        for Rn in (4, 6, 10):
            extra = (Rn - round(r["reps_now"])) * r["runs_per_extra_rep"]
            print(f"   {Rn} reps: {extra} extra runs, about ${extra * r['cost_per_run']:.2f} at ${r['cost_per_run']:.4f} per run (measured cost per run in this domain)")
