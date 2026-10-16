import numpy as np
from quasi_static import *

def brute(M,b,lam,N=20000):
    e=Engine(M,b); mu=np.array([min(n,M)*(1+b)/(1+b*min(max(n,1),M)) for n in range(N+1)])
    lw=np.concatenate([[0],np.cumsum(np.log(lam)-np.log(mu[1:]))]); p=np.exp(lw-lw.max()); p/=p.sum()
    n=np.arange(N+1); EN=(p*n).sum(); var=(p*n*n).sum()-EN**2
    return EN/lam,(var-EN)/lam

for M,b,lam in [(8,0.2,3.0),(64,0.1,9.0),(16,0.0,15.0),(100,0.06,14.0)]:
    e=Engine(M,b); s=e.stats(lam); d,t=brute(M,b,lam)
    print(M,b,lam,'d',s['d'],d,'t',s['t'],t, 'chk',s['d_check'],s['t_check'])
    assert abs(s['d']-d)<1e-6*d and abs(s['t']-t)<1e-5*max(t,1e-9)+1e-9 and abs(s['d_check']-s['d'])<1e-8
# B.1: unbounded batch closed form d=1/(1-b' lam), b'=beta/(alpha+beta), here M huge
e=Engine(3000,0.2); bp=0.2/1.2
print(e.d(2.0),1/(1-bp*2.0), e.t(5.5), bp*5.5/(1-bp*5.5)**2)
# tolls rise with load (Prop 1)
e=Engine(64,0.1); ls=np.linspace(0.1,e.mubar*0.99,60); ts=[e.t(l) for l in ls]; assert np.all(np.diff(ts)>0)
# t' check
print(e.tprime(5.0),(e.t(5.001)-e.t(4.999))/0.002)
# Prop 2: dedicated -> tS=0
print(Engine(10,0).stats(8.0)['tS'])
print('ok')
