"""One-at-a-time sensitivity of the seeding result to manual parameters and network.

python sensitivity.py [--reps 15]
"""
import argparse, json, random
from multiprocessing import Pool
import numpy as np
from scipy import stats
import sim as S
from study2 import pick_seeds, boot_ci, N, M, T_CAMP, H_AFTER, TOPIC
from analysis import hawkes_branching

BASE = dict(kappa=0.16, s_max=3.0, p_view=0.5, net="pa")
GRID = [("base", {})]
for k in (0.12, 0.20):
    GRID.append((f"kappa={k}", dict(kappa=k)))
for v in (2.0, 4.0):
    GRID.append((f"S_max={v}", dict(s_max=v)))
for v in (0.4, 0.6):
    GRID.append((f"p_view={v}", dict(p_view=v)))
for v in ("random", "community"):
    GRID.append((f"net={v}", dict(net=v)))
NETS = dict(pa=None, random=S.random_network, community=S.community_network)


def run(args):
    name, over, cond, seed = args
    c = {**BASE, **over}
    s = S.Sim(N, M, seed, kappa=c["kappa"], s_max=c["s_max"], p_view=c["p_view"],
              netfun=NETS[c["net"]], max_events=400000)
    seeds, reach = pick_seeds(cond, s, random.Random(seed * 31 + 5))
    s.run(T_CAMP + H_AFTER, inject=(T_CAMP, seeds, TOPIC))
    at = np.sort(np.array(s.adopt_times) - T_CAMP) if s.adopt_times else np.array([])
    n = len(at)
    return dict(name=name, cond=cond, seed=seed, adopters=n, truncated=s.truncated,
                total_events=len(s.events),
                t50=float(at[max(0, int(np.ceil(0.5 * n)) - 1)]) if n else float("nan"),
                reach=reach)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=15)
    a = ap.parse_args()
    jobs = [(nm, ov, cd, sd) for nm, ov in GRID for sd in range(1, a.reps + 1)
            for cd in ("concentrated", "distributed")]
    with Pool(4) as p:
        recs = p.map(run, jobs, chunksize=1)
    rows = []
    print(f"{'config':16s} {'conc':>7s} {'dist':>7s} {'diff [95% CI]':>24s} {'conc>dist':>9s} {'t50 diff':>9s} {'SD c/d':>11s} {'trunc':>5s}")
    for nm, _ in GRID:
        by = {c: {r["seed"]: r for r in recs if r["name"] == nm and r["cond"] == c}
              for c in ("concentrated", "distributed")}
        sd_ = sorted(by["concentrated"])
        c = np.array([by["concentrated"][x]["adopters"] for x in sd_], float)
        d = np.array([by["distributed"][x]["adopters"] for x in sd_], float)
        tc = np.array([by["concentrated"][x]["t50"] for x in sd_])
        td = np.array([by["distributed"][x]["t50"] for x in sd_])
        tr = sum(by[k][x]["truncated"] for k in by for x in sd_)
        diff = c - d
        lo, hi = boot_ci(diff)
        p = stats.wilcoxon(c, d).pvalue if (diff != 0).any() else 1.0
        row = dict(config=nm, conc=c.mean(), dist=d.mean(), diff=diff.mean(), lo=lo, hi=hi,
                   frac=(diff > 0).mean(), p=float(p), t50diff=float(np.nanmean(tc - td)),
                   sd_c=c.std(ddof=1), sd_d=d.std(ddof=1), truncated=int(tr),
                   events=float(np.mean([r["total_events"] for r in recs if r["name"] == nm])))
        rows.append(row)
        print(f"{nm:16s} {row['conc']:7.1f} {row['dist']:7.1f} {row['diff']:+8.1f} [{lo:+6.1f},{hi:+6.1f}] {row['frac']:9.2f} {row['t50diff']:+9.2f} {row['sd_c']:5.0f}/{row['sd_d']:<5.0f} {tr:5d}")
    json.dump(dict(rows=rows, runs=recs), open("results_sensitivity.json", "w"), indent=1)
