import sys, numpy as np, pickle
from poisson_sns import simulate
B0 = -2.87
res = {}
for sch in ('ipp', 'hpp', 'poll'):
    res[sch] = []
    for seed in range(5):
        r = simulate(sch, hours=72, seed=seed, b0=B0, max_events=400000)
        print(sch, seed, r['events'], len(r['posts']), len(r['comments']), flush=True)
        res[sch].append(r)
pickle.dump(res, open('sim_study1.pkl', 'wb'))
