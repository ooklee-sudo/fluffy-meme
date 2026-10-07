"""Study 2 / 3: seeding strategies (concentrated vs distributed) at equal exposure budget.

usage: python study2.py [--oracle surrogate|coarse|llm:<table.json>] [--reps N] [--out file]
"""
import argparse, json, random
from multiprocessing import Pool
import numpy as np
from scipy import stats
from sim import Sim, TableOracle, SurrogateFine, coarse_surrogate_table, state_key
from analysis import hawkes_branching

N, M, T_CAMP, H_AFTER = 2000, 3, 18.0, 48.0
TOPIC = 0
N_EXCLUDE = 3  # only the seeded influencers are excluded from the "ordinary users" pool


def make_oracle(spec):
    if spec == "surrogate":
        return None
    if spec == "coarse":
        return TableOracle(coarse_surrogate_table())
    if spec.startswith("llm:"):
        raw = json.load(open(spec[4:]))
        tab = {tuple(json.loads(k)): v for k, v in raw["ratings"].items()}
        return TableOracle(tab)
    raise ValueError(spec)


def pick_seeds(cond, s, rng):
    fol = s.followers
    order = sorted(range(s.n), key=lambda i: -len(fol[i]))
    top3 = order[:3]
    reach = sum(len(fol[i]) for i in top3)
    pool = order[N_EXCLUDE:]
    if cond == "concentrated":
        return top3, reach
    if cond == "random3":
        return rng.sample(pool, 3), reach
    if cond == "distributed":
        pool = pool[:]
        rng.shuffle(pool)
        seeds, r = [], 0
        for i in pool:
            seeds.append(i)
            r += len(fol[i])
            if r >= reach:
                break
        return seeds, r
    return [], 0


def run_one(args):
    cond, seed, spec = args
    s = Sim(N, M, seed, oracle=make_oracle(spec))
    seeds, reach = pick_seeds(cond, s, random.Random(seed * 31 + 5))
    inj = (T_CAMP, seeds, TOPIC) if seeds else None
    s.run(T_CAMP + H_AFTER, inject=inj)
    at = np.sort(np.array(s.adopt_times) - T_CAMP) if s.adopt_times else np.array([])
    n = len(at)
    rec = dict(cond=cond, seed=seed, n_seeds=len(seeds), reach=reach, adopters=n,
               exposed=len(s.exposed),
               t10=float(at[max(0, int(np.ceil(0.1 * n)) - 1)]) if n else float("nan"),
               t50=float(at[max(0, int(np.ceil(0.5 * n)) - 1)]) if n else float("nan"))
    if n >= 20:
        br, be = hawkes_branching(s.camp_events, T_CAMP, H_AFTER)
    else:
        br, be = float("nan"), float("nan")
    rec.update(branching=br, kernel_beta=be)
    return rec


def boot_ci(d, B=10000, rng=np.random.default_rng(0)):
    d = np.asarray(d)
    m = rng.choice(d, (B, len(d))).mean(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def summarize(recs):
    by = {}
    for r in recs:
        by.setdefault(r["cond"], {})[r["seed"]] = r
    out = {}
    seeds = sorted(set(by["concentrated"]) & set(by["distributed"]))
    for k in ("adopters", "exposed", "t50", "t10", "branching"):
        c = np.array([by["concentrated"][s][k] for s in seeds], float)
        d = np.array([by["distributed"][s][k] for s in seeds], float)
        ok = ~(np.isnan(c) | np.isnan(d))
        c, d = c[ok], d[ok]
        diff = c - d
        try:
            p = float(stats.wilcoxon(c, d).pvalue)
        except ValueError:
            p = float("nan")
        lo, hi = boot_ci(diff)
        out[k] = dict(conc=float(c.mean()), dist=float(d.mean()), diff=float(diff.mean()),
                      ci=[lo, hi], p=p, conc_sd=float(c.std(ddof=1)), dist_sd=float(d.std(ddof=1)),
                      conc_min=float(c.min()), conc_max=float(c.max()),
                      dist_min=float(d.min()), dist_max=float(d.max()),
                      conc_larger=float((diff > 0).mean()),
                      dz=float(diff.mean() / diff.std(ddof=1)), n=int(ok.sum()))
    for cond in ("random3", "noseed"):
        if cond in by:
            out[cond] = dict(adopters=float(np.mean([r["adopters"] for r in by[cond].values()])),
                             exposed=float(np.mean([r["exposed"] for r in by[cond].values()])))
    out["reach"] = dict(conc=float(np.mean([by["concentrated"][s]["reach"] for s in seeds])),
                        dist=float(np.mean([by["distributed"][s]["reach"] for s in seeds])),
                        dist_n_seeds=float(np.mean([by["distributed"][s]["n_seeds"] for s in seeds])))
    out["beta_mean"] = float(np.nanmean([r["kernel_beta"] for r in recs if r["cond"] in ("concentrated", "distributed")]))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--oracle", default="surrogate")
    ap.add_argument("--reps", type=int, default=40)
    ap.add_argument("--conds", default="concentrated,distributed,random3,noseed")
    ap.add_argument("--out", default="results_study2.json")
    a = ap.parse_args()
    jobs = [(c, sd, a.oracle) for sd in range(1, a.reps + 1) for c in a.conds.split(",")]
    with Pool(4) as p:
        recs = p.map(run_one, jobs, chunksize=1)
    summ = summarize(recs)
    json.dump(dict(oracle=a.oracle, summary=summ, runs=recs), open(a.out, "w"), indent=1)
    for k, v in summ.items():
        print(k, v if not isinstance(v, dict) else {x: (round(y, 3) if isinstance(y, float) else y) for x, y in v.items()})
