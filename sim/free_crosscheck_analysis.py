"""Free observational analysis on the existing tau2-bench injection runs (no API calls).

Question: after an injected error, does the agent cross-check (call a DIFFERENT read-only tool within the next two
calls), and are cross-checking runs less often derailed?

Definitions (per run, call index i = position among the agent's tool calls, j = injection index, shared by the
control run and the injected run of the same task/repetition because the seed is shared):
  window   : calls i in (j, j+2], excluding injected calls
  crosscheck (CC): a call in the window whose tool is a read tool (get_/find_/search_/list_) AND differs from the
                  tool of call j
  retry (RT)    : no CC, but the window contains the same tool as call j again
  none          : neither
Only runs that reached the injection point are used (control: at least j calls; injected arms: an injected call).

1. Induced behaviour: P(CC) in the injected run minus P(CC) in the paired control run (same task, rep) -> what the
   error itself causes (natural next-call patterns subtracted out). Cluster bootstrap over tasks.
2. Outcome by behaviour, within the blame arm: success, success of the paired control run, and
   theta_g = 1 - S_blame(g) / S_control(g) with the paired control runs of the same (task, rep) as the denominator.
   d_hat = 1 - theta_CC / theta_noCC (rough recovery rate implied by cross-checking).
Cross-checking is chosen by the agent, so 2 is observational (selection possible), unlike the randomized error itself.
"""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd

RES = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("replication/replication_agent_handoff/inject/results")
OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("sim/free_crosscheck_results.json")
MAXR = {"deepseek": 2}
READ = ("get_", "find_", "search_", "list_")
B = 2000


def load(m):
    rows = [json.loads(l) for l in open(RES / f"{m}.jsonl")]
    rows = [r for r in rows if r.get("ok") and r["rep"] < MAXR.get(m, 99)]
    seen = {}
    for r in rows: seen[r["key"]] = r
    return list(seen.values())


def behaviour(r):
    """Return (reached, label) for one run."""
    calls, j = r["calls"], r["j"]
    if len(calls) < j: return False, None
    if r["arm"] != "control" and not any(c["injected"] for c in calls): return False, None
    cj = next((c for c in calls if c["i"] == j), None)
    if cj is None: return False, None
    name_j = cj["name"]
    win = [c for c in calls if j < c["i"] <= j + 2 and not c["injected"]]
    cc = any(c["name"].startswith(READ) and c["name"] != name_j for c in win)
    rt = any(c["name"] == name_j for c in win)
    return True, ("CC" if cc else ("RT" if rt else "none"))


def build(m):
    recs = {}
    for r in load(m):
        ok, lab = behaviour(r)
        recs[(r["domain"] + ":" + r["task"], r["rep"], r["arm"])] = dict(reached=ok, lab=lab, rew=(r["reward"] or 0.0))
    rows = []
    for (tid, rep, arm), v in recs.items():
        if arm not in ("single", "blame"): continue
        c = recs.get((tid, rep, "control"))
        if not (v["reached"] and c and c["reached"]): continue
        rows.append(dict(tid=tid, rep=rep, arm=arm, lab=v["lab"], cc=int(v["lab"] == "CC"), rew=v["rew"],
                         c_lab=c["lab"], c_cc=int(c["lab"] == "CC"), c_rew=c["rew"]))
    return pd.DataFrame(rows)


def boot(df, stat, seed=0):
    rng = np.random.default_rng(seed)
    g = {k: v for k, v in df.groupby("tid")}; keys = list(g); vals = []
    for _ in range(B):
        s = pd.concat([g[k] for k in rng.choice(keys, len(keys))])
        vals.append(stat(s))
    vals = [v for v in vals if np.isfinite(v)]
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))] if vals else [None, None]


def theta(s):
    return 1 - s.rew.mean() / s.c_rew.mean() if len(s) and s.c_rew.mean() > 0 else np.nan


res = {}
for m in ["llama8b", "llama70b", "deepseek", "gpt61terra", "sonnet55"]:
    if not (RES / f"{m}.jsonl").exists(): continue
    D = build(m); out = {}
    for arm in ("single", "blame"):
        d = D[D.arm == arm]
        ind = dict(n_pairs=int(len(d)), p_cc_injected=float(d.cc.mean()), p_cc_control=float(d.c_cc.mean()),
                   induced=float(d.cc.mean() - d.c_cc.mean()),
                   induced_ci=boot(d, lambda s: s.cc.mean() - s.c_cc.mean()),
                   label_share={k: float((d.lab == k).mean()) for k in ("CC", "RT", "none")})
        out[arm] = dict(induced_behaviour=ind)
    d = D[D.arm == "blame"]
    byb = {}
    for lab in ("CC", "RT", "none"):
        s = d[d.lab == lab]
        if len(s) < 5: continue
        byb[lab] = dict(n=int(len(s)), success=float(s.rew.mean()), paired_control_success=float(s.c_rew.mean()),
                        theta=float(theta(s)) if np.isfinite(theta(s)) else None,
                        theta_ci=boot(s, theta))
    out["blame"]["outcome_by_behaviour"] = byb
    cc, nc = d[d.cc == 1], d[d.cc == 0]
    if len(cc) >= 5 and len(nc) >= 5:
        out["blame"]["theta_CC_vs_noCC"] = dict(
            theta_cc=float(theta(cc)), theta_nocc=float(theta(nc)),
            d_hat=float(1 - theta(cc) / theta(nc)) if np.isfinite(theta(cc)) and np.isfinite(theta(nc)) and theta(nc) > 0 else None,
            diff_theta_ci=boot(d, lambda s: theta(s[s.cc == 1]) - theta(s[s.cc == 0])))
    res[m] = out

OUT.write_text(json.dumps(res, indent=1))
for m, o in res.items():
    print(f"\n=== {m} ===")
    for arm in ("single", "blame"):
        i = o[arm]["induced_behaviour"]
        print(f" {arm:6s} pairs={i['n_pairs']:4d}  P(cross-check): injected {i['p_cc_injected']:.3f} vs control {i['p_cc_control']:.3f}  "
              f"induced {i['induced']:+.3f} {np.round(i['induced_ci'], 3).tolist()}  shares {{{', '.join(f'{k}:{v:.2f}' for k, v in i['label_share'].items())}}}")
    for lab, v in o["blame"].get("outcome_by_behaviour", {}).items():
        t = v["theta"]
        print(f"   blame/{lab:4s} n={v['n']:4d} success {v['success']:.3f}  paired-control {v['paired_control_success']:.3f}  "
              f"theta {('%.3f' % t) if t is not None else 'NA'} {np.round(v['theta_ci'], 3).tolist() if v['theta_ci'][0] is not None else ''}")
    t = o["blame"].get("theta_CC_vs_noCC")
    if t: print(f"   theta(CC) {t['theta_cc']:.3f} vs theta(no CC) {t['theta_nocc']:.3f};  d_hat {t['d_hat'] if t['d_hat'] is None else round(t['d_hat'], 3)};  diff CI {np.round(t['diff_theta_ci'], 3).tolist()}")
