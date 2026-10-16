import numpy as np, time
from capacity_sim import simulate
from quasi_static import Engine
rng=np.random.default_rng(3); b=0.1; M=16
for c,load,rt in [(1,0.5,'random'),(1,0.85,'random'),(4,0.7,'random'),(4,0.7,'jsq')]:
    e=Engine(M,b); lam_tot=load*e.mubar*c; n=400000
    arr=np.cumsum(rng.exponential(1/lam_tot,n)); work=rng.exponential(1,n)
    t0=time.time(); w,s=simulate(arr,work,c,M,b,rt,seed=1)
    ex=e.d(load*e.mubar) if rt=='random' else float('nan')
    print(c,load,rt,'sim sojourn',round(s.mean(),4),'exact',round(ex,4),'wait',round(w.mean(),4),f'{time.time()-t0:.1f}s')
