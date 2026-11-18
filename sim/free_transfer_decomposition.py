"""Free analysis: how much of the success drop after an injected error is the AGENT TRANSFERRING TO A HUMAN
(transfer_to_human_agents) rather than finishing with a wrong database state?
tau2-bench scores the final database; a transfer therefore counts as failure unless the task expects it.
Per model and arm: share of runs with a transfer call, success by transfer status, and the decomposition of
the success difference vs control (paired by task and repetition, runs that reached the injection point)."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
RES = Path(sys.argv[1]); OUT = Path(sys.argv[2]); B = 2000
MAXR = {"deepseek": 2}
def load(m):
    rows = [json.loads(l) for l in open(RES / f"{m}.jsonl")]
    rows = [r for r in rows if r.get("ok") and r["rep"] < MAXR.get(m, 99)]
    seen = {}
    for r in rows: seen[r["key"]] = r
    return list(seen.values())
def reached(r):
    return len(r["calls"]) >= r["j"] if r["arm"] == "control" else any(c["injected"] for c in r["calls"])
res = {}
for m in ["llama70b", "deepseek", "gpt61terra", "sonnet55"]:
    R = load(m); rec = {}
    for r in R:
        rec[(r["domain"] + ":" + r["task"], r["rep"], r["arm"])] = dict(
            reached=reached(r), rew=(r["reward"] or 0.0), tr=int(any(c["name"] == "transfer_to_human_agents" for c in r["calls"])))
    out = {}
    for arm in ("single", "blame"):
        rows = []
        for (tid, rep, a), v in rec.items():
            if a != arm: continue
            c = rec.get((tid, rep, "control"))
            if v["reached"] and c and c["reached"]:
                rows.append(dict(tid=tid, rew=v["rew"], tr=v["tr"], c_rew=c["rew"], c_tr=c["tr"]))
        D = pd.DataFrame(rows)
        def parts(s):
            # success difference = -(extra failures with transfer) - (extra failures without transfer)
            f_tr = ((1 - s.rew) * s.tr).mean() - ((1 - s.c_rew) * s.c_tr).mean()
            f_no = ((1 - s.rew) * (1 - s.tr)).mean() - ((1 - s.c_rew) * (1 - s.c_tr)).mean()
            return f_tr, f_no
        g = {k: v for k, v in D.groupby("tid")}; keys = list(g); rng = np.random.default_rng(0); bs = []
        for _ in range(B):
            s = pd.concat([g[k] for k in rng.choice(keys, len(keys))]); bs.append(parts(s))
        bs = np.array(bs); f_tr, f_no = parts(D)
        out[arm] = dict(n=int(len(D)), p_transfer=float(D.tr.mean()), p_transfer_control=float(D.c_tr.mean()),
                        success=float(D.rew.mean()), success_control=float(D.c_rew.mean()),
                        success_given_transfer=float(D[D.tr == 1].rew.mean()) if (D.tr == 1).any() else None,
                        extra_fail_with_transfer=float(f_tr), ci_tr=np.percentile(bs[:, 0], [2.5, 97.5]).tolist(),
                        extra_fail_without_transfer=float(f_no), ci_no=np.percentile(bs[:, 1], [2.5, 97.5]).tolist())
    res[m] = out
    print(f"\n=== {m} ===")
    for arm, o in out.items():
        sg = o["success_given_transfer"]
        print(f" {arm:6s} n={o['n']:3d}  P(transfer) {o['p_transfer']:.3f} (control {o['p_transfer_control']:.3f})  success {o['success']:.3f} vs {o['success_control']:.3f}"
              f"  success|transfer {('%.3f' % sg) if sg is not None else 'NA'}")
        print(f"        extra failures: with transfer {o['extra_fail_with_transfer']:+.3f} {np.round(o['ci_tr'],3).tolist()}   without transfer {o['extra_fail_without_transfer']:+.3f} {np.round(o['ci_no'],3).tolist()}")
OUT.write_text(json.dumps(res, indent=1))
