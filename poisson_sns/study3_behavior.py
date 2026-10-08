"""Study 3 behavioural check: IPP scheduler under coarse-surrogate vs LLM oracle (5 reps each)."""
import json, sys
from multiprocessing import Pool
import numpy as np
from sim import Sim
from study2 import make_oracle
from analysis import behaviour_metrics, hourly_counts_series

def one(a):
    spec, seed = a
    s = Sim(800, 5, seed, oracle=make_oracle(spec)).run(72)
    m = behaviour_metrics(s.events); m["vmr"] = float(hourly_counts_series(s.events, 72).var() / hourly_counts_series(s.events, 72).mean())
    return spec, m

if __name__ == "__main__":
    specs = ["surrogate", "coarse", "llm:llm_table.json"]
    with Pool(4) as p:
        res = p.map(one, [(sp, sd) for sp in specs for sd in range(1, 6)])
    out = {}
    for sp, m in res: out.setdefault(sp, []).append(m)
    summ = {sp: {k: float(np.mean([m[k] for m in ms])) for k in ms[0]} for sp, ms in out.items()}
    json.dump(summ, open("results_study3_behavior.json", "w"), indent=1)
    for sp, d in summ.items(): print(sp, {k: round(v, 3) for k, v in d.items()})
