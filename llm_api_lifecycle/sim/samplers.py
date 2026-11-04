import numpy as np, pandas as pd, sys
sys.path.insert(0,'.')
from km import km, lifetimes, load
def km_sample_pool(L, n=20000, seed=11, tail=240.0):
    """Draw n lifetimes from the KM curve; mass beyond the last event goes to `tail` months."""
    ts, ss = km(L.months.values, L.event.values)
    rng = np.random.default_rng(seed); u = rng.random(n)
    out = np.full(n, tail)
    for i in range(1, len(ts)):
        out[(u > ss[i]) & (u <= ss[i-1]) & (out == tail)] = ts[i]
    return out

from scipy.optimize import minimize
def weibull_fit(L):
    t=np.maximum(L.months.values,0.25); e=L.event.values
    def nll(p):
        k,lam=np.exp(p); z=(t/lam)**k
        return -(np.sum(e*(np.log(k/lam)+(k-1)*np.log(t/lam))) - np.sum(z))
    r=minimize(nll,[np.log(1.5),np.log(np.median(t)*1.5)],method='Nelder-Mead')
    k,lam=np.exp(r.x); return k,lam
def weibull_pool(L,n=20000,seed=11):
    k,lam=weibull_fit(L); rng=np.random.default_rng(seed)
    return lam*rng.weibull(k,n),(k,lam)
