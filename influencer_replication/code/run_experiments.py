"""Runs all simulation experiments of Section 5 and stores per-run adoption times in results/runs/*.json.gz.

Usage: python run_experiments.py [--out ../results] [--procs 4] [--only base,schedulers,injection,pricing,beta] [--quick]
Replications are paired: replication r of both plans uses the same network, personas, and random seed r.
"""
import argparse, gzip, json, os
from multiprocessing import Pool

import numpy as np

from simulator import Config, build_world, run, seed_plan

N_BASE, N_SCHED, N_OTHER, N_BETA = 30, 30, 20, 15
BETAS = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.50]


def job(spec):
    tag, cfg_kw, plan, rep, plan_kw = spec
    cfg = Config(**cfg_kw)
    W = build_world(cfg, rep)
    seeds = seed_plan(W, plan, np.random.default_rng(10_000 + rep), **plan_kw)
    r = run(cfg, seeds, rep)
    return dict(tag=tag, plan=plan, rep=rep, n_seeds=len(seeds), seed_followers=[int(W["nfol"][s]) for s in seeds[:3]],
                adopt=[round(x, 4) for x in r["adopt_times"]], n_events=r["n_events"])


def _pilot_events(spec):
    tag, kw, plan, rep, pk = spec
    return run(Config(**kw), [], rep)["n_events"]


def calibrate_multiplier(procs, n=6):
    """Volume matching (Section 4.5): ratio of total events under the event-driven and circadian-only schedulers in
    pilot runs without a campaign."""
    specs_e = [("pilot", dict(scheduler="event"), "none", r, {}) for r in range(100, 100 + n)]
    specs_c = [("pilot", dict(scheduler="circadian", rate_multiplier=1.0), "none", r, {}) for r in range(100, 100 + n)]

    with Pool(procs) as P:
        ev = P.map(_pilot_events, specs_e); ci = P.map(_pilot_events, specs_c)
    return float(np.sum(ev) / np.sum(ci))


def save(path, rows):
    with gzip.open(path, "wt") as fh:
        json.dump(rows, fh)


def run_set(name, specs, out, procs):
    path = os.path.join(out, "runs", f"{name}.json.gz")
    if os.path.exists(path):
        print("skip (exists):", path); return
    with Pool(procs) as P:
        rows = P.map(job, specs, chunksize=1)
    save(path, rows)
    print("saved", path, len(rows), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="../results"); ap.add_argument("--procs", type=int, default=os.cpu_count())
    ap.add_argument("--only", default="base,schedulers,injection,pricing,beta,beta_obs,beta_fine"); ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    os.makedirs(os.path.join(a.out, "runs"), exist_ok=True)
    only = a.only.split(",")
    q = (lambda n: 3) if a.quick else (lambda n: n)
    plans = ["concentrated", "distributed"]

    if "base" in only:
        run_set("base", [("base", {}, p, r, {}) for r in range(q(N_BASE)) for p in plans], a.out, a.procs)
    if "schedulers" in only:
        mpath = os.path.join(a.out, "volume_multiplier.json")
        if os.path.exists(mpath):
            mult = json.load(open(mpath))["multiplier"]
        else:
            mult = calibrate_multiplier(a.procs)
            json.dump({"multiplier": mult}, open(mpath, "w"))
        print("volume-matching multiplier:", mult)
        specs = [(f"sched_{s}", dict(scheduler=s, rate_multiplier=mult), p, r, {})
                 for s in ("circadian", "hpp", "polling") for r in range(q(N_SCHED)) for p in plans]
        run_set("schedulers", specs, a.out, a.procs)
    if "injection" in only:
        mult = json.load(open(os.path.join(a.out, "volume_multiplier.json")))["multiplier"] if os.path.exists(os.path.join(a.out, "volume_multiplier.json")) else 1.77
        specs = []
        for hour in (3.0, 9.0):
            for s in ("event", "circadian"):
                kw = dict(scheduler=s, injection_hour=hour, rate_multiplier=mult)
                specs += [(f"inj{int(hour):02d}_{s}", kw, p, r, {}) for r in range(q(N_OTHER)) for p in plans]
        run_set("injection", specs, a.out, a.procs)
    if "pricing" in only:
        specs = []
        for pname, pk in (("equal", dict(cost_c0=0.0, cost_gamma=1.0)), ("concave", dict(cost_c0=0.0, cost_gamma=0.7)),
                          ("fixed", dict(cost_c0=10.0, cost_gamma=1.0))):
            for k in range(0, 4):
                if k == 3 and pname != "equal":
                    continue  # three influencers cost the whole budget under every pricing rule: identical plan
                plan = "hybrid"
                specs += [(f"price_{pname}_k{k}", {}, plan, r, dict(pk, k_hybrid=k)) for r in range(q(N_OTHER))]
        run_set("pricing", specs, a.out, a.procs)
    if "beta_obs" in only:
        # elasticity at the SAGraph point estimate (0.66), beyond the sweep range
        specs = [(f"beta_{b:.2f}", dict(beta=b), p, r, {}) for b in (0.66,) for r in range(q(N_BETA)) for p in plans]
        run_set("beta_obs", specs, a.out, a.procs)
    if "beta_fine" in only:
        # finer grid between 0.30 and 0.66 to localize the reversal of final reach; 30 replications per cell
        specs = [(f"beta_{b:.2f}", dict(beta=b), p, r, {}) for b in (0.35, 0.40, 0.45, 0.60) for r in range(q(30)) for p in plans]
        run_set("beta_fine", specs, a.out, a.procs)
    if "beta" in only:
        specs = [(f"beta_{b:.2f}", dict(beta=b), p, r, {}) for b in BETAS for r in range(q(N_BETA)) for p in plans]
        run_set("beta", specs, a.out, a.procs)


if __name__ == "__main__":
    main()
