"""Proposition 10 (Section 4.8): trust traps. Fixed points of Phi(tau) = T(G(tau)) with
G(tau) = 1 - F(e/(1-tau)) (stakes lognormal) and T(v) = 1 - (1-q)(rho + (1-rho) v); hysteresis after a temporary
rise in error detection rho (0.02 -> 0.5 -> 0.02). Paper example: median stake 0.35, sigma 0.2, e = 0.05, rho = 0.02,
q = 0.6 (three equilibria: tau = 0.60, 0.87, 0.99) and q = 0.9 (complacent only). No data needed."""
import numpy as np
from scipy.stats import lognorm
# users verify (click) when (1-tau)*L > e ; stakes L ~ lognormal
def G(tau,e,s=1.0,mu=0.0): # share who click
    thr=e/np.maximum(1-tau,1e-9); return 1-lognorm.cdf(thr,s,scale=np.exp(mu))
def T(v,q,rho): return 1-(1-q)*(rho+(1-rho)*v)
def fixed_points(q,rho,e,s,mu):
    taus=np.linspace(0,0.9999,200001); phi=T(G(taus,e,s,mu),q,rho); d=phi-taus
    idx=np.where(np.sign(d[:-1])!=np.sign(d[1:]))[0]; return [(round(taus[i],4),round(G(taus[i],e,s,mu),4)) for i in idx]
for q,rho,e,s,mu in [(0.7,0.05,0.05,0.6,np.log(0.5)),(0.7,0.05,0.05,0.25,np.log(0.4)),(0.9,0.05,0.05,0.25,np.log(0.4)),(0.6,0.02,0.05,0.2,np.log(0.35))]:
    fp=fixed_points(q,rho,e,s,mu); print(f"q={q} rho={rho} e={e} s={s}: equilibria (tau,click share):",fp, " overtrust:",[round(t-q,3) for t,_ in fp])
# hysteresis: start at complacent eq of last case, raise rho temporarily
q,rho,e,s,mu=0.6,0.02,0.05,0.2,np.log(0.35)
tau=0.99
for t in range(400): tau=T(G(tau,e,s,mu),q,rho)
print("start complacent tau",round(tau,4),"click",round(G(tau,e,s,mu),4))
for t in range(400): tau=T(G(tau,e,s,mu),q,0.5)   # salient error period
print("during shock tau",round(tau,4))
for t in range(400): tau=T(G(tau,e,s,mu),q,rho)
print("after shock tau",round(tau,4),"click",round(G(tau,e,s,mu),4))
