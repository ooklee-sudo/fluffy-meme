"""Proposition 9 (Section 4.7): numerical example. Engine with share sigma switches to full answers at the first tau with
sigma [pi_A - (R0 + rho sigma - c_O) g(tau)] >= K, g(tau) = 0.3 + 0.9 exp(-0.05 tau).
pi_A = 1, R0 = 0.6, rho = 1.2, c_O = 0.05, K = 0.04. Reported in the paper: first switcher sigma = 0.18;
sigma = 0.10, 0.30, 0.60, 0.90 switch after 8.3, 6.4, 14.6, 22.9 periods; sigma = 0.02 never switches (nan).
The empirical part of the same session block is 02_analysis/t12_prop9_regressions.py. No data needed."""
import numpy as np
# Model check: switch when sigma*[piA - (R0+rho*sigma - cO)*g(tau)] >= K ; g decreasing in tau
piA,R0,rho,cO,K=1.0,0.6,1.2,0.05,0.04
taus=np.linspace(0,30,3001); g=lambda tau: 0.9*np.exp(-0.05*tau)+0.3
sig=np.linspace(0.01,0.95,95); T=[]
for s in sig:
    ok=[tau for tau in taus if s*(piA-(R0+rho*s-cO)*g(tau))>=K]
    T.append(ok[0] if ok else np.nan)
T=np.array(T); i=np.nanargmin(T)
print("earliest adopter sigma=",round(sig[i],2),"T=",round(T[i],2)); print("T at sigma .02,.1,.3,.6,.9:",[round(T[np.argmin(abs(sig-v))],1) for v in [.02,.1,.3,.6,.9]])
for KK in [0.02,0.04]:
    print("K",KK,"T(.1)",[t for t in taus if .1*(piA-(R0+rho*.1-cO)*g(t))>=KK][0])
