"""Dedicated servers (M=1, b=0), Poisson arrivals, exponential work: simulated P(wait > t) vs Erlang C."""
import numpy as np, math
from capacity_sim import simulate
def erlang_c(c, a):
    x = sum(a**k / math.factorial(k) for k in range(c)); y = a**c / math.factorial(c) * c / (c - a)
    return y / (x + y)
rng = np.random.default_rng(5)
for c, a in [(10, 7.0), (45, 38.0)]:
    n = 300000; arr = np.cumsum(rng.exponential(1 / a, n)); work = rng.exponential(1, n)
    # one pooled M/M/c queue == c servers with a single FCFS queue: JSQ with M=1 approximates; use c engines of M=1 + 'jsq'
    w, s = simulate(arr, work, 1, c, 0.0, 'random', seed=1)   # pooled queue: one engine with M = c
    print(c, a, 'sim P(wait>1)=%.4f' % np.mean(w > 1), ' M/M/c exact=%.4f' % (erlang_c(c, a) * math.exp(-(c - a) * 1)),
          '')
