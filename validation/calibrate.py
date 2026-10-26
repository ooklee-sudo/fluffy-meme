import sys, numpy as np
from poisson_sns import simulate
# find intercept b0 so that a 24 h / 800 agent IPP run yields ~14,830 events (Section III-E)
lo, hi = -6.0, 2.0
for _ in range(9):
    b0 = (lo + hi) / 2
    ev = np.mean([simulate('ipp', hours=24, seed=s, b0=b0, max_events=60000)['events'] for s in range(3)])
    print(round(b0, 3), round(ev), flush=True)
    if ev > 14830: hi = b0
    else: lo = b0
print('b0 =', round((lo + hi) / 2, 3))
