"""Table 4 recomputed with two derailment components, and the matching threshold rule (Proposition 6').

Model change. Each error (a) derails the task into a WRONG output with probability theta_w (cost F if the task completes),
and (b) triggers the agent's own transfer to a human with probability theta_h (cost H, the task ends). The firm still
chooses when to hand off. Per step: e ~ Poisson(mu); the agent self-escalates with prob s(e) = 1-(1-theta_h)^e;
otherwise the task completes w.p. q and pays F*pi_w(N+e), else it continues.

One-step-lookahead (OLA) threshold, with rho_h = exp(-mu*theta_h), theta~ = theta_w + theta_h - theta_w*theta_h:
  continue at count N  iff  (1-theta_w)^N >= RHS,  RHS = exp(mu*theta~) * [ (k+c*mu)/(q*F) - rho_h*(H-F)/F ]
  N* = smallest N with (1-theta_w)^N <= RHS        (theta_h = 0 gives the original Equation (3)).
The stopping set is absorbing (counts never fall; self-escalation does not change the count dynamics), so OLA is optimal
(monotone case of optimal stopping). This script checks the closed form against value iteration.

Estimation (same estimator as theory/theta_all.py): theta = 1 - S_inj/S_ctrl with task-clustered bootstrap, split exactly as
  theta_h = [extra failures that include a transfer_to_human_agents call] / S_ctrl
  theta_w = [extra failures without a transfer call]                     / S_ctrl     (theta = theta_h + theta_w)
Coding experiment: there is no transfer tool, so theta_h = 0 and theta_w = theta.
"""
import json, math, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SVC = ROOT / "replication/replication_agent_handoff/inject/results"
k, c, q, H, mu = 1.0, 5.0, 0.06, 40.0, 0.054
MAXREP = {"deepseek": 2, "gpt61terra": 2, "sonnet55": 2}
MODELS = ["llama8b", "llama70b", "deepseek", "gpt61terra", "sonnet55"]
B = 2000


# ------------------------------------------------------------------ thresholds
def rhs_new(tw, th, F):
    rho = math.exp(-mu * th); tt = tw + th - tw * th
    return math.exp(mu * tt) * ((k + c * mu) / (q * F) - rho * (H - F) / F)


def n_star_new(tw, th, F):
    r = rhs_new(tw, th, F)
    if r >= 1: return 0
    if tw <= 0 or r <= 0: return math.inf
    return max(0, math.ceil(math.log(r) / math.log(1 - tw) - 1e-12))


def n_star_old(theta, F):
    return n_star_new(theta, 0.0, F)


def vi_threshold(tw, th, F, Nmax=80, emax=12):
    """Value iteration on the count N in the model with self-escalation."""
    e = np.arange(emax + 1); pe = np.array([math.exp(-mu) * mu**i / math.factorial(i) for i in e]); pe /= pe.sum()
    s = 1 - (1 - th) ** e
    V = np.full(Nmax + 1 + emax, H)

    def pi(N): return 1 - (1 - tw) ** N
    for _ in range(4000):
        Vn = V.copy()
        for N in range(Nmax + 1):
            Nn = N + e
            cont = k + c * mu + float(np.sum(pe * (s * H + (1 - s) * (q * F * pi(Nn) + (1 - q) * V[np.minimum(Nn, len(V) - 1)]))))
            Vn[N] = min(H, cont)
        Vn[Nmax + 1:] = H
        if np.max(np.abs(Vn - V)) < 1e-12: V = Vn; break
        V = Vn
    stop = []
    for N in range(Nmax + 1):
        Nn = N + e
        cont = k + c * mu + float(np.sum(pe * (s * H + (1 - s) * (q * F * pi(Nn) + (1 - q) * V[np.minimum(Nn, len(V) - 1)]))))
        stop.append(H <= cont + 1e-12)
    for N, st in enumerate(stop):
        if st: return N
    return math.inf


def check_closed_form(ndraw=150):
    global k, c, q, H, mu
    save = (k, c, q, H, mu); rng = np.random.default_rng(3); bad = 0; tot = 0
    for _ in range(ndraw):
        k = rng.uniform(0.5, 2); c = rng.uniform(1, 8); q = rng.uniform(0.03, 0.3); mu = rng.uniform(0.02, 0.3)
        H = rng.uniform(15, 80); F = rng.uniform(30, 200)
        tw = rng.uniform(0.02, 0.6); th = rng.choice([0.0, rng.uniform(0.02, 0.6)])
        a, b = n_star_new(tw, th, F), vi_threshold(tw, th, F)
        tot += 1
        if not (a == b or (math.isinf(a) and math.isinf(b))): bad += 1; print("  mismatch", dict(tw=tw, th=th, F=F, closed=a, vi=b))
    k, c, q, H, mu = save
    print(f"closed-form N* vs value iteration (random parameters, with and without self-escalation): mismatches {bad}/{tot}")


# ------------------------------------------------------------------ estimation
def load(m):
    out = {}
    for l in open(SVC / f"{m}.jsonl"):
        r = json.loads(l)
        if r.get("ok") and r["rep"] < MAXREP.get(m, 99): out[r["key"]] = r
    return list(out.values())


def est(m):
    R = load(m); tasks = sorted({r["domain"] + ":" + r["task"] for r in R}); idx = {t: i for i, t in enumerate(tasks)}
    by = {a: [[] for _ in tasks] for a in ("control", "single", "blame")}
    for r in R:
        if r["arm"] not in by: continue
        tr = int(any(cl["name"] == "transfer_to_human_agents" for cl in r["calls"]))
        by[r["arm"]][idx[r["domain"] + ":" + r["task"]]].append((r["reward"] or 0.0, tr))

    def stats(ts, arm):
        v = [x for t in ts for x in by[arm][t]]
        rew = np.mean([x[0] for x in v]); ftr = np.mean([(1 - x[0]) * x[1] for x in v]); fno = np.mean([(1 - x[0]) * (1 - x[1]) for x in v])
        ptr = np.mean([x[1] for x in v])
        sno = np.mean([x[0] * (1 - x[1]) for x in v])  # success without any transfer
        return rew, ftr, fno, ptr, sno

    def comp(ts):
        sc = stats(ts, "control"); out = {"S_ctrl": sc[0], "ptr_ctrl": sc[3]}
        for arm, nm in (("single", "transient"), ("blame", "misleading")):
            s = stats(ts, arm)
            if sc[0] <= 0 or sc[4] <= 0 or sc[3] >= 1: out[nm] = (np.nan,) * 6; continue
            # model-consistent estimator: error-induced transfer thins the runs that would not have transferred;
            # success-without-transfer is then thinned by (1-theta_h)(1-theta_w)
            thm_h = max(0.0, (s[3] - sc[3]) / (1 - sc[3]))
            thm_w = 1 - (s[4] / sc[4]) / (1 - thm_h) if thm_h < 1 else np.nan
            out[nm] = ((s[1] - sc[1]) / sc[0], (s[2] - sc[2]) / sc[0], 1 - s[0] / sc[0], s[3] - sc[3], thm_h, thm_w)
        return out
    e = comp(list(range(len(tasks)))); rng = np.random.default_rng(1)
    bs = [comp(list(rng.integers(0, len(tasks), len(tasks)))) for _ in range(B)]
    res = {"S_ctrl": float(e["S_ctrl"]), "ptr_ctrl": float(e["ptr_ctrl"])}
    for nm in ("transient", "misleading"):
        d = {}
        for j, key in enumerate(("theta_h", "theta_w", "theta", "d_transfer", "thm_h", "thm_w")):
            v = [b[nm][j] for b in bs if not np.isnan(b[nm][j])]
            d[key] = None if np.isnan(e[nm][j]) else float(e[nm][j])
            d[key + "_ci"] = [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] if v else None
        res[nm] = d
    return res


def fmt(x, ci=None):
    if x is None: return "NA"
    s = f"{x:+.2f}"
    return s + (f" [{ci[0]:+.2f}, {ci[1]:+.2f}]" if ci else "")


def ns(v): return "inf" if math.isinf(v) else ("0" if v == 0 else str(int(v)))


if __name__ == "__main__":
    check_closed_form()
    out = {}
    print("\nTable 4 (customer service), old = theta total as in the manuscript, new = split into theta_w (wrong output) and theta_h (self-transfer)")
    print(" H=40, k=1, c=5, q=0.06, mu=0.054; F in {60,100}; 'inf' = no count rule is worthwhile\n")
    print(f"{'agent':11s} {'kind':10s} {'S_ctrl':>6s} {'theta (old)':>20s} {'theta_h (transfer)':>22s} {'theta_w (wrong)':>22s} {'extra P(transfer)':>18s}  N* old F60/100   N* new F60/100")
    for m in MODELS:
        r = est(m)
        if r["S_ctrl"] < 0.05: continue
        out[m] = r
        for nm in ("transient", "misleading"):
            d = r[nm]
            th_c = max(0.0, d["theta_h"]); tw_c = max(0.0, d["theta_w"]); t_old = max(0.0, d["theta"])
            # significance-aware: a component whose CI includes zero is treated as zero for the recommendation
            tw_use = tw_c if d["theta_w_ci"][0] > 0 else 0.0
            th_use = th_c if d["theta_h_ci"][0] > 0 else 0.0
            to_use = t_old if d["theta_ci"][0] > 0 else 0.0
            old = [ns(n_star_old(to_use, F)) if to_use > 0 else "none" for F in (60.0, 100.0)]
            new = [ns(n_star_new(tw_use, th_use, F)) if (tw_use > 0 or th_use > 0) else "none" for F in (60.0, 100.0)]
            d["n_star_old"] = old; d["n_star_new"] = new
            print(f"{m:11s} {nm:10s} {r['S_ctrl']:6.2f} {fmt(d['theta'], d['theta_ci']):>20s} {fmt(d['theta_h'], d['theta_h_ci']):>22s} {fmt(d['theta_w'], d['theta_w_ci']):>22s} {fmt(d['d_transfer'], d['d_transfer_ci']):>18s}  {'/'.join(old):>13s}   {'/'.join(new):>13s}")
    print("\nSensitivity: model-consistent estimator (independent hazards; success-without-transfer thinned by (1-theta_h)(1-theta_w))")
    print(f"{'agent':11s} {'kind':10s} {'theta_h (model)':>22s} {'theta_w (model)':>22s}   N* additive F60/100   N* model-consistent F60/100")
    for m in MODELS:
        if m not in out: continue
        for nm in ("transient", "misleading"):
            d = out[m][nm]
            if d.get("thm_w") is None: continue
            th_use = max(0.0, d["thm_h"]) if d["thm_h_ci"][0] > 0 else 0.0
            tw_use = max(0.0, d["thm_w"]) if d["thm_w_ci"][0] > 0 else 0.0
            new = [ns(n_star_new(tw_use, th_use, F)) if (tw_use > 0 or th_use > 0) else "none" for F in (60.0, 100.0)]
            d["n_star_model_consistent"] = new
            print(f"{m:11s} {nm:10s} {fmt(d['thm_h'], d['thm_h_ci']):>22s} {fmt(d['thm_w'], d['thm_w_ci']):>22s}   {'/'.join(d['n_star_new']):>14s}      {'/'.join(new):>14s}")
    Path(ROOT / "sim/table4_two_component.json").write_text(json.dumps(out, indent=1))
