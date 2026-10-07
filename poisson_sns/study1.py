"""Study 1: scheduler comparison (IPP vs HPP vs polling)."""
import json, sys
from multiprocessing import Pool
import numpy as np
from sim import Sim
from analysis import behaviour_metrics, hourly_counts_series

N, M, H, REPS = 800, 5, 72, 5


def one(args):
    sch, seed = args
    s = Sim(N, M, seed, scheduler=sch).run(H)
    m = behaviour_metrics(s.events)
    hc = hourly_counts_series(s.events, H)
    m["vmr"] = float(hc.var() / hc.mean())
    return sch, m


if __name__ == "__main__":
    jobs = [(sch, seed) for sch in ("ipp", "hpp", "poll") for seed in range(1, REPS + 1)]
    with Pool(4) as p:
        res = p.map(one, jobs)
    out = {}
    for sch, m in res:
        out.setdefault(sch, []).append(m)
    summ = {sch: {k: float(np.mean([m[k] for m in ms])) for k in ms[0]} for sch, ms in out.items()}
    json.dump(dict(summary=summ, runs=out), open("results_study1.json", "w"), indent=1)
    keys = ["r", "tv", "chi2", "ks", "med_delay", "frac_5min", "tail24", "vmr", "n"]
    print("scheduler", *keys)
    for sch, d in summ.items():
        print(sch, *[round(d[k], 3) for k in keys])
