import json, sys, math
import numpy as np, pandas as pd
from pathlib import Path
RES = Path(sys.argv[1])
MAXR = {"deepseek": 2}
def load(m):
    rows = [json.loads(l) for l in open(RES / f"{m}.jsonl")]
    rows = [r for r in rows if r.get("ok") and r["rep"] < MAXR.get(m, 99)]
    seen = {}
    for r in rows: seen[r["key"]] = r
    return list(seen.values())
for m in ["llama8b","llama70b","deepseek","gpt61terra","sonnet55"]:
    R = load(m)
    df = pd.DataFrame([dict(tid=r["domain"]+":"+r["task"], dom=r["domain"], arm=r["arm"], rep=r["rep"], rew=(r["reward"] or 0.0),
        j=r["j"], ninj=r["n_inj"], ncalls=len(r["calls"]), cost=(r.get("agent_cost") or 0)+(r.get("user_cost") or 0),
        agent_cost=r.get("agent_cost") or 0, crashed=r.get("crashed",0)) for r in R])
    df["reached"] = np.where(df.arm=="control", df.ncalls>=df.j, df.ninj>0)
    print(f"\n=== {m}: runs={len(df)}, tasks={df.tid.nunique()}, mean cost/run ${df.cost.mean():.4f} (agent ${df.agent_cost.mean():.4f}), mean calls {df.ncalls.mean():.1f}")
    for arm in ["control","single","blame"]:
        d = df[df.arm==arm]
        print(f"  {arm:8s} success {d.rew.mean():.3f}  reached injection-point share {d.reached.mean():.3f}  crash {d.crashed.mean():.3f}")
    # ITT vs reached-only effect for blame: pair by (tid,rep) and require control also reached (same j)
    piv = df.pivot_table(index=["tid","rep"], columns="arm", values="rew")
    rch = df.pivot_table(index=["tid","rep"], columns="arm", values="reached", aggfunc="first")
    for arm in ["single","blame"]:
        p = piv[[arm,"control"]].dropna(); itt = (p[arm]-p["control"]).mean()
        ok = rch.loc[p.index, arm].astype(bool) & rch.loc[p.index, "control"].astype(bool)
        sub = p[ok.values]
        eff = (sub[arm]-sub["control"]).mean() if len(sub) else float("nan")
        print(f"  {arm}-control: ITT {itt:+.3f} (n={len(p)})  | injection actually reached: {eff:+.3f} (n={len(sub)}, {len(sub)/len(p):.0%} of pairs)")
    # task-level SD of paired blame-control difference (mean over reps) for power
    t = piv.reset_index().groupby("tid")[["blame","control"]].mean().dropna()
    sd = (t["blame"]-t["control"]).std()
    print(f"  task-level SD of (blame-control): {sd:.3f} over {len(t)} tasks")
