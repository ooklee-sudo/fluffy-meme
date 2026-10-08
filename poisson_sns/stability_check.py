"""Check the Section 3.5 claim: does an uncapped additive stimulus make the process explode?"""
import json, time
from multiprocessing import Pool
import numpy as np
from sim import Sim

CFG = [("capped kappa=0.16, S_max=3", 0.16, 3.0), ("uncapped kappa=0.16", 0.16, 1e9),
       ("uncapped kappa=0.20", 0.20, 1e9), ("uncapped kappa=0.25", 0.25, 1e9),
       ("capped kappa=0.25, S_max=3", 0.25, 3.0)]

def run(a):
    name, k, cap, seed = a
    t0 = time.time()
    s = Sim(800, 5, seed, kappa=k, s_max=cap, max_events=40000).run(24)
    # evening (18-24h) events per hour vs events in same window under HPP baseline
    ev = [e for e in s.events if e[2] < 3]
    return dict(name=name, seed=seed, events=len(s.events), truncated=s.truncated,
                last_t=s.t, secs=time.time() - t0)

if __name__ == "__main__":
    with Pool(4) as p:
        res = p.map(run, [(n, k, c, sd) for n, k, c in CFG for sd in (1, 2, 3)])
    out = []
    for n, _, _ in CFG:
        r = [x for x in res if x["name"] == n]
        row = dict(config=n, events=float(np.mean([x["events"] for x in r])), truncated=sum(x["truncated"] for x in r),
                   reached_hour=float(np.mean([x["last_t"] for x in r])), secs=float(np.mean([x["secs"] for x in r])))
        out.append(row); print(row)
    json.dump(out, open("results_stability.json", "w"), indent=1)
