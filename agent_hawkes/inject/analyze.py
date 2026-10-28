"""Analysis of the fault-injection experiment. Writes inject_results.json.
Unit of time: the agent's tool calls. Agent error: a tool call the real environment rejected (injected calls excluded).
1. Task success by arm (environment check), task-clustered bootstrap.
2. Causal excitation: agent-error rate in the W calls after the injection point vs the same window in control runs
   (control runs carry a virtual injection index j drawn the same way). Pre-window rates check balance.
3. Lag profile: logit of agent error at call i on injected-error lags 1..L (exogenous) and agent-error lags 1..L,
   with task fixed effects (conditional logit approximated by task dummies) -> jump and decay of excitation.
"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm

HERE = Path(__file__).resolve().parent
import os
MAX_REPS = {"deepseek": 2}  # DeepSeek was cut to two repetitions because of upstream rate limits
W, L, B = 5, 3, int(os.environ.get("B", 1000))


def load(m):
    rows = [json.loads(l) for l in open(HERE / "results" / f"{m}.jsonl")]
    rows = [r for r in rows if r.get("ok") and r["rep"] < MAX_REPS.get(m, 99)]
    seen = {}
    for r in rows: seen[r["key"]] = r  # keep the last complete record per key
    return list(seen.values())


def boot(df, stat, cluster="tid"):
    rng = np.random.default_rng(0); g = {k: v for k, v in df.groupby(cluster)}; keys = list(g)
    vals = []
    for _ in range(B):
        s = pd.concat([g[k] for k in rng.choice(keys, len(keys))]); vals.append(stat(s))
    return [float(np.nanpercentile(vals, 2.5)), float(np.nanpercentile(vals, 97.5))]


def analyse(m):
    R = load(m)
    runs = pd.DataFrame([dict(tid=r["domain"] + ":" + r["task"], arm=r["arm"], rep=r["rep"], reward=r["reward"] or 0.0,
                              crashed=r.get("crashed", 0), n_calls=len(r["calls"]), n_inj=r["n_inj"], j=r["j"]) for r in R])
    out = dict(n_runs=len(runs), n_tasks=runs.tid.nunique(), crash_rate=runs.groupby("arm").crashed.mean().round(3).to_dict(),
               mean_calls=runs.groupby("arm").n_calls.mean().round(2).to_dict())
    succ = {}
    for arm in ("control", "single", "blame", "multi"):
        d = runs[runs.arm == arm]
        if not len(d): continue
        succ[arm] = dict(rate=float(d.reward.mean()), ci=boot(d, lambda s: s.reward.mean()))
    for arm in ("single", "blame", "multi"):
        piv = runs.pivot_table(index=["tid", "rep"], columns="arm", values="reward")
        if arm not in piv: continue
        piv = piv.dropna(subset=["control", arm]).reset_index()
        if not len(piv): continue
        succ[arm + "_minus_control"] = dict(diff=float((piv[arm] - piv.control).mean()), ci=boot(piv, lambda s: (s[arm] - s.control).mean()), n_pairs=len(piv))
    out["success"] = succ
    # 2. window comparison: single vs control at the same j
    win = []
    for r in R:
        if r["arm"] not in ("control", "single", "blame"): continue
        c = r["calls"]; j = r["j"]
        if len(c) < j: continue  # injection point never reached
        if r["arm"] != "control" and not any(x["injected"] for x in c): continue
        post = [x["error"] for x in c if j < x["i"] <= j + W and not x["injected"]]
        post2 = [x["error"] for x in c if j + 1 < x["i"] <= j + W and not x["injected"]]  # skips the immediate retry
        pre = [x["error"] for x in c if x["i"] < j and not x["injected"]]
        win.append(dict(tid=r["domain"] + ":" + r["task"], arm=r["arm"], post_err=sum(post), post_n=len(post), post2_err=sum(post2), post2_n=len(post2), pre_err=sum(pre), pre_n=len(pre)))
    wd = pd.DataFrame(win)
    def rate(s, a, k): d = s[s.arm == a]; return d[k + "_err"].sum() / max(d[k + "_n"].sum(), 1)
    ex = {}
    for arm in ("single", "blame"):
        if (wd.arm == arm).sum() < 2: continue
        for k in ("post", "post2", "pre"):
            ex[f"{arm}_{k}"] = dict(control=float(rate(wd, "control", k)), treated=float(rate(wd, arm, k)),
                                    diff=float(rate(wd, arm, k) - rate(wd, "control", k)),
                                    ci=boot(wd, lambda s, k=k, arm=arm: rate(s, arm, k) - rate(s, "control", k)))
    ex["n_runs"] = wd.groupby("arm").size().to_dict()
    out["window"] = ex
    # 3. lag regression across all arms
    rows = []
    for r in R:
        c = r["calls"]; tid = r["domain"] + ":" + r["task"]
        inj = [x["injected"] for x in c]; arm = r["arm"]; err = [x["error"] * (1 - x["injected"]) for x in c]
        for t in range(len(c)):
            if inj[t]: continue
            d = dict(tid=tid, y=err[t], pos=np.log1p(t), blame=int(arm == "blame"))
            for l in range(1, L + 1):
                d[f"inj{l}"] = inj[t - l] * (arm != "blame") if t - l >= 0 else 0
                d[f"blm{l}"] = inj[t - l] * (arm == "blame") if t - l >= 0 else 0
                d[f"err{l}"] = err[t - l] if t - l >= 0 else 0
            rows.append(d)
    X = pd.DataFrame(rows)
    keep = X.groupby("tid").y.transform(lambda v: 0 < v.mean() < 1)  # tasks with variation (conditional-logit logic)
    Xk = X[keep]
    cols = [f"inj{l}" for l in range(1, L + 1)] + [f"blm{l}" for l in range(1, L + 1)] + [f"err{l}" for l in range(1, L + 1)] + ["pos"]
    D = pd.get_dummies(Xk.tid, drop_first=True, dtype=float)
    try:
        fit = sm.Logit(Xk.y.values, pd.concat([Xk[cols].astype(float), D], axis=1).assign(const=1.0)).fit(disp=0, maxiter=200, method="lbfgs")
        se = np.sqrt(np.diag(fit.cov_params()))[:len(cols)] if hasattr(fit, "cov_params") else [np.nan] * len(cols)
        out["lag_logit"] = {c_: dict(b=float(fit.params[c_]), se=float(s_)) for c_, s_ in zip(cols, se)}
    except Exception as e:
        out["lag_logit"] = dict(error=str(e))
    out["lag_logit_n"] = dict(obs=int(len(Xk)), tasks=int(Xk.tid.nunique()), base_rate=float(X.y.mean()))
    # raw lag profile: agent-error rate k calls after an injection vs overall
    prof = {}
    for v in ("inj", "blm"):
        for l in range(1, L + 1):
            s = X[X[f"{v}{l}"] == 1]; prof[f"{v}{l}"] = dict(rate=float(s.y.mean()) if len(s) else None, n=int(len(s)))
    prof["baseline_no_recent_inj"] = float(X[(X[[f"{v}{l}" for v in ("inj", "blm") for l in range(1, L + 1)]].sum(axis=1) == 0)].y.mean())
    out["lag_profile"] = prof
    return out


if __name__ == "__main__":
    models = sys.argv[1:] or ["llama8b", "llama70b", "deepseek"]
    res = {m: analyse(m) for m in models if (HERE / "results" / f"{m}.jsonl").exists()}
    json.dump(res, open(HERE / "inject_results.json", "w"), indent=1); print(json.dumps(res, indent=1))
