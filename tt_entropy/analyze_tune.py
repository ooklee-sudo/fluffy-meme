"""Pick one learning rate per method from a phase2.py --tune run (rule fixed in PREREGISTRATION_H2.md):
the lr with the highest mean dev relative gain over the tuning tenants. A choice at the edge of its grid is
flagged; the preregistered rule then extends the grid by one step for that method and tunes again.

Usage: python analyze_tune.py [results/phase2_tune] [results/phase2_tune2 ...]   (folders are merged)
Prints the --lrs argument for the main run and saves it to <dir>_choice.json.
"""
import glob
import json
import os
import sys
from collections import defaultdict


def main():
    dirs = sys.argv[1:] or ["results/phase2_tune"]
    d = dirs[0]
    rows = [json.load(open(p)) for x in dirs for p in sorted(glob.glob(os.path.join(x, "*.json")))]
    if not rows:
        raise SystemExit(f"no results in {', '.join(dirs)}")
    acc = defaultdict(list)
    for r in rows:
        for run in r["runs"]:
            acc[(run["method"], run["config"], run["lr"])].append(run["dev_rel_gain"])
    print(f"{len({r['tenant'] for r in rows})} tuning tenants\n\n{'config':<12}{'lr':>9}{'mean dev rel gain':>20}{'n':>4}")
    best, grids = {}, defaultdict(list)
    for (m, c, lr), v in sorted(acc.items()):
        mean = sum(v) / len(v)
        grids[m].append(lr)
        print(f"{c:<12}{lr:>9.0e}{mean:>20.4f}{len(v):>4}")
        if m not in best or mean > best[m][1]:
            best[m] = (lr, mean)
    print()
    edge = []
    for m, (lr, mean) in best.items():
        g = sorted(grids[m])
        at_edge = lr in (g[0], g[-1])
        if at_edge:
            edge.append(m)
        print(f"{m}: lr {lr:.0e} (mean dev rel gain {mean:.4f}){'  <- at the grid edge' if at_edge else ''}")
    arg = ",".join(f"{m}={best[m][0]:g}" for m in sorted(best))
    print(f"\n--lrs {arg}")
    if edge:
        print(f"\nEdge choices for {', '.join(edge)}: extend that grid by one step and rerun --tune for it "
              "(PREREGISTRATION_H2.md section 5) before the main run.")
    with open(d.rstrip("/") + "_choice.json", "w") as f:
        json.dump(dict(lrs={m: best[m][0] for m in best}, mean_dev_rel_gain={m: best[m][1] for m in best},
                       at_edge=edge, n_tenants=len({r["tenant"] for r in rows}), dirs=dirs, arg=arg), f, indent=1)


if __name__ == "__main__":
    main()
